"""Static contract for the Vivado-native USB-video BD verifier."""

from pathlib import Path
import unittest


FPGA_DIR = Path(__file__).resolve().parents[1]
SCRIPT = FPGA_DIR / "verify_pynq_zu_usb_video_bd.tcl"


class UsbVideoBdVerifierScriptTests(unittest.TestCase):
    def test_reopens_and_validates_the_bd_and_its_control_addresses(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            "open_project",
            "open_bd_design",
            "validate_bd_design",
            "axi_dma_0",
            "frame_id_gpio_0",
            "yolox_video_rtl_0",
            "0xA0000000",
            "0xA0010000",
            "0xA0020000",
            "PYNQ_ZU_USB_VIDEO_BD_VERIFY_PASS",
        ):
            self.assertIn(required, source)


if __name__ == "__main__":
    unittest.main()
