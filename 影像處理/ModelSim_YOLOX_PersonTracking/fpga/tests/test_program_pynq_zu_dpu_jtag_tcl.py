"""Safety contract for volatile programming of the current DPU bitstream."""

from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "program_pynq_zu_dpu_jtag.tcl"


class ProgramPynqZuDpuJtagTests(unittest.TestCase):
    def test_requires_explicit_bitstream_and_current_pynq_zu_device(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            "PYNQ_ZU_DPU_JTAG_BIT",
            "get_hw_devices xczu5_0",
            "set_property PROGRAM.FILE",
            "program_hw_devices",
            "REGISTER.CONFIG_STATUS.BIT04_END_OF_STARTUP_",
            "PYNQ_ZU_DPU_JTAG_PROGRAM_PASS",
        ):
            self.assertIn(required, source)

    def test_is_not_a_persistent_boot_or_application_programmer(self):
        source = SCRIPT.read_text(encoding="utf-8").lower()
        for forbidden in (
            "program_hw_cfgmem",
            "boot.bin",
            "xsdb",
            "dow ",
            "rst -",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
