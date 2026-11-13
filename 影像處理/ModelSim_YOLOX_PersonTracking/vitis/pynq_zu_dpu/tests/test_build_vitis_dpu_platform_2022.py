"""Regression checks for the Vitis 2022.1 DPU platform handoff script."""

from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "build_vitis_dpu_platform_2022.tcl"


class BuildVitisDpuPlatform2022Tests(unittest.TestCase):
    def test_reads_the_xpfm_from_vitis_2022_export_directory(self) -> None:
        """Vitis 2022.1 exports XPFM under export/<platform>, not platform root."""
        contents = SCRIPT.read_text(encoding="utf-8")
        self.assertIn(
            'file join $platform_dir export $platform_name "${platform_name}.xpfm"',
            contents,
        )


if __name__ == "__main__":
    unittest.main()
