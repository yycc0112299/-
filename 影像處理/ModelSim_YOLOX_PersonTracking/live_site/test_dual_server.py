"""Synthetic tests for the local person photo and candidate gallery data."""
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

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
            engine.photo_observations = {}
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
                self.assertEqual(manifest["pairs"][0]["photo_a_url"], "/api/photo/A/15?v=1")
                self.assertEqual(manifest["pairs"][0]["photo_b_url"], "/api/photo/B/5?v=1")
                self.assertEqual(len(list((root / "test-session").glob("*.jpg"))), 2)

    def test_frontal_face_replaces_first_photo_and_review_freezes_it(self):
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
            engine.photo_observations = {}
            engine.state = engine._state("live", "test")
            engine.images = [None, None]
            frames = [np.full((120, 120, 3), 80, dtype=np.uint8),
                      np.full((120, 120, 3), 160, dtype=np.uint8)]
            observed = [[dict(track_id=1, status="confirmed", box=[10, 10, 110, 110], confidence=.9)],
                        [dict(track_id=2, status="confirmed", box=[10, 10, 110, 110], confidence=.9)]]
            fake_faces = Mock()
            fake_faces.empty.return_value = False
            fake_faces.detectMultiScale.side_effect = [[], [], [(1, 1, 20, 20)], []]
            with patch.object(dual_server, "CAPTURE_ROOT", root), patch.object(dual_server, "FACE_CASCADE", fake_faces):
                for _ in range(3):
                    engine.save_people_and_pairs(frames, observed, [], 1)
                self.assertEqual(engine.photos[("A", 1)]["revision"], 2)
                self.assertTrue(engine.photos[("A", 1)]["face_detected"])
                self.assertEqual(engine.photos[("A", 1)]["photo_url"], "/api/photo/A/1?v=2")
                chosen = engine.retake_photo("A", 1)
                self.assertEqual(chosen["revision"], 3)
                self.assertTrue(chosen["locked"])
                manual = engine.add_manual_pair(1, 2)
                self.assertEqual(manual["pair_label"], "M1")
                engine.review_pair("M1", "different")
                self.assertEqual(engine.matched_pairs["M1"]["review"], "different")
                before = engine.photos[("A", 1)]["revision"]
                engine.save_people_and_pairs(frames, observed, [], 1)
                self.assertEqual(engine.photos[("A", 1)]["revision"], before)
                with self.assertRaises(ValueError):
                    engine.retake_photo("A", 1)
                manifest = json.loads((root / "test-session" / "manifest.json").read_text(encoding="utf-8"))
                self.assertEqual(manifest["pairs"][0]["review"], "different")

    def test_rejected_pair_is_excluded_from_automatic_matcher(self):
        feature = np.zeros((2, 15))
        feature[:, 0] = 1
        first = dict(track_id=1, status="confirmed", appearance=feature)
        second = dict(track_id=2, status="confirmed", appearance=feature)
        matcher = dual_server.CrossCameraMatcher(min_hits=1)
        self.assertEqual(matcher.update([first], [second], excluded_pairs={(1, 2)}), [])
        self.assertEqual(matcher.update([first], [second])[0]["pair_label"], "P1")

    def test_appearance_history_uses_recent_frames_per_track(self):
        history = dual_server.AppearanceHistory(length=3)
        dark = np.zeros((2, 15))
        light = np.zeros((2, 15))
        dark[:, 0] = 1
        light[:, 2] = 1
        np.testing.assert_allclose(history.update("A", 1, dark), dark)
        blended = history.update("A", 1, light)
        np.testing.assert_allclose(blended, .25 * dark + .75 * light)
        np.testing.assert_allclose(history.update("B", 1, dark), dark)

    def test_explicit_stop_deletes_only_current_registered_photos(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            current = root / "20261002_120000_000001"
            previous = root / "20261002_110000_000001"
            current.mkdir()
            previous.mkdir()
            photo = current / "A_0001.jpg"
            photo.write_bytes(b"test JPEG")
            (current / "manifest.json").write_text("{}", encoding="utf-8")
            unrelated = current / "my-notes.txt"
            unrelated.write_text("keep me", encoding="utf-8")
            older_photo = previous / "B_0002.jpg"
            older_photo.write_bytes(b"older JPEG")
            engine = dual_server.DualEngine.__new__(dual_server.DualEngine)
            engine.lock = threading.RLock()
            engine.enabled = True
            engine.epoch = 1
            engine.session_id = current.name
            engine.cameras = (2, 1)
            engine.photos = {("A", 1): {"file": photo.name}}
            engine.matched_pairs = {"P1": {"pair_label": "P1"}}
            engine.state = engine._state("live", "test")
            engine.images = [None, None]
            with patch.object(dual_server, "CAPTURE_ROOT", root):
                engine.control(False, 2, 1)  # Automatic inactivity stop does not delete.
                self.assertTrue(photo.exists())
                self.assertEqual(engine.stop_and_clear(2, 1), 1)
                self.assertFalse(photo.exists())
                self.assertFalse((current / "manifest.json").exists())
                self.assertTrue(unrelated.exists())
                self.assertTrue(older_photo.exists())
                self.assertIsNone(engine.snapshot()["session"])
                self.assertEqual(engine.snapshot()["saved_people"], [])
                self.assertEqual(engine.stop_and_clear(2, 1), 0)


if __name__ == "__main__":
    unittest.main()
