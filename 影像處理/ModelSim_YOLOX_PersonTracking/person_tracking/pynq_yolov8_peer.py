"""Send one PYNQ C270/YOLOv8/tracker stream to a peer PYNQ over TCP.

The process deliberately sends validated person metadata, never video frames.
Run one copy on each board after Wi-Fi has connected them.  It uses the
project's default YOLOv8 backend unless ``PERSON_DETECTOR`` is explicitly set.
"""

from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import cv2
import numpy as np

from appearance_features import appearance
import peer_protocol
import pipeline


def configure_dpu_backend(xmodel: Path, environment: dict[str, str] = os.environ) -> str:
    """Select the original GraphRunner graph, never the CPU ONNX fallback."""
    xmodel = xmodel.resolve()
    if xmodel.suffix != ".xmodel" or not xmodel.is_file() or xmodel.stat().st_size == 0:
        raise FileNotFoundError(f"compiled DPU xmodel is missing or empty: {xmodel}")
    environment["PERSON_DETECTOR"] = "yolov8_vart"
    environment["PYNQ_VART_XMODEL"] = str(xmodel)
    environment["PYNQ_VART_GRAPH_RUNNER"] = "1"
    return "yolov8_vart"


def build_packet(board_id, frame_id, capture_monotonic_ns, frame, tracked):
    """Map project tracker output to the strict two-board peer schema."""
    height, width = frame.shape[:2]
    packet = {
        "schema": peer_protocol.SCHEMA,
        "board_id": board_id,
        "frame_id": int(frame_id),
        "capture_monotonic_ns": int(capture_monotonic_ns),
        "image_width": int(width),
        "image_height": int(height),
        "detections": [],
    }
    for item in tracked:
        detection = {
                "track_id": int(item["track_id"]),
                "class_name": "person",
                "confidence": float(item["confidence"]),
                "box_xyxy": [int(value) for value in item["box"]],
                "tracking_status": item.get("status", "tentative"),
        }
        if "appearance" in item:
            detection["appearance"] = np.asarray(item["appearance"], dtype=float).tolist()
        packet["detections"].append(detection)
    return packet


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


def send_packet_with_retry(host, port, packet, *, attempts=3, retry_delay=.5,
                           sender=peer_protocol.send_packet, sleep=time.sleep,
                           on_retry=None):
    """Deliver one frame's metadata again after transient TCP peer failures.

    The function retries the *same* validated packet so a receiver reboot does
    not silently turn a captured frame into a dropped result.  A permanent
    failure remains an error after the explicit retry budget rather than being
    reported as a successful cross-board exchange.
    """
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if retry_delay < 0:
        raise ValueError("retry_delay must not be negative")
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            sender(host, port, packet)
            return attempt
        except OSError as error:
            last_error = error
            if attempt == attempts:
                break
            if on_retry is not None:
                on_retry(attempt, error)
            sleep(retry_delay)
    raise ConnectionError(f"peer {host}:{port} unavailable after {attempts} attempts") from last_error


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--board-id", required=True)
    parser.add_argument("--peer-host", required=True)
    parser.add_argument("--port", type=int, default=8790)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--fps", type=float, default=5.0)
    parser.add_argument("--send-attempts", type=int, default=3,
                        help="TCP attempts for each captured metadata packet")
    parser.add_argument("--retry-delay", type=float, default=.5,
                        help="seconds between retry attempts after a TCP failure")
    parser.add_argument("--dpu-xmodel", type=Path,
                        help="run the original GraphRunner/DPU YOLOv8 model from this .xmodel")
    parser.add_argument("--frames", type=int, default=0,
                        help="0 streams forever; a positive count sends that many frames")
    args = parser.parse_args()
    if (not 1 <= args.port <= 65535 or args.camera < 0 or args.width < 1 or args.height < 1
            or args.send_attempts < 1 or args.retry_delay < 0):
        parser.error("invalid camera, dimensions, or port")
    if args.frames < 0:
        parser.error("--frames must be zero or positive")
    backend = configure_dpu_backend(args.dpu_xmodel) if args.dpu_xmodel else None
    detector = pipeline.Detector(backend)
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
            for item in tracked:
                item["appearance"] = appearance(frame, item["box"])
            packet = build_packet(args.board_id, sent, capture_monotonic_ns, frame, tracked)
            used_attempts = send_packet_with_retry(
                args.peer_host, args.port, packet, attempts=args.send_attempts,
                retry_delay=args.retry_delay,
                on_retry=lambda attempt, error: print(
                    f"PYNQ_YOLOV8_PEER_RETRY frame={sent} attempt={attempt} error={error}",
                    flush=True,
                ),
            )
            print(f"PYNQ_YOLOV8_PEER_SENT frame={sent} people={len(tracked)} attempts={used_attempts}",
                  flush=True)
            sent += 1
    finally:
        capture.release()
    print(f"PYNQ_YOLOV8_PEER_PASS frames={sent}")


if __name__ == "__main__":
    main()
