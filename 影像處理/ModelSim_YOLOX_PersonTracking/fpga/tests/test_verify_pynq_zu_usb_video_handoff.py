"""Offline tests for the USB-video Vivado XSA handoff verifier."""

from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


FPGA_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FPGA_DIR))

from verify_pynq_zu_usb_video_handoff import verify_xsa


HWH = b'''<?xml version="1.0"?>
<EDKSYSTEM><MODULES>
<MODULE INSTANCE="axi_dma_0"><PARAMETERS><PARAMETER NAME="C_BASEADDR" VALUE="0xA0000000"/></PARAMETERS></MODULE>
<MODULE INSTANCE="frame_id_gpio_0"><PARAMETERS><PARAMETER NAME="C_BASEADDR" VALUE="0xA0010000"/></PARAMETERS></MODULE>
<MODULE INSTANCE="yolox_video_rtl_0"><PARAMETERS><PARAMETER NAME="C_BASEADDR" VALUE="0xA0020000"/></PARAMETERS></MODULE>
</MODULES></EDKSYSTEM>'''


class UsbVideoHandoffTests(unittest.TestCase):
    def make_xsa(self, root: Path, *, include_bitstream: bool = True) -> Path:
        xsa = root / "pynq_zu_usb_video.xsa"
        with zipfile.ZipFile(xsa, "w") as archive:
            archive.writestr("pynq_zu_usb_video.hwh", HWH)
            archive.writestr("sysdef.xml", "<system/>")
            archive.writestr("psu_init.c", "/* init */")
            if include_bitstream:
                archive.writestr("pynq_zu_usb_video.bit", b"bitstream")
        return xsa

    def test_accepts_complete_expected_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = verify_xsa(self.make_xsa(Path(temporary)))
        self.assertTrue(report["ok"])
        self.assertEqual(report["addresses"]["axi_dma_0"], "0xA0000000")

    def test_rejects_missing_bitstream(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = verify_xsa(self.make_xsa(Path(temporary), include_bitstream=False))
        self.assertFalse(report["ok"])
        self.assertIn("bitstream", " ".join(report["errors"]).lower())


if __name__ == "__main__":
    unittest.main()
