"""Backend-selection contract for the project detector facade."""

from pathlib import Path
import os
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pipeline


class DetectorBackendTests(unittest.TestCase):
    def test_yolov8_is_the_default_backend_and_uses_its_model(self) -> None:
        self.assertEqual(pipeline.Detector.default_backend(), "yolov8")
        self.assertEqual(pipeline.Detector.model_path_for_backend("yolov8").name,
                         "yolov8n.onnx")

    def test_yolox_remains_an_explicit_legacy_backend(self) -> None:
        self.assertEqual(pipeline.Detector.model_path_for_backend("yolox").name,
                         "yolox.onnx")
        with self.assertRaises(ValueError):
            pipeline.Detector.model_path_for_backend("unsupported")

    def test_vart_backend_requires_an_explicit_compiled_xmodel(self) -> None:
        with patch.dict(os.environ, {"PYNQ_VART_XMODEL": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "PYNQ_VART_XMODEL"):
                pipeline.Detector(backend="yolov8_vart")


if __name__ == "__main__":
    unittest.main()
