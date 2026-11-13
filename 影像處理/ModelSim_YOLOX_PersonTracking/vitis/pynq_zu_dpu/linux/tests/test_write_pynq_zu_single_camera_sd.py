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
            "pynq_zu_dpu_single_camera_tracker_python_modules_2022_1.wic",
            "1c1604a7d60febe5e028e4ee64513be971a80f1f061a82caa1c25f480b6255ec",
            "Get-FileHash",
            "Get-Disk -Number $DiskNumber",
            "IsBoot -or $disk.IsSystem",
            "'USB', 'SD'",
            "Get-Partition -DiskNumber $TargetDiskNumber",
            "FSCTL_LOCK_VOLUME",
            "FSCTL_DISMOUNT_VOLUME",
            "DeviceIoControl",
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

    def test_locks_and_dismounts_mounted_volumes_instead_of_offlining_removable_disk(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("Set-Disk", source)
        self.assertIn("$volumeHandles", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
