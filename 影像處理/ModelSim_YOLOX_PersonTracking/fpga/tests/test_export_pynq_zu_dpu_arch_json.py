"""Contract for extracting the exact generated DPU compiler architecture."""

from pathlib import Path
import json
import sys
import tempfile
import unittest


FPGA_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FPGA_DIR))

from export_pynq_zu_dpu_arch_json import export_architecture


class ExportDpuArchitectureTests(unittest.TestCase):
    def test_exports_exact_generated_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "generated" / "arch.json"
            source.parent.mkdir()
            source.write_text('{"fingerprint":"0x101000016010400"}\n', encoding="utf-8")
            output = root / "deployment" / "pynq_zu_dpu_b512_arch.json"
            fingerprint = export_architecture(source, output)
            self.assertEqual(fingerprint, "0x101000016010400")
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")),
                             {"fingerprint": "0x101000016010400"})

    def test_rejects_missing_or_invalid_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "arch.json"
            output = Path(temporary) / "output.json"
            source.write_text('{"fingerprint":"unknown"}\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "fingerprint"):
                export_architecture(source, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
