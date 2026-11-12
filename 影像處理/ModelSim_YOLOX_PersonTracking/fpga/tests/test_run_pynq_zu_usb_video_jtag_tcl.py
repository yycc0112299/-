"""Static safety contract for the temporary USB-video JTAG smoke flow."""
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "run_pynq_zu_usb_video_jtag.tcl"


class RunPynqZuUsbVideoJtagTests(unittest.TestCase):
    def test_uses_explicit_external_artifacts_and_only_volatile_jtag_actions(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            "PYNQ_ZU_JTAG_BIT",
            "PYNQ_ZU_JTAG_PMUFW",
            "PYNQ_ZU_JTAG_FSBL",
            "PYNQ_ZU_JTAG_ELF",
            "PYNQ_ZU_JTAG_RESULT_ADDR",
            "PYNQ_ZU_JTAG_SKIP_RESET",
            "PYNQ_ZU_JTAG_SKIP_FPGA",
            "PYNQ_ZU_JTAG_SKIP_BOOT",
            "name == \"PL\"",
            "name == \"PMU\"",
            "fpga -n -file",
            "dow $pmufw",
            "dow $fsbl",
            "dow $elf",
            "mrd $result_address 5",
            "PYNQ_ZU_USB_VIDEO_JTAG_LAUNCHED",
        ):
            self.assertIn(required, source)
        for forbidden in ("program_hw_cfgmem", "bootgen", "write_cfgmem",
                          "skip_compatibility_check"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
