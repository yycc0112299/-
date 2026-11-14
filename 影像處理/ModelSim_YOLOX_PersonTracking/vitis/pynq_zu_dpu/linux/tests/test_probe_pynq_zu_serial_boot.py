"""Contract tests for the non-destructive Windows UART boot evidence tool."""

from pathlib import Path
import subprocess
import sys
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "probe_pynq_zu_serial_boot.py"


class ProbePynqZuSerialBootTests(unittest.TestCase):
    def test_offers_explicit_port_timeout_output_and_opt_in_wake(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for option in ("--port", "--baud", "--timeout", "--output", "--wake"):
            self.assertIn(option, result.stdout)

    def test_source_keeps_uart_input_non_destructive_by_default(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("UART_BOOT_BANNER_SEEN", source)
        self.assertIn("UART_LOGIN_PROMPT_SEEN", source)
        self.assertIn("UART_NO_OUTPUT", source)
        self.assertIn("if args.wake:", source)
        self.assertIn("serial_port.write(b\"\\r\")", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
