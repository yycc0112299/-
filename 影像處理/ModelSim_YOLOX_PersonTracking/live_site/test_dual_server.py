"""Synthetic tests for the local person photo and candidate gallery data."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

import dual_server


class SnapshotTests(unittest.TestCase):
    def test_confirmed_people_are_saved_once_and_pair_uses_both_photos(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "test-session").mkdir()
            engine = dual_server.DualEngine.__new__(dual_server.DualEngine)
            engine.lock = threading.RLock()
            engine.enabled = True
            engine.epoch = 1
            engine.session_id = "test-session"
            engine.cameras = (2, 1)
            engine.photos = {}
            engine.matched_pairs = {}
            engine.state = engine._state("live", "test")
            engine.images = [None, None]
            frame_a = np.full((48, 64, 3), 90, dtype=np.uint8)
            frame_b = np.full((48, 64, 3), 170, dtype=np.uint8)
            observed = [
                [dict(track_id=15, status="confirmed", box=[5, 6, 25, 35])],
                [dict(track_id=5, status="confirmed", box=[10, 8, 40, 39])],
            ]
            pair = [dict(a_id=15, b_id=5, score=0.84,
                         status="confirmed_candidate", pair_label="P1")]
            with patch.object(dual_server, "CAPTURE_ROOT", root):
                engine.save_people_and_pairs([frame_a, frame_b], observed, pair, 1)
                engine.save_people_and_pairs([frame_a, frame_b], observed, pair, 1)
                self.assertEqual(len(engine.photos), 2)
                self.assertEqual(len(engine.matched_pairs), 1)
                self.assertTrue(engine.photo("A", 15).startswith(b"\xff\xd8"))
                self.assertTrue(engine.photo("B", 5).startswith(b"\xff\xd8"))
                self.assertIsNone(engine.photo("A", 5))
                manifest = json.loads((root / "test-session" / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(len(manifest["people"]), 2)
                self.assertEqual(manifest["pairs"][0]["photo_a_url"], "/api/photo/A/15")
                self.assertEqual(manifest["pairs"][0]["photo_b_url"], "/api/photo/B/5")
                self.assertEqual(len(list((root / "test-session").glob("*.jpg"))), 2)


if __name__ == "__main__":
    unittest.main()
