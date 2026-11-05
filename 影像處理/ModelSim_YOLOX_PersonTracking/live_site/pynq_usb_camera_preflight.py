"""Read-only PYNQ-ZU UVC camera preflight for the two-camera dashboard."""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def inspect(index: int) -> tuple[int, int]:
    cap = cv2.VideoCapture(index, getattr(cv2, "CAP_V4L2", cv2.CAP_ANY))
    try:
        if not cap.isOpened():
            raise RuntimeError(f"camera index {index} did not open")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError(f"camera index {index} did not return a frame")
        height, width = frame.shape[:2]
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise RuntimeError(f"camera index {index} returned unsupported shape {frame.shape}")
        return width, height
    finally:
        cap.release()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera-a", type=int, default=0)
    parser.add_argument("--camera-b", type=int, default=1)
    args = parser.parse_args()
    if args.camera_a == args.camera_b or min(args.camera_a, args.camera_b) < 0:
        parser.error("camera-a and camera-b must be distinct non-negative indices")
    devices = sorted(str(path) for path in Path("/dev").glob("video*"))
    print("PYNQ_VIDEO_DEVICES=" + ",".join(devices))
    for label, index in (("A", args.camera_a), ("B", args.camera_b)):
        width, height = inspect(index)
        print(f"PYNQ_CAMERA_{label}_PASS=index={index} size={width}x{height}")


if __name__ == "__main__":
    main()
