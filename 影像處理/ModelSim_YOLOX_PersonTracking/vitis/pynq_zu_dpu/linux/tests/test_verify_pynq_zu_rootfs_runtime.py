"""Contracts for the pre-flash PYNQ-ZU rootfs Python runtime gate."""

from __future__ import annotations

import tarfile
import tempfile
import unittest
from pathlib import Path


LINUX_DIR = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(LINUX_DIR))

from verify_pynq_zu_rootfs_runtime import DEPLOYED_RUNTIME_FILES, verify_rootfs_runtime


class PynqZuRootfsRuntimeTests(unittest.TestCase):
    def test_runtime_gate_tracks_the_fusion_sources_that_rootfs_installs(self) -> None:
        self.assertIn(Path("appearance_features.py"), DEPLOYED_RUNTIME_FILES)
        self.assertIn(Path("pynq_cross_camera_fusion.py"), DEPLOYED_RUNTIME_FILES)

    def write_archive(self, root: Path, entries: set[str]) -> Path:
        staging = root / "staging"
        for entry in entries:
            target = staging / entry
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("present\n", encoding="utf-8")
        archive = root / "rootfs.tar.gz"
        with tarfile.open(archive, "w:gz") as output:
            for item in staging.rglob("*"):
                if item.is_file():
                    output.add(item, arcname=f"./{item.relative_to(staging).as_posix()}")
        return archive

    def test_accepts_rootfs_with_runtime_sources_stdlib_and_native_bindings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            (runtime / "person_tracking" / "assets").mkdir(parents=True)
            (runtime / "person_tracking" / "pipeline.py").write_text(
                "import argparse, json\nfrom pathlib import Path\nimport cv2\nimport numpy as np\n",
                encoding="utf-8",
            )
            archive = self.write_archive(root, {
                "usr/lib/python3.9/argparse.py",
                "usr/lib/python3.9/json/__init__.py",
                "usr/lib/python3.9/pathlib.py",
                "usr/lib/python3.9/site-packages/numpy/__init__.py",
                "usr/lib/python3.9/site-packages/cv2.cpython-39-aarch64-linux-gnu.so",
            })
            report = verify_rootfs_runtime(archive, runtime / "person_tracking")
        self.assertTrue(report["ok"])
        self.assertEqual(report["missing"], [])

    def test_rejects_missing_stdlib_before_the_sd_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            runtime.mkdir()
            (runtime / "launcher.py").write_text("import json\n", encoding="utf-8")
            archive = self.write_archive(root, set())
            report = verify_rootfs_runtime(archive, runtime)
        self.assertFalse(report["ok"])
        self.assertIn("stdlib:json", report["missing"])

    def test_rejects_missing_numpy_or_opencv_even_when_stdlib_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime"
            runtime.mkdir()
            (runtime / "launcher.py").write_text("import cv2\nimport numpy\n", encoding="utf-8")
            archive = self.write_archive(root, set())
            report = verify_rootfs_runtime(archive, runtime)
        self.assertFalse(report["ok"])
        self.assertEqual(set(report["missing"]), {"binding:cv2", "binding:numpy"})

    def test_checks_only_the_runtime_files_actually_packaged_for_the_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "person_tracking"
            assets = runtime / "assets"
            assets.mkdir(parents=True)
            (runtime / "pipeline.py").write_text("import json\n", encoding="utf-8")
            (runtime / "appearance_features.py").write_text("import cv2\n", encoding="utf-8")
            (runtime / "cross_camera.py").write_text("import numpy\n", encoding="utf-8")
            (runtime / "peer_protocol.py").write_text("import socket\n", encoding="utf-8")
            (runtime / "pynq_cross_camera_fusion.py").write_text("import json\n", encoding="utf-8")
            (runtime / "pynq_yolov8_dpu_inference.py").write_text("import argparse\n", encoding="utf-8")
            (runtime / "pynq_yolov8_peer.py").write_text("import time\n", encoding="utf-8")
            (runtime / "pynq_wifi_peer_preflight.py").write_text("import socket\n", encoding="utf-8")
            (assets / "yolov8.py").write_text("import pathlib\n", encoding="utf-8")
            (assets / "yolov8_vart.py").write_text("import typing\n", encoding="utf-8")
            # This project-local CPU-only helper is deliberately not installed in rootfs.
            (runtime / "cpu_only.py").write_text("import unittest\n", encoding="utf-8")
            archive = self.write_archive(root, {
                "usr/lib/python3.9/argparse.py",
                "usr/lib/python3.9/json/__init__.py",
                "usr/lib/python3.9/pathlib.py",
                "usr/lib/python3.9/typing.py",
                "usr/lib/python3.9/socket.py",
                "usr/lib/python3.9/time.py",
                "usr/lib/python3.9/site-packages/numpy/__init__.py",
                "usr/lib/python3.9/site-packages/cv2.cpython-39-aarch64-linux-gnu.so",
            })
            report = verify_rootfs_runtime(archive, runtime)
        self.assertTrue(report["ok"])
        self.assertNotIn("unittest", report["required_stdlib"])


if __name__ == "__main__":
    unittest.main()
