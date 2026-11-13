"""Contract between the YOLOv8 camera loop and the two-board TCP schema."""

from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import peer_protocol
from appearance_features import appearance
from pynq_yolov8_peer import build_packet, configure_dpu_backend, send_packet_with_retry


class YoloV8PeerTests(unittest.TestCase):
    def test_sender_serializes_two_region_appearance_from_a_frame(self) -> None:
        frame = np.zeros((20, 10, 3), dtype=np.uint8)
        frame[:10, :, :] = [0, 0, 255]
        frame[10:, :, :] = [0, 255, 0]
        feature = appearance(frame, [0, 0, 10, 20])
        packet = build_packet(
            "pynq-a", 1, 2, frame,
            [{"track_id": 7, "confidence": .9, "box": [0, 0, 10, 20],
              "status": "confirmed", "appearance": feature}],
        )
        serialized = packet["detections"][0]["appearance"]
        self.assertEqual((len(serialized), len(serialized[0])), (2, 15))
        self.assertAlmostEqual(sum(serialized[0]), 1.0)
        self.assertAlmostEqual(sum(serialized[1]), 1.0)
        self.assertEqual(packet["detections"][0]["tracking_status"], "confirmed")

    def test_dpu_model_selects_graph_runner_without_cpu_onnx_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            xmodel = Path(temporary) / "yolov8n_b512.xmodel"
            xmodel.write_bytes(b"compiled")
            environment: dict[str, str] = {}
            backend = configure_dpu_backend(xmodel, environment)
        self.assertEqual(backend, "yolov8_vart")
        self.assertEqual(environment["PERSON_DETECTOR"], "yolov8_vart")
        self.assertEqual(environment["PYNQ_VART_GRAPH_RUNNER"], "1")
        self.assertTrue(environment["PYNQ_VART_XMODEL"].endswith("yolov8n_b512.xmodel"))

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

    def test_retries_the_same_packet_after_transient_peer_disconnect(self) -> None:
        packet = build_packet("pynq-a", 9, 999, np.zeros((2, 3, 3), dtype=np.uint8), [])
        sent = []
        pauses = []

        def transient_sender(host, port, payload):
            sent.append((host, port, payload))
            if len(sent) < 3:
                raise ConnectionRefusedError("peer rebooting")

        attempts = send_packet_with_retry(
            "192.0.2.2", 8790, packet, attempts=3, retry_delay=.25,
            sender=transient_sender, sleep=pauses.append,
        )
        self.assertEqual(attempts, 3)
        self.assertEqual(pauses, [.25, .25])
        self.assertTrue(all(payload is packet for _, _, payload in sent))

    def test_does_not_silently_drop_when_peer_stays_unavailable(self) -> None:
        calls = []

        def unavailable_sender(*_):
            calls.append(1)
            raise ConnectionResetError("peer still rebooting")

        with self.assertRaisesRegex(ConnectionError, "after 2 attempts"):
            send_packet_with_retry(
                "192.0.2.2", 8790, {"not": "a packet"}, attempts=2,
                sender=unavailable_sender, sleep=lambda _: None,
            )
        self.assertEqual(calls, [1, 1])


if __name__ == "__main__":
    unittest.main()
