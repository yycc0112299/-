"""Contract tests for the on-target GraphRunner camera inference gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np


TRACKING = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TRACKING))
SCRIPT = TRACKING / "pynq_yolov8_dpu_inference.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pynq_yolov8_dpu_inference", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCapture:
    def __init__(self, frames):
        self.frames = list(frames)
        self.released = False

    def read(self):
        if not self.frames:
            return False, None
        return True, self.frames.pop(0)

    def release(self):
        self.released = True


class FakeDetector:
    def __init__(self):
        self.shapes = []

    def detect(self, frame):
        self.shapes.append(frame.shape)
        return [{
            "box": [1, 2, 10, 20],
            "confidence": 0.9,
            "hist": np.full(96, 1 / 96, dtype=np.float32),
        }]


class PynqYoloV8DpuInferenceTests(unittest.TestCase):
    def test_runs_every_camera_frame_through_injected_graph_runner_detector(self):
        module = load_module()
        capture = FakeCapture([np.zeros((240, 320, 3), dtype=np.uint8) for _ in range(3)])
        detector = FakeDetector()

        summary = module.run_camera_inference(capture, detector, frames=3)

        self.assertEqual(summary, {"frames": 3, "detections": 3, "track_ids": 1})
        self.assertEqual(detector.shapes, [(240, 320, 3)] * 3)
        self.assertTrue(capture.released)

    def test_fails_when_the_camera_stops_before_the_requested_inference_count(self):
        module = load_module()
        capture = FakeCapture([np.zeros((240, 320, 3), dtype=np.uint8)])

        with self.assertRaisesRegex(RuntimeError, "camera did not return a frame"):
            module.run_camera_inference(capture, FakeDetector(), frames=2)
        self.assertTrue(capture.released)

    def test_configures_the_original_yolov8_graph_runner_contract(self):
        module = load_module()
        environment = {}
        model = Path("/opt/models/yolov8n_b512.xmodel")

        module.configure_dpu_environment(model, environment)

        self.assertEqual(environment["PERSON_DETECTOR"], "yolov8_vart")
        self.assertEqual(environment["PYNQ_VART_XMODEL"], str(model))
        self.assertEqual(environment["PYNQ_VART_GRAPH_RUNNER"], "1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
