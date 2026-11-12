"""Tests for binding deployable DPU files to the exact generated IP metadata."""

import json
from pathlib import Path
import sys
import tempfile
import unittest


LINUX_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LINUX_DIR))

from verify_dpu_artifact_contract import verify_artifact_contract


class DpuArtifactContractTests(unittest.TestCase):
    def test_reports_ip_version_fingerprint_and_hashes_for_complete_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            component = root / "component.xml"
            component.write_text(
                '<component xmlns:spirit="urn:spirit"><spirit:name>dpuczdx8g</spirit:name>'
                '<spirit:version>4.0</spirit:version></component>', encoding="utf-8"
            )
            arch = root / "arch.json"
            arch.write_text(json.dumps({"fingerprint": "0x101000016010400"}), encoding="utf-8")
            bitstream = root / "design.bit"
            bitstream.write_bytes(b"bitstream")
            xsa = root / "design.xsa"
            xsa.write_bytes(b"xsa")
            report = verify_artifact_contract(component, arch, bitstream, xsa)
        self.assertTrue(report["ok"])
        self.assertEqual(report["dpu_ip_version"], "4.0")
        self.assertEqual(report["fingerprint"], "0x101000016010400")
        self.assertEqual(set(report["sha256"]), {"component_xml", "arch_json", "bitstream", "xsa"})


if __name__ == "__main__":
    unittest.main()
