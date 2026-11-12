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


if __name__ == "__main__":
    unittest.main()
