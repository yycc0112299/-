"""OpenCV-DNN YOLOv8 person adapter for a static 640x640 ONNX export.

This is the CPU fallback and integration contract for the later VART/DPU
backend.  It deliberately emits only COCO class 0 (person), matching the
tracker and two-board packet schema rather than changing their public data.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


class YoloV8:
    """Run a static 640-square YOLOv8 detection ONNX model with OpenCV DNN."""

    input_size = 640
    person_class = 0

    def __init__(self, model_path: str | Path, confidence_threshold: float = .30,
                 nms_threshold: float = .45, backend: str = "auto") -> None:
        if backend not in {"auto", "onnxruntime", "opencv"}:
            raise ValueError("backend must be auto, onnxruntime, or opencv")
        self.model_path = str(model_path)
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.backend = ""
        self.session = None
        self.input_name = ""
        if backend in {"auto", "onnxruntime"}:
            try:
                import onnxruntime as ort
                self.session = ort.InferenceSession(self.model_path,
                                                    providers=["CPUExecutionProvider"])
                self.input_name = self.session.get_inputs()[0].name
                self.backend = "onnxruntime"
            except Exception:
                if backend == "onnxruntime":
                    raise
        if not self.backend:
            self.net = cv2.dnn.readNet(self.model_path)
            self.backend = "opencv"

    @staticmethod
    def _prediction_rows(predictions: np.ndarray) -> np.ndarray:
        values = np.asarray(predictions, dtype=np.float32)
        if values.ndim == 3 and values.shape[0] == 1:
            values = values[0]
        if values.ndim != 2:
            raise ValueError(f"unexpected YOLOv8 output shape {predictions.shape}")
        # Ultralytics ONNX commonly emits (84, 8400); some exporters emit
        # (8400, 84).  Both are raw xywh + 80 COCO class scores.
        if values.shape[0] == 84:
            values = values.T
        if values.shape[1] < 5:
            raise ValueError(f"unexpected YOLOv8 prediction width {values.shape[1]}")
        return values

    @classmethod
    def decode_predictions(cls, predictions: np.ndarray, *, source_width: int,
                           source_height: int, confidence_threshold: float,
                           nms_threshold: float) -> list[dict[str, object]]:
        """De-letterbox raw model output and return only person detections."""
        if source_width <= 0 or source_height <= 0:
            raise ValueError("source dimensions must be positive")
        scale = min(cls.input_size / source_width, cls.input_size / source_height)
        resized_width = round(source_width * scale)
        resized_height = round(source_height * scale)
        pad_x = (cls.input_size - resized_width) / 2
        pad_y = (cls.input_size - resized_height) / 2
        candidates: list[dict[str, object]] = []
        boxes_xywh: list[list[int]] = []
        scores: list[float] = []
        for row in cls._prediction_rows(predictions):
            class_scores = row[4:]
            if len(class_scores) <= cls.person_class:
                raise ValueError("YOLOv8 output has no person class score")
            confidence = float(class_scores[cls.person_class])
            if confidence < confidence_threshold:
                continue
            center_x, center_y, width, height = (float(value) for value in row[:4])
            x0 = max(0, min(source_width, int(np.floor((center_x - width / 2 - pad_x) / scale))))
            y0 = max(0, min(source_height, int(np.floor((center_y - height / 2 - pad_y) / scale))))
            x1 = max(0, min(source_width, int(np.ceil((center_x + width / 2 - pad_x) / scale))))
            y1 = max(0, min(source_height, int(np.ceil((center_y + height / 2 - pad_y) / scale))))
            if x1 <= x0 or y1 <= y0:
                continue
            candidates.append({"class_id": cls.person_class, "confidence": confidence,
                               "box": [x0, y0, x1, y1]})
            boxes_xywh.append([x0, y0, x1 - x0, y1 - y0])
            scores.append(confidence)
        if not boxes_xywh:
            return []
        kept = cv2.dnn.NMSBoxes(boxes_xywh, scores, confidence_threshold, nms_threshold)
        indices = np.asarray(kept).reshape(-1).tolist() if len(kept) else []
        return [candidates[int(index)] for index in indices]

    def infer(self, source: np.ndarray) -> list[dict[str, object]]:
        """Run inference on a BGR frame and return clipped person boxes."""
        if source.ndim != 3 or source.shape[2] != 3:
            raise ValueError(f"expected BGR HxWx3 frame, received {source.shape}")
        height, width = source.shape[:2]
        scale = min(self.input_size / width, self.input_size / height)
        resized = cv2.resize(source, (round(width * scale), round(height * scale)),
                             interpolation=cv2.INTER_LINEAR)
        canvas = np.full((self.input_size, self.input_size, 3), 114, dtype=np.uint8)
        offset_x = (self.input_size - resized.shape[1]) // 2
        offset_y = (self.input_size - resized.shape[0]) // 2
        canvas[offset_y:offset_y + resized.shape[0], offset_x:offset_x + resized.shape[1]] = resized
        blob = cv2.dnn.blobFromImage(canvas, 1 / 255.0,
                                     (self.input_size, self.input_size),
                                     swapRB=True, crop=False)
        if self.backend == "onnxruntime":
            assert self.session is not None
            predictions = self.session.run(None, {self.input_name: blob})[0]
        else:
            self.net.setInput(blob)
            predictions = self.net.forward()
        return self.decode_predictions(predictions, source_width=width,
                                       source_height=height,
                                       confidence_threshold=self.confidence_threshold,
                                       nms_threshold=self.nms_threshold)
