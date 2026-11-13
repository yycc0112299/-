"""Deployment-bundle contract for the two-board PYNQ runtime."""

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import prepare_pynq_dual_bundle as bundle


class PynqDualBundleTests(unittest.TestCase):
    def test_runtime_sources_include_wifi_gate_and_vart_backend_adapter(self) -> None:
        sources = bundle.runtime_sources()
        self.assertIn(bundle.TRACKING / "pynq_wifi_peer_preflight.py", sources)
        self.assertIn(bundle.TRACKING / "assets" / "yolov8_vart.py", sources)

    def test_runtime_sources_include_usb_video_overlay_verifier(self) -> None:
        self.assertIn(bundle.TRACKING / "verify_pynq_zu_usb_video_overlay.py",
                      bundle.runtime_sources())

    def test_dpu_bundle_uses_the_sd_image_xmodel_and_keeps_the_camera_gate(self) -> None:
        sources = bundle.runtime_sources(dpu_runtime=True)
        self.assertIn(bundle.TRACKING / "pynq_yolov8_dpu_inference.py", sources)
        self.assertIn(bundle.TRACKING / "assets" / "yolov8_vart.py", sources)
        self.assertNotIn(bundle.MODEL, sources)


if __name__ == "__main__":
    unittest.main()
