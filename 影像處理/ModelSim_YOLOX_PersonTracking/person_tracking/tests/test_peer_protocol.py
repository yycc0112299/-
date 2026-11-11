import sys
import socket
import threading
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import peer_protocol as peer


def valid_packet():
    return {
        "schema": peer.SCHEMA,
        "board_id": "pynq-a",
        "frame_id": 7,
        "capture_monotonic_ns": 123456,
        "image_width": 640,
        "image_height": 480,
        "detections": [{
            "track_id": 3,
            "class_name": "person",
            "confidence": 0.91,
            "box_xyxy": [20, 30, 120, 230],
        }],
    }


class PeerProtocolTests(unittest.TestCase):
    def test_round_trip_preserves_validated_detection(self):
        self.assertEqual(peer.decode_packet(peer.encode_packet(valid_packet()))["detections"][0]["track_id"], 3)

    def test_rejects_box_outside_image(self):
        packet = valid_packet()
        packet["detections"][0]["box_xyxy"] = [20, 30, 641, 230]
        with self.assertRaisesRegex(ValueError, "outside the image"):
            peer.encode_packet(packet)

    def test_rejects_non_person_and_wrong_schema(self):
        packet = valid_packet()
        packet["detections"][0]["class_name"] = "car"
        with self.assertRaisesRegex(ValueError, "only person"):
            peer.encode_packet(packet)
        packet = valid_packet()
        packet["schema"] = "unknown"
        with self.assertRaisesRegex(ValueError, "schema"):
            peer.encode_packet(packet)

    def test_tcp_sender_delivers_one_framed_packet(self):
        ready = threading.Event()
        received = []
        def listener():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
                server.bind(("127.0.0.1", 0)); server.listen(1)
                received.append(server.getsockname()[1]); ready.set()
                connection, _ = server.accept()
                with connection: received.append(peer.read_packet(connection))
        thread = threading.Thread(target=listener)
        thread.start(); self.assertTrue(ready.wait(2))
        peer.send_packet("127.0.0.1", received[0], valid_packet())
        thread.join(2)
        self.assertFalse(thread.is_alive())
        self.assertEqual(received[1]["board_id"], "pynq-a")


if __name__ == "__main__":
    unittest.main()
