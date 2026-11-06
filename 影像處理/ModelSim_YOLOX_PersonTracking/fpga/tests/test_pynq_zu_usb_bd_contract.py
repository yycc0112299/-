"""Static safety contract for the reproducible PYNQ-ZU USB-video BD script.

The actual integration check is Vivado's ``validate_bd_design``.  This test
keeps accidental regressions in the board-specific wiring visible before a
long Vivado build is launched.
"""
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "create_pynq_zu_usb_video_bd.tcl"
PACKAGE_SCRIPT = Path(__file__).resolve().parents[1] / "package_pynq_zu_video_ip.tcl"


class PynqZuUsbVideoBdContractTests(unittest.TestCase):
    def test_ps_usb_and_dma_video_path_are_declared(self):
        """Removing PS USB, DDR-facing DMA or 64-bit video transport is a bug."""
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            "PSU__USB0__PERIPHERAL__ENABLE {1}",
            "PSU__USB1__PERIPHERAL__ENABLE {1}",
            "PSU__USE__S_AXI_GP2 {1}",
            "xilinx.com:ip:axi_dma",
            "CONFIG.c_m_axis_mm2s_tdata_width {64}",
            "project.local:video:dual_camera_yolox_axis:1.0",
            "validate_bd_design",
        ):
            self.assertIn(required, source)

        package_source = PACKAGE_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("top dual_camera_yolox_axis_top", package_source)
        self.assertIn("set_property name dual_camera_yolox_axis", package_source)

    def test_usb_is_documented_as_ps_mio_not_pl_gpio(self):
        """The generated design must not pretend USB D+/D- are PL video pins."""
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("MIO 52 .. 63", source)
        self.assertIn("MIO 64 .. 75", source)
        self.assertNotIn("make_bd_pins_external [get_bd_pins zynq_ultra_ps_e_0/USB", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
