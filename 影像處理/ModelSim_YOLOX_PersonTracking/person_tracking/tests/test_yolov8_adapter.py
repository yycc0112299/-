"""CPU-only contract tests for the YOLOv8 ONNX person adapter."""

from pathlib import Path
import sys
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "assets"))

from yolov8 import YoloV8


def _prediction(person_score: float, bicycle_score: float = 0.0) -> np.ndarray:
    """One YOLOv8 raw prediction: xywh plus 80 COCO class scores."""
    values = np.zeros(84, dtype=np.float32)
    values[:4] = [320.0, 320.0, 100.0, 200.0]
    values[4] = person_score
    values[5] = bicycle_score
    return values


class YoloV8AdapterTests(unittest.TestCase):
    def test_decodes_person_and_rejects_non_person(self) -> None:
        # Static 640x640 letterbox of a 640x480 source has 80-pixel vertical pads.
        raw = np.stack([_prediction(.90), _prediction(.10, .95)], axis=1)[None, :, :]
        detections = YoloV8.decode_predictions(raw, source_width=640, source_height=480,
                                               confidence_threshold=.25, nms_threshold=.45)
        self.assertEqual(len(detections), 1)
        detection = detections[0]
        self.assertEqual(detection["class_id"], 0)
        self.assertAlmostEqual(detection["confidence"], .90, places=5)
        self.assertEqual(detection["box"], [270, 140, 370, 340])

    def test_accepts_predictions_first_layout_and_clips_boxes(self) -> None:
        raw = _prediction(.75)[None, None, :]
        raw[0, 0, :4] = [10.0, 80.0, 100.0, 100.0]
        detections = YoloV8.decode_predictions(raw, source_width=640, source_height=480,
                                               confidence_threshold=.25, nms_threshold=.45)
        self.assertEqual(len(detections), 1)
        self.assertEqual(detections[0]["box"], [0, 0, 60, 50])


if __name__ == "__main__":
    unittest.main()
