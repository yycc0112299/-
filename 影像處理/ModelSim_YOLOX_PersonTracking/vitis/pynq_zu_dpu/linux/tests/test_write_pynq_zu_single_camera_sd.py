"""Static safety contract for the controlled Windows raw-SD writer."""

from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "write_pynq_zu_single_camera_sd.ps1"


class WritePynqZuSingleCameraSdTests(unittest.TestCase):
    def test_requires_explicit_removable_target_and_expected_image_identity(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            "[int]$DiskNumber",
            "IUnderstandThisErasesDisk",
            "013f29c2f3feb8c0cf26b2f7f3987557905899d44b2157713cb0c9ae8e5791d6",
            "Get-FileHash",
            "Get-Disk -Number $DiskNumber",
            "IsBoot -or $disk.IsSystem",
            "'USB', 'SD'",
            "Set-Disk -Number $DiskNumber -IsOffline $true",
            "Set-Disk -Number $DiskNumber -IsOffline $true -Confirm:$false",
            "ErrorReportPath",
            r"\\.\PhysicalDrive$DiskNumber",
            "ShouldProcess",
        ):
            self.assertIn(required, source)

    def test_never_selects_a_disk_implicitly_or_runs_diskpart(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("Get-Disk | Select-Object -First", source)
        self.assertNotIn("diskpart", source.lower())

    def test_reports_failures_without_a_rethrowing_top_level_trap(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("trap {", source)
        self.assertIn("catch {", source)
        self.assertIn("ErrorReportPath", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
