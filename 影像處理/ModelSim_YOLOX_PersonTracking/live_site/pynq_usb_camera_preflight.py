"""Read-only PYNQ-ZU UVC camera preflight for the two-camera dashboard."""
from __future__ import annotations

import argparse
from pathlib import Path
import threading

import cv2


def configure_low_bandwidth(cap) -> None:
    """Ask each C270 for the repeatable low-bandwidth PYNQ test mode."""
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FPS, 10)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)


def inspect(index: int) -> tuple[int, int]:
    cap = cv2.VideoCapture(index, getattr(cv2, "CAP_V4L2", cv2.CAP_ANY))
    try:
        if not cap.isOpened():
            raise RuntimeError(f"camera index {index} did not open")
        configure_low_bandwidth(cap)
        ok, frame = cap.read()
        if not ok or frame is None:
            raise RuntimeError(f"camera index {index} did not return a frame")
        height, width = frame.shape[:2]
        if frame.ndim != 3 or frame.shape[2] != 3:
            raise RuntimeError(f"camera index {index} returned unsupported shape {frame.shape}")
        return width, height
    finally:
        cap.release()


def simultaneous_capture(camera_a: int, camera_b: int, frames: int) -> dict[int, dict[str, int]]:
    """Capture both UVC devices concurrently, not merely open them sequentially.

    A successful open is not enough evidence that a shared USB controller can
    sustain two streams.  This deliberately gives each device its own reader
    thread, then insists every requested frame is delivered on both sides.
    """
    if frames <= 0:
        raise ValueError("frames must be positive")
    start = threading.Barrier(3)
    outcome: dict[int, dict[str, int]] = {}
    lock = threading.Lock()

    def worker(index: int) -> None:
        cap = cv2.VideoCapture(index, getattr(cv2, "CAP_V4L2", cv2.CAP_ANY))
        try:
            if not cap.isOpened():
                record = {"opened": 0, "ok": 0, "failed": frames}
                with lock:
                    outcome[index] = record
                start.wait()
                return
            configure_low_bandwidth(cap)
            # Discard exposure/format-negotiation frames before the shared test.
            for _ in range(5):
                cap.read()
            start.wait()
            ok = failed = 0
            for _ in range(frames):
                success, frame = cap.read()
                if success and frame is not None and frame.ndim == 3 and frame.shape[2] == 3:
                    ok += 1
                else:
                    failed += 1
            with lock:
                outcome[index] = {"opened": 1, "ok": ok, "failed": failed}
        finally:
            cap.release()

    threads = [threading.Thread(target=worker, args=(index,), daemon=True)
               for index in (camera_a, camera_b)]
    for thread in threads:
        thread.start()
    start.wait()
    for thread in threads:
        thread.join()
    return outcome


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera-a", type=int, default=0)
    parser.add_argument("--camera-b", type=int, default=1)
    parser.add_argument("--simultaneous", action="store_true",
                        help="require concurrent low-bandwidth frames from both cameras")
    parser.add_argument("--frames", type=int, default=30)
    args = parser.parse_args()
    if args.camera_a == args.camera_b or min(args.camera_a, args.camera_b) < 0:
        parser.error("camera-a and camera-b must be distinct non-negative indices")
    devices = sorted(str(path) for path in Path("/dev").glob("video*"))
    print("PYNQ_VIDEO_DEVICES=" + ",".join(devices))
    for label, index in (("A", args.camera_a), ("B", args.camera_b)):
        width, height = inspect(index)
        print(f"PYNQ_CAMERA_{label}_PASS=index={index} size={width}x{height}")
    if args.simultaneous:
        results = simultaneous_capture(args.camera_a, args.camera_b, args.frames)
        print("PYNQ_SIMULTANEOUS_CAMERA_RESULT=" + repr(results))
        if any(row["opened"] != 1 or row["ok"] != args.frames for row in results.values()):
            raise RuntimeError(
                "PYNQ_SIMULTANEOUS_CAMERA_FAIL: both cameras must deliver every frame; "
                "change the USB topology or use one camera per board"
            )
        print(f"PYNQ_SIMULTANEOUS_CAMERA_PASS=frames={args.frames}")


if __name__ == "__main__":
    main()
