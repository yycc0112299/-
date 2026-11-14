#!/usr/bin/env python3
"""Run the two future PYNQ cross-camera services against each other on loopback.

The program deliberately simulates only the metadata plane: each process owns
one board ID and local detection file, then receives confirmed detections from
the other process over the same TCP framing used on PYNQ Linux.  It does not
claim a physical camera, DPU, Wi-Fi link, or identity-recognition result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
import time

import peer_protocol


ROOT = Path(__file__).resolve().parent
FUSION_SCRIPT = ROOT / "pynq_cross_camera_fusion.py"


def packet(board_id: str, frame_id: int, track_id: int) -> dict:
    """Produce one confirmed, compact person observation for loopback only."""
    upper = [0.0] * 15
    lower = [0.0] * 15
    upper[2] = 1.0
    lower[9] = 1.0
    return {
        "schema": peer_protocol.SCHEMA,
        "board_id": board_id,
        "frame_id": frame_id,
        "capture_monotonic_ns": frame_id,
        "image_width": 640,
        "image_height": 480,
        "detections": [{
            "track_id": track_id,
            "class_name": "person",
            "confidence": 0.95,
            "box_xyxy": [100, 100, 240, 420],
            "tracking_status": "confirmed",
            "appearance": [upper, lower],
        }],
    }


def write_packet(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(peer_protocol.validate_packet(payload), indent=2) + "\n", encoding="utf-8")


def select_port(requested_port: int) -> int:
    if requested_port:
        return requested_port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
        candidate.bind(("127.0.0.1", 0))
        return int(candidate.getsockname()[1])


def wait_for_listener(port: int, timeout_seconds: float = 5.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"fusion service did not listen on loopback port {port}")


def wait_for_result_hits(path: Path, expected_hits: int, timeout_seconds: float = 5.0) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            candidates = payload.get("candidates", [])
            if candidates and candidates[0].get("consecutive_hits") == expected_hits:
                return payload
        except (FileNotFoundError, PermissionError, json.JSONDecodeError):
            pass
        time.sleep(0.05)
    raise RuntimeError(f"no candidate with {expected_hits} consecutive hits appeared in {path}")


def start_fusion_service(board_id: str, local_input: Path, output: Path, port: int,
                         min_hits: int, log_path: Path) -> tuple[subprocess.Popen[str], object]:
    log_file = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable, "-u", str(FUSION_SCRIPT), "serve",
            "--local-board-id", board_id,
            "--local-input", str(local_input),
            "--output", str(output),
            "--bind", "127.0.0.1",
            "--port", str(port),
            "--min-hits", str(min_hits),
        ],
        cwd=ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return process, log_file


def stop_process(process: subprocess.Popen[str], log_file: object) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
    log_file.close()


def run_simulation(output_directory: Path, min_hits: int, port_a: int, port_b: int) -> None:
    output_directory.mkdir(parents=True, exist_ok=True)
    board_a, board_b = "sim-pynq-a", "sim-pynq-b"
    a_local = output_directory / "board_a_local.json"
    b_local = output_directory / "board_b_local.json"
    a_result = output_directory / "board_a_candidates.json"
    b_result = output_directory / "board_b_candidates.json"
    write_packet(a_local, packet(board_a, 1, 101))
    write_packet(b_local, packet(board_b, 1, 202))

    actual_port_a = select_port(port_a)
    actual_port_b = select_port(port_b)
    if actual_port_a == actual_port_b:
        raise ValueError("the two simulated boards must use different TCP ports")

    a_process, a_log = start_fusion_service(
        board_a, a_local, a_result, actual_port_a, min_hits, output_directory / "board_a_service.log")
    b_process, b_log = start_fusion_service(
        board_b, b_local, b_result, actual_port_b, min_hits, output_directory / "board_b_service.log")
    try:
        wait_for_listener(actual_port_a)
        wait_for_listener(actual_port_b)
        for frame_id in range(1, min_hits + 1):
            peer_protocol.send_packet("127.0.0.1", actual_port_a, packet(board_b, frame_id, 202))
            wait_for_result_hits(a_result, frame_id)
            peer_protocol.send_packet("127.0.0.1", actual_port_b, packet(board_a, frame_id, 101))
            wait_for_result_hits(b_result, frame_id)
        a_confirmed = wait_for_result_hits(a_result, min_hits)
        b_confirmed = wait_for_result_hits(b_result, min_hits)
    finally:
        stop_process(a_process, a_log)
        stop_process(b_process, b_log)

    print(
        "TWO_PYNQ_LOOPBACK_SIMULATION_PASS "
        f"ports={actual_port_a},{actual_port_b} "
        f"a_candidates={len(a_confirmed['candidates'])} "
        f"b_candidates={len(b_confirmed['candidates'])} "
        f"output={output_directory}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--min-hits", type=int, default=3)
    parser.add_argument("--port-a", type=int, default=0, help="0 chooses an available loopback port")
    parser.add_argument("--port-b", type=int, default=0, help="0 chooses an available loopback port")
    args = parser.parse_args(argv)
    if args.min_hits < 1:
        parser.error("--min-hits must be at least 1")
    if any(not 0 <= port <= 65535 for port in (args.port_a, args.port_b)):
        parser.error("--port-a and --port-b must be 0 or between 1 and 65535")
    run_simulation(args.output_dir, args.min_hits, args.port_a, args.port_b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
