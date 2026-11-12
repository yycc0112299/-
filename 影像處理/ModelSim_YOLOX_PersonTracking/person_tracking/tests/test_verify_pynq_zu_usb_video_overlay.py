"""Host tests for the PYNQ USB-video overlay MMIO verification contract."""
from pathlib import Path
import sys
import tempfile
import unittest


PERSON_TRACKING = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PERSON_TRACKING))

from verify_pynq_zu_usb_video_overlay import (  # noqa: E402
    FRAME_GPIO_BASE,
    MAILBOX_BASE,
    verify_overlay,
)


class FakeMmio:
    def __init__(self, base, length):
        self.base = base
        self.length = length
        self.values = {0: 0}
        self.writes = []

    def read(self, offset):
        return self.values.get(offset, 0)

    def write(self, offset, value):
        self.writes.append((offset, value))
        self.values[offset] = value


class VerifyPynqZuUsbVideoOverlayTests(unittest.TestCase):
    def test_downloads_matching_overlay_and_only_exercises_safe_frame_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "pynq_zu_usb_video.bit").write_bytes(b"bit")
            (folder / "pynq_zu_usb_video.hwh").write_text("hwh", encoding="utf-8")
            downloads = []
            mmios = []

            def overlay(path, download):
                downloads.append((path, download))

            def mmio(base, length):
                fake = FakeMmio(base, length)
                mmios.append(fake)
                return fake

            report = verify_overlay(folder, overlay, mmio)

        self.assertEqual(downloads, [(str(folder / "pynq_zu_usb_video.bit"), True)])
        self.assertEqual([item.base for item in mmios], [FRAME_GPIO_BASE, MAILBOX_BASE])
        self.assertEqual(mmios[0].writes, [(0, 0x5A17_C0DE), (0, 0)])
        self.assertEqual(mmios[1].writes, [(4, 0x5A17_C0DE), (4, 0)])
        self.assertEqual(report["frame_id"], 0x5A17_C0DE)

    def test_rejects_missing_matching_hardware_pair_before_download(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            (folder / "pynq_zu_usb_video.bit").write_bytes(b"bit")
            with self.assertRaisesRegex(FileNotFoundError, "pynq_zu_usb_video.bit"):
                verify_overlay(folder, lambda *_: None, lambda *_: None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
