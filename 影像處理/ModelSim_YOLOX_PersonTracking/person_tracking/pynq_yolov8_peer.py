"""Send one PYNQ C270/YOLOv8/tracker stream to a peer PYNQ over TCP.

The process deliberately sends validated person metadata, never video frames.
Run one copy on each board after Wi-Fi has connected them.  It uses the
project's default YOLOv8 backend unless ``PERSON_DETECTOR`` is explicitly set.
"""

from __future__ import annotations

import argparse
import time

import cv2

import peer_protocol
import pipeline


def build_packet(board_id, frame_id, capture_monotonic_ns, frame, tracked):
    """Map project tracker output to the strict two-board peer schema."""
    height, width = frame.shape[:2]
    return {
        "schema": peer_protocol.SCHEMA,
        "board_id": board_id,
        "frame_id": int(frame_id),
        "capture_monotonic_ns": int(capture_monotonic_ns),
        "image_width": int(width),
        "image_height": int(height),
        "detections": [
            {
                "track_id": int(item["track_id"]),
                "class_name": "person",
                "confidence": float(item["confidence"]),
                "box_xyxy": [int(value) for value in item["box"]],
            }
            for item in tracked
        ],
    }


def open_camera(index, width, height, fps):
    backend = getattr(cv2, "CAP_V4L2", cv2.CAP_ANY)
    capture = cv2.VideoCapture(index, backend)
    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    capture.set(cv2.CAP_PROP_FPS, fps)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"camera index {index} did not open")
    return capture


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board-id", required=True)
    parser.add_argument("--peer-host", required=True)
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--fps", type=float, default=5.0)
    parser.add_argument("--frames", type=int, default=0,
                        help="0 streams forever; a positive count sends that many frames")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or args.camera < 0 or args.width < 1 or args.height < 1:
        parser.error("invalid camera, dimensions, or port")
    if args.frames < 0:
        parser.error("--frames must be zero or positive")
    detector = pipeline.Detector()
    tracker = pipeline.Tracker()
    capture = open_camera(args.camera, args.width, args.height, args.fps)
    sent = 0
    try:
        while args.frames == 0 or sent < args.frames:
            capture_monotonic_ns = time.monotonic_ns()
            ok, frame = capture.read()
            if not ok or frame is None:
                raise RuntimeError("camera did not return a frame")
            tracked = tracker.update(detector.detect(frame))
            packet = build_packet(args.board_id, sent, capture_monotonic_ns, frame, tracked)
            peer_protocol.send_packet(args.peer_host, args.port, packet)
            print(f"PYNQ_YOLOV8_PEER_SENT frame={sent} people={len(tracked)}", flush=True)
            sent += 1
    finally:
        capture.release()
    print(f"PYNQ_YOLOV8_PEER_PASS frames={sent}")


if __name__ == "__main__":
    main()
