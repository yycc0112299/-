"""Contracts for choosing CPU-ONNX versus DPU-GraphRunner deployment gates."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "pynq_system_preflight.py"


def load_module():
    spec = importlib.util.spec_from_file_location("pynq_system_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PynqSystemPreflightTests(unittest.TestCase):
    def test_dpu_gate_checks_graph_runner_modules_and_the_sd_image_model(self):
        module = load_module()
        self.assertEqual(
            module.required_modules(dpu_runtime=True),
            ("numpy", "cv2", "vart", "xir", "vitis_ai_library"),
        )
        self.assertEqual(module.model_path(dpu_runtime=True), Path("/opt/models/yolov8n_b512.xmodel"))

    def test_cpu_gate_keeps_onnx_runtime_and_bundle_local_model_contract(self):
        module = load_module()
        self.assertEqual(module.required_modules(dpu_runtime=False), ("numpy", "cv2", "onnxruntime"))
        self.assertEqual(module.model_path(dpu_runtime=False), module.MODEL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
