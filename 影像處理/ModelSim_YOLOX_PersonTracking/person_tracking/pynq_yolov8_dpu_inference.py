#!/usr/bin/env python3
"""Run the original compiled YOLOv8 model through GraphRunner on one UVC camera.

This is a target-side gate for the PYNQ-ZU DPU Linux image.  It deliberately
uses one camera: the current board's shared USB topology has not passed a
two-C270 concurrent-stream test.  A successful run proves that requested UVC
frames were received and submitted through the whole original YOLOv8 GraphRunner
graph; an empty scene can therefore pass with zero person detections.
"""

from __future__ import annotations

import argparse
import hashlib
import os
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import cv2

import pipeline


DEFAULT_XMODEL = Path("/opt/models/yolov8n_b512.xmodel")


def configure_dpu_environment(xmodel: Path,
                              environment: MutableMapping[str, str] = os.environ) -> None:
    """Select the heterogeneous GraphRunner route for the original YOLOv8 graph."""
    environment["PERSON_DETECTOR"] = "yolov8_vart"
    environment["PYNQ_VART_XMODEL"] = str(xmodel)
    environment["PYNQ_VART_GRAPH_RUNNER"] = "1"


def open_camera(index: int, width: int, height: int, fps: float) -> Any:
    """Open a low-bandwidth UVC/V4L2 stream on the Linux target."""
    backend = getattr(cv2, "CAP_V4L2", cv2.CAP_ANY)
    capture = cv2.VideoCapture(index, backend)
    capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    capture.set(cv2.CAP_PROP_FPS, fps)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"camera index {index} did not open through V4L2")
    return capture


def run_camera_inference(capture: Any, detector: Any, *, frames: int) -> dict[str, int]:
    """Read exactly ``frames`` images and require GraphRunner detection for each one."""
    if frames < 1:
        raise ValueError("frames must be positive")
    detected = 0
    try:
        for _ in range(frames):
            ok, frame = capture.read()
            if not ok or frame is None:
                raise RuntimeError("camera did not return a frame")
            detected += len(detector.detect(frame))
    finally:
        capture.release()
    return {"frames": frames, "detections": detected}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xmodel", type=Path, default=DEFAULT_XMODEL)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--frames", type=int, default=3)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--fps", type=float, default=5.0)
    args = parser.parse_args()
    if args.camera < 0 or args.frames < 1 or args.width < 1 or args.height < 1 or args.fps <= 0:
        parser.error("camera, frames, dimensions and fps must be positive")
    xmodel = args.xmodel.resolve()
    if xmodel.suffix != ".xmodel" or not xmodel.is_file() or xmodel.stat().st_size == 0:
        raise FileNotFoundError(f"compiled DPU model is missing or empty: {xmodel}")
    configure_dpu_environment(xmodel)
    detector = pipeline.Detector("yolov8_vart")
    capture = open_camera(args.camera, args.width, args.height, args.fps)
    summary = run_camera_inference(capture, detector, frames=args.frames)
    model_hash = hashlib.sha256(xmodel.read_bytes()).hexdigest()
    print(
        "PYNQ_YOLOV8_DPU_CAMERA_PASS "
        f"frames={summary['frames']} detections={summary['detections']} xmodel_sha256={model_hash}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
