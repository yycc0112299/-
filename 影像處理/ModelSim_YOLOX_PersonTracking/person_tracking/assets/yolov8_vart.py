"""VART execution boundary for a compiled PYNQ-ZU YOLOv8 DPU model.

This module intentionally owns only the parts that are invariant across VART
models: finding the DPU runner, RGB letterboxing, INT8 quantization, job
execution and output dequantization.  A Vitis-AI compiled YOLOv8 graph can
emit one or several output heads whose layout is model-specific, so person
detection is deliberately unavailable until that compiled model has a tested
decoder.  This prevents an ONNX-output assumption from being misrepresented
as a working DPU detector.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from yolov8 import YoloV8


Decoder = Callable[[Mapping[str, np.ndarray], int, int], list[dict[str, object]]]


def standard_yolov8_decoder(*, output_name: str | None = None,
                            confidence_threshold: float = .30,
                            nms_threshold: float = .45) -> Decoder:
    """Create a decoder for a *verified* raw single-head YOLOv8 output.

    The compiled model must expose one tensor compatible with the raw Ultralytics
    ONNX layout, either ``(1, 84, candidates)`` or ``(1, candidates, 84)``.
    DPU compilation can instead expose several feature heads, so callers must
    inspect the actual `.xmodel` before registering this decoder.
    """
    if not 0.0 <= confidence_threshold <= 1.0:
        raise ValueError("confidence_threshold must be between 0 and 1")
    if not 0.0 <= nms_threshold <= 1.0:
        raise ValueError("nms_threshold must be between 0 and 1")

    def decode(outputs: Mapping[str, np.ndarray], source_width: int,
               source_height: int) -> list[dict[str, object]]:
        if output_name is None:
            if len(outputs) != 1:
                raise RuntimeError(
                    "standard YOLOv8 decoder requires exactly one standard YOLOv8 output; "
                    "inspect the compiled model and select a model-specific decoder"
                )
            predictions = next(iter(outputs.values()))
        else:
            try:
                predictions = outputs[output_name]
            except KeyError as error:
                raise RuntimeError(
                    f"expected verified YOLOv8 output {output_name!r}, got {sorted(outputs)}"
                ) from error
        return YoloV8.decode_predictions(
            predictions,
            source_width=source_width,
            source_height=source_height,
            confidence_threshold=confidence_threshold,
            nms_threshold=nms_threshold,
        )

    return decode


def _tensor_fix_point(tensor: Any) -> int:
    try:
        return int(tensor.get_attr("fix_point"))
    except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
        return 0


def _tensor_name(tensor: Any, index: int) -> str:
    name = getattr(tensor, "name", None)
    if not name:
        try:
            name = tensor.get_name()
        except AttributeError:
            name = None
    return str(name or f"output_{index}")


class VartYoloV8:
    """Run one compiled B512 DPU graph and expose its real output tensors.

    ``infer_tensors`` is usable once VART/XIR and an exact `.xmodel` exist.
    ``infer`` additionally needs a decoder bound to the compiled graph's real
    output tensors; it otherwise raises rather than returning guessed boxes.
    """

    def __init__(self, runner: Any, input_tensor: Any, output_tensors: list[Any], *,
                 confidence_threshold: float = .30, nms_threshold: float = .45,
                 decoder: Decoder | None = None) -> None:
        dimensions = tuple(int(value) for value in input_tensor.dims)
        if len(dimensions) != 4 or dimensions[0] != 1 or dimensions[-1] != 3:
            raise ValueError("VART YOLOv8 input must be batch-one NHWC RGB")
        if not output_tensors:
            raise ValueError("VART graph has no output tensors")
        self.runner = runner
        self.input_tensor = input_tensor
        self.output_tensors = list(output_tensors)
        self.input_shape = dimensions
        self.input_fix_point = _tensor_fix_point(input_tensor)
        self.output_names = [_tensor_name(tensor, index)
                             for index, tensor in enumerate(output_tensors)]
        if len(set(self.output_names)) != len(self.output_names):
            raise ValueError("VART graph output tensor names must be unique")
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.decoder = decoder

    @classmethod
    def from_runner(cls, runner: Any, *, input_tensor: Any, output_tensors: list[Any],
                    confidence_threshold: float = .30, nms_threshold: float = .45,
                    decoder: Decoder | None = None) -> "VartYoloV8":
        """Construct from injected tensors; used by hardware-free contract tests."""
        return cls(runner, input_tensor, output_tensors,
                   confidence_threshold=confidence_threshold, nms_threshold=nms_threshold,
                   decoder=decoder)

    @classmethod
    def from_xmodel(cls, xmodel: str | Path, *, confidence_threshold: float = .30,
                    nms_threshold: float = .45, decoder: Decoder | None = None) -> "VartYoloV8":
        """Load the only DPU subgraph from a compiled XIR model on the board."""
        path = Path(xmodel)
        if not path.is_file() or path.suffix != ".xmodel":
            raise FileNotFoundError(f"compiled .xmodel is required: {path}")
        try:
            import vart
            import xir
        except ImportError as error:
            raise RuntimeError("VART and XIR are required for the DPU backend") from error
        graph = xir.Graph.deserialize(str(path))
        root = graph.get_root_subgraph()
        dpu_subgraphs = []
        for subgraph in root.toposort_child_subgraph():
            try:
                device = subgraph.get_attr("device")
            except (AttributeError, RuntimeError):
                continue
            if str(device).upper() == "DPU":
                dpu_subgraphs.append(subgraph)
        if len(dpu_subgraphs) != 1:
            raise RuntimeError(f"expected exactly one DPU subgraph, found {len(dpu_subgraphs)}")
        runner = vart.Runner.create_runner(dpu_subgraphs[0], "run")
        return cls(runner, list(runner.get_input_tensors())[0],
                   list(runner.get_output_tensors()),
                   confidence_threshold=confidence_threshold, nms_threshold=nms_threshold,
                   decoder=decoder)

    def _quantized_input(self, frame: np.ndarray) -> np.ndarray:
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise ValueError(f"expected BGR HxWx3 frame, received {frame.shape}")
        _, target_height, target_width, _ = self.input_shape
        source_height, source_width = frame.shape[:2]
        scale = min(target_width / source_width, target_height / source_height)
        resized = cv2.resize(frame, (round(source_width * scale), round(source_height * scale)),
                             interpolation=cv2.INTER_LINEAR)
        canvas = np.full((target_height, target_width, 3), 114, dtype=np.uint8)
        offset_x = (target_width - resized.shape[1]) // 2
        offset_y = (target_height - resized.shape[0]) // 2
        canvas[offset_y:offset_y + resized.shape[0], offset_x:offset_x + resized.shape[1]] = resized
        rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        scale_factor = float(2 ** self.input_fix_point) / 255.0
        values = np.rint(rgb.astype(np.float32) * scale_factor)
        return np.clip(values, -128, 127).astype(np.int8)[None, ...]

    def infer_tensors(self, frame: np.ndarray) -> dict[str, np.ndarray]:
        """Run VART and return outputs converted from their fixed-point form."""
        input_data = self._quantized_input(frame)
        raw_outputs = [np.empty(tuple(int(value) for value in tensor.dims), dtype=np.int8)
                       for tensor in self.output_tensors]
        job_id = self.runner.execute_async([input_data], raw_outputs)
        status = self.runner.wait(job_id)
        if status not in (0, None):
            raise RuntimeError(f"VART job {job_id} failed with status {status}")
        return {
            name: raw.astype(np.float32) / float(2 ** _tensor_fix_point(tensor))
            for name, raw, tensor in zip(self.output_names, raw_outputs, self.output_tensors)
        }

    def infer(self, frame: np.ndarray) -> list[dict[str, object]]:
        """Return person detections only when a tested compiled-model decoder exists."""
        if self.decoder is None:
            raise RuntimeError(
                "no model-specific VART decoder is registered; inspect the compiled .xmodel "
                "outputs and bind a tested decoder before requesting person detections"
            )
        height, width = frame.shape[:2]
        return self.decoder(self.infer_tensors(frame), width, height)
