"""Static contract for packaging the USB-video Vivado overlay.

The packager deliberately only copies local implementation artifacts.  Board
programming belongs to a separately authorised SD/Linux deployment step.
"""
from pathlib import Path
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "prepare_pynq_zu_usb_video_overlay.ps1"


class PreparePynqZuUsbVideoOverlayTests(unittest.TestCase):
    def test_packages_matching_usb_video_bit_and_hwh_without_board_access(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for required in (
            "pynq_zu_usb_video_wrapper.bit",
            "pynq_zu_usb_video.hwh",
            "$overlayBase = 'pynq_zu_usb_video'",
            '"$overlayBase.bit"',
            '"$overlayBase.hwh"',
        ):
            self.assertIn(required, source)
        self.assertNotIn("scp ", source.lower())
        self.assertNotIn("ssh ", source.lower())
        self.assertNotIn("bootgen", source.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
