"""Contract between the YOLOv8 camera loop and the two-board TCP schema."""

from pathlib import Path
import sys
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import peer_protocol
from pynq_yolov8_peer import build_packet


class YoloV8PeerTests(unittest.TestCase):
    def test_build_packet_uses_tracked_persons_and_live_dimensions(self) -> None:
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        packet = build_packet(
            board_id="pynq-a", frame_id=7, capture_monotonic_ns=123,
            frame=frame,
            tracked=[{"track_id": 4, "confidence": .8, "box": [1, 2, 30, 40]}],
        )
        normalized = peer_protocol.validate_packet(packet)
        self.assertEqual(normalized["board_id"], "pynq-a")
        self.assertEqual(normalized["image_width"], 320)
        self.assertEqual(normalized["image_height"], 240)
        self.assertEqual(normalized["detections"][0]["track_id"], 4)
        self.assertEqual(normalized["detections"][0]["box_xyxy"], [1, 2, 30, 40])

    def test_build_packet_keeps_empty_detection_frames(self) -> None:
        packet = build_packet("pynq-b", 2, 456, np.zeros((2, 3, 3), dtype=np.uint8), [])
        self.assertEqual(peer_protocol.validate_packet(packet)["detections"], [])


if __name__ == "__main__":
    unittest.main()
