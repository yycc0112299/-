import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pynq_cross_camera_fusion import CrossCameraFusion


def packet(board_id, frame_id, *, track_id=1, color=2, status="confirmed", include_appearance=True):
    detection = {
        "track_id": track_id,
        "class_name": "person",
        "confidence": .9,
        "box_xyxy": [0, 0, 20, 40],
        "tracking_status": status,
    }
    if include_appearance:
        upper = [0.0] * 15
        lower = [0.0] * 15
        upper[color] = lower[color] = 1.0
        detection["appearance"] = [upper, lower]
    return {
        "schema": "pynq-person-detections-v1",
        "board_id": board_id,
        "frame_id": frame_id,
        "capture_monotonic_ns": frame_id,
        "image_width": 20,
        "image_height": 40,
        "detections": [detection],
    }


class CrossCameraFusionTests(unittest.TestCase):
    def test_repeated_confirmed_evidence_produces_candidate_label(self):
        fusion = CrossCameraFusion("pynq-a", min_hits=2)
        fusion.update_local(packet("pynq-a", 1, track_id=4))
        first = fusion.update_remote(packet("pynq-b", 1, track_id=9))
        fusion.update_local(packet("pynq-a", 2, track_id=4))
        second = fusion.update_remote(packet("pynq-b", 2, track_id=9))

        self.assertEqual(first["candidates"][0]["status"], "candidate")
        self.assertEqual(second["candidates"][0]["status"], "confirmed_candidate")
        self.assertEqual(second["candidates"][0]["candidate_label"], "P1")
        self.assertEqual(second["candidates"][0]["local_track_id"], 4)
        self.assertEqual(second["candidates"][0]["remote_track_id"], 9)

    def test_missing_appearance_or_tentative_status_never_becomes_candidate(self):
        fusion = CrossCameraFusion("pynq-a", min_hits=1)
        fusion.update_local(packet("pynq-a", 1, include_appearance=False))
        self.assertEqual(fusion.update_remote(packet("pynq-b", 1))["candidates"], [])
        fusion.update_local(packet("pynq-a", 2, status="tentative"))
        self.assertEqual(fusion.update_remote(packet("pynq-b", 2))["candidates"], [])

    def test_empty_remote_evidence_breaks_candidate_streak(self):
        fusion = CrossCameraFusion("pynq-a", min_hits=2)
        fusion.update_local(packet("pynq-a", 1))
        fusion.update_remote(packet("pynq-b", 1))
        fusion.update_local(packet("pynq-a", 2))
        fusion.update_remote({**packet("pynq-b", 2), "detections": []})
        fusion.update_local(packet("pynq-a", 3))
        result = fusion.update_remote(packet("pynq-b", 3))
        self.assertEqual(result["candidates"][0]["status"], "candidate")

    def test_local_refresh_does_not_reuse_a_stale_remote_frame_as_new_evidence(self):
        fusion = CrossCameraFusion("pynq-a", min_hits=2)
        fusion.update_local(packet("pynq-a", 1))
        self.assertEqual(fusion.update_remote(packet("pynq-b", 1))["candidates"][0]["status"], "candidate")
        self.assertEqual(fusion.update_local(packet("pynq-a", 2))["candidates"], [])
        self.assertEqual(
            fusion.update_remote(packet("pynq-b", 2))["candidates"][0]["status"],
            "confirmed_candidate",
        )

    def test_rejects_wrong_local_or_same_board_packet(self):
        fusion = CrossCameraFusion("pynq-a")
        with self.assertRaisesRegex(ValueError, "local board"):
            fusion.update_local(packet("pynq-b", 1))
        fusion.update_local(packet("pynq-a", 1))
        with self.assertRaisesRegex(ValueError, "different board"):
            fusion.update_remote(packet("pynq-a", 1))


if __name__ == "__main__":
    unittest.main()
