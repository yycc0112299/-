"""Contracts for the board-side concurrent UVC capability gate."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import pynq_usb_camera_preflight as preflight


class FakeCapture:
    def __init__(self, successful_reads: int):
        self.successful_reads = successful_reads
        self.reads = 0
        self.released = False

    def isOpened(self):
        return True

    def set(self, *_args):
        return True

    def read(self):
        self.reads += 1
        if self.reads <= 5 + self.successful_reads:
            return True, np.zeros((120, 160, 3), dtype=np.uint8)
        return False, None

    def release(self):
        self.released = True


class PynqUsbCameraPreflightTests(unittest.TestCase):
    def test_concurrent_gate_requires_every_frame_from_both_devices(self):
        captures = {0: FakeCapture(4), 2: FakeCapture(0)}
        with patch.object(preflight.cv2, "VideoCapture", side_effect=lambda index, *_: captures[index]):
            result = preflight.simultaneous_capture(0, 2, 4)
        self.assertEqual(result[0], {"opened": 1, "ok": 4, "failed": 0})
        self.assertEqual(result[2], {"opened": 1, "ok": 0, "failed": 4})
        self.assertTrue(captures[0].released)
        self.assertTrue(captures[2].released)

    def test_concurrent_gate_accepts_two_complete_streams(self):
        captures = {0: FakeCapture(3), 2: FakeCapture(3)}
        with patch.object(preflight.cv2, "VideoCapture", side_effect=lambda index, *_: captures[index]):
            result = preflight.simultaneous_capture(0, 2, 3)
        self.assertEqual(result[0]["ok"], 3)
        self.assertEqual(result[2]["ok"], 3)
        self.assertEqual(result[0]["failed"], 0)
        self.assertEqual(result[2]["failed"], 0)


if __name__ == "__main__":
    unittest.main()
