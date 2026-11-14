"""Safety contract for the host-side UART acceptance harness."""

from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "run_pynq_zu_sd_acceptance.py"


class RunPynqZuSdAcceptanceTests(unittest.TestCase):
    def test_requires_explicit_uart_login_inputs_and_camera_opt_in(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for option in ("--port", "--username", "--password-env", "--run-camera", "--output"):
            self.assertIn(option, result.stdout)

    def test_source_never_embeds_or_prints_password_and_checks_runtime_before_camera(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('os.environ[args.password_env]', source)
        self.assertIn('"<redacted>"', source)
        self.assertIn("PYNQ_ZU_DPU_LINUX_RUNTIME_PASS", source)
        self.assertIn("PYNQ_YOLOV8_DPU_CAMERA_PASS", source)
        self.assertIn("if args.run_camera:", source)
        self.assertLess(
            source.index("PYNQ_ZU_DPU_LINUX_RUNTIME_PASS"),
            source.index("PYNQ_YOLOV8_DPU_CAMERA_PASS"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
