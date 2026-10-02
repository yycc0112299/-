"""Simulate camera A then camera B with one USB camera and a saved appearance gallery."""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np

import pipeline as p
from cross_camera import CrossCameraMatcher
from dual_camera import appearance


def parse_args():
    parser = argparse.ArgumentParser(
        description="Track in camera-A time, save appearance features, then re-associate in camera-B time."
    )
    parser.add_argument("--camera", type=int, default=0, help="USB camera device index")
    parser.add_argument("--a-seconds", type=float, default=10.0, help="Duration assigned to camera A")
    parser.add_argument("--transition-seconds", type=float, default=1.0, help="Ignored interval before camera B")
    parser.add_argument("--b-seconds", type=float, default=10.0, help="Duration assigned to camera B")
    parser.add_argument("--no-display", action="store_true", help="Run without an OpenCV preview window")
    args = parser.parse_args()
    if args.camera < 0 or args.a_seconds <= 0 or args.b_seconds <= 0 or args.transition_seconds < 0:
        parser.error("camera must be non-negative; A/B durations must be positive; transition cannot be negative")
    return args


def appearance_for(frame, detections):
    observed = []
    for detection in detections:
        item = dict(detection)
        item["appearance"] = appearance(frame, item["box"])
        observed.append(item)
    return observed


def aggregate_gallery(samples):
    gallery = []
    for track_id, value in sorted(samples.items()):
        feature = value["sum"] / value["count"]
        feature /= np.maximum(feature.sum(axis=1, keepdims=True), 1e-12)
        gallery.append({
            "track_id": track_id,
            "status": "confirmed",
            "appearance": feature,
            "samples": value["count"],
        })
    return gallery


def json_feature(feature):
    return np.round(feature, 6).tolist()


def draw(frame, detections, label, matches=None, side="A"):
    rendered = frame.copy()
    matches = matches or []
    for detection in detections:
        x0, y0, x1, y1 = detection["box"]
        track_id = detection["track_id"]
        pair = next((m for m in matches if m.get("b_id" if side == "B" else "a_id") == track_id
                     and m.get("status") == "confirmed_candidate"), None)
        suffix = f" {pair['pair_label']} SAME-CANDIDATE" if pair and side == "B" else ""
        text = f"{side}:{track_id} {detection['status']}{suffix}"
        p.cv2.rectangle(rendered, (x0, y0), (x1, y1), (0, 230, 80), 2)
        p.cv2.putText(rendered, text, (x0, max(20, y0 - 7)), p.cv2.FONT_HERSHEY_SIMPLEX,
                      .55, (0, 230, 80), 2)
    p.cv2.putText(rendered, label, (12, 28), p.cv2.FONT_HERSHEY_SIMPLEX,
                  .75, (0, 230, 255), 2)
    return rendered


def main():
    args = parse_args()
    output = p.ROOT / "runs" / ("handoff_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    output.mkdir(parents=True, exist_ok=False)

    capture = p.cv2.VideoCapture(args.camera, p.cv2.CAP_DSHOW)
    if not capture.isOpened():
        raise RuntimeError(f"USB camera {args.camera} could not be opened")
    capture.set(p.cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(p.cv2.CAP_PROP_FRAME_HEIGHT, 480)
    capture.set(p.cv2.CAP_PROP_BUFFERSIZE, 1)

    detector = p.Detector()
    tracker_a = p.Tracker()
    tracker_b = None
    matcher = CrossCameraMatcher()
    samples = {}
    gallery = []
    records = []
    phase_frames = {"A": 0, "transition": 0, "B": 0}
    phase_detections = {"A": 0, "B": 0}
    phase = "A"
    start = time.monotonic()
    b_start = args.a_seconds + args.transition_seconds
    end_at = b_start + args.b_seconds
    quit_key = False

    print(f"Camera {args.camera}: A=0-{args.a_seconds:g}s; B starts at {b_start:g}s; stop at {end_at:g}s.")
    print("Keep the same person visible through the A-to-B switch. Output contains feature/match data, not images.")
    try:
        while True:
            elapsed = time.monotonic() - start
            if elapsed >= end_at:
                break
            ok, frame = capture.read()
            if not ok or frame is None or frame.shape != (480, 640, 3):
                raise RuntimeError("Camera must provide readable 640x480 frames for the full run")

            if elapsed < args.a_seconds:
                current_phase = "A"
                detections = appearance_for(frame, tracker_a.update(detector.detect(frame)))
                phase_frames["A"] += 1
                phase_detections["A"] += len(detections)
                for detection in detections:
                    if detection["status"] != "confirmed":
                        continue
                    track_id = detection["track_id"]
                    if track_id not in samples:
                        samples[track_id] = {"sum": np.zeros((2, 192), dtype=float), "count": 0}
                    samples[track_id]["sum"] += detection["appearance"]
                    samples[track_id]["count"] += 1
                rendered = draw(frame, detections, f"CAMERA A  {elapsed:.1f}s")

            elif elapsed < b_start:
                current_phase = "transition"
                phase_frames["transition"] += 1
                if phase == "A":
                    gallery = aggregate_gallery(samples)
                    tracker_b = p.Tracker()  # New local IDs model a different camera.
                    phase = "transition"
                    print(f"A->B switch: saved {len(gallery)} confirmed appearance profiles; B tracker reset.")
                remaining = max(0.0, b_start - elapsed)
                rendered = frame.copy()
                p.cv2.putText(rendered, f"SWITCH A -> B  {remaining:.1f}s", (12, 30),
                              p.cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 230, 255), 2)
                detections = []

            else:
                current_phase = "B"
                if phase != "B":
                    if tracker_b is None:
                        gallery = aggregate_gallery(samples)
                        tracker_b = p.Tracker()
                    phase = "B"
                    print("Camera B phase started; comparing new tracks to frozen camera-A profiles.")
                detections = appearance_for(frame, tracker_b.update(detector.detect(frame)))
                phase_frames["B"] += 1
                phase_detections["B"] += len(detections)
                matches = matcher.update(gallery, detections) if gallery else []
                rendered = draw(frame, detections, f"CAMERA B  {elapsed:.1f}s", matches, side="B")
                records.append({
                    "elapsed_seconds": round(elapsed, 3),
                    "b_tracks": [
                        {"track_id": d["track_id"], "status": d["status"], "box": d["box"]}
                        for d in detections
                    ],
                    "matches": matches,
                })

            if not args.no_display:
                p.cv2.imshow("Single-camera A-to-B handoff (candidate is not identity proof)", rendered)
                if p.cv2.waitKey(1) & 0xFF == ord("q"):
                    quit_key = True
                    break

    finally:
        elapsed_total = time.monotonic() - start
        capture.release()
        if not args.no_display:
            p.cv2.destroyAllWindows()

    if not gallery:
        gallery = aggregate_gallery(samples)
    confirmed = [
        {"a_id": key[0], "b_id": key[1], "pair_label": f"P{label}"}
        for key, label in sorted(matcher.labels.items())
    ]
    if confirmed:
        result_status = "candidate_found"
    elif not gallery:
        result_status = "no_a_person_detected_or_confirmed"
    elif phase_detections["B"] == 0:
        result_status = "no_person_detected_in_b"
    else:
        result_status = "b_tracks_seen_but_no_candidate_confirmed"
    gallery_json = [
        {"a_track_id": g["track_id"], "samples": g["samples"], "upper_lower_hsv_histograms": json_feature(g["appearance"])}
        for g in gallery
    ]
    (output / "camera_a_feature_gallery.json").write_text(
        json.dumps(gallery_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output / "handoff_matches.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary = {
        "mode": "single_camera_temporal_handoff",
        "camera_index": args.camera,
        "resolution": [640, 480],
        "camera_a_seconds": args.a_seconds,
        "transition_seconds": args.transition_seconds,
        "camera_b_start_seconds": b_start,
        "camera_b_seconds": args.b_seconds,
        "elapsed_seconds": round(elapsed_total, 3),
        "phase_frames": phase_frames,
        "phase_detection_count": phase_detections,
        "gallery_track_count": len(gallery),
        "confirmed_candidates": confirmed,
        "same_person_candidate_found": bool(confirmed),
        "result_status": result_status,
        "completed": not quit_key and elapsed_total >= end_at,
        "note": "One physical camera with a tracker reset and a frozen A-feature gallery; this does not validate two-camera view/lighting differences or identity.",
    }
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"RESULT={output}")


if __name__ == "__main__":
    main()
