"""Safety contract for the read-only Vivado Hardware Manager JTAG scan."""
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scan_pynq_zu_jtag.tcl"


class ScanPynqZuJtagTests(unittest.TestCase):
    def test_connects_and_lists_targets_without_programming_hardware(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for required in ("open_hw_manager", "connect_hw_server", "get_hw_targets"):
            self.assertIn(required, source)
        for forbidden in ("program_hw_devices", "program_hw_cfgmem", "set_property PROGRAM.FILE"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
