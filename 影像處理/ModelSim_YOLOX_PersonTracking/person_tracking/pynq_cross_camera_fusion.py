"""Conservatively turn two PYNQ metadata streams into cross-camera candidates.

This process never receives video and never rewrites a board's local tracker
ID.  A returned candidate is an appearance-based correlation, not identity.
"""

from __future__ import annotations

import argparse
import json
import socket
from pathlib import Path

import numpy as np

import peer_protocol
from cross_camera import CrossCameraMatcher


def _matcher_observations(packet: dict) -> list[dict]:
    """Keep only evidence that the conservative matcher is allowed to use."""
    return [
        {
            "track_id": detection["track_id"],
            "status": detection["tracking_status"],
            "appearance": np.asarray(detection["appearance"], dtype=float),
        }
        for detection in packet["detections"]
        if detection["tracking_status"] == "confirmed" and "appearance" in detection
    ]


class CrossCameraFusion:
    """Store the latest metadata from two boards and emit candidate-only output."""

    def __init__(self, local_board_id: str, *, threshold=.72, margin=.08, min_hits=3):
        if not isinstance(local_board_id, str) or not local_board_id:
            raise ValueError("local_board_id must be a nonempty string")
        self.local_board_id = local_board_id
        self.matcher = CrossCameraMatcher(threshold=threshold, margin=margin, min_hits=min_hits)
        self.local_packet = None
        self.remote_packet = None

    def update_local(self, packet: dict) -> dict:
        normalized = peer_protocol.validate_packet(packet)
        if normalized["board_id"] != self.local_board_id:
            raise ValueError("local packet board_id does not match the configured local board")
        self.local_packet = normalized
        # A refreshed local frame must not reuse the same remote frame as
        # artificial additional evidence.  Only arrival of a remote frame
        # advances the cross-camera hit counter.
        return self._result()

    def update_remote(self, packet: dict) -> dict:
        normalized = peer_protocol.validate_packet(packet)
        if normalized["board_id"] == self.local_board_id:
            raise ValueError("remote packet must come from a different board")
        self.remote_packet = normalized
        return self._result(advance=True)

    def _result(self, *, advance=False) -> dict:
        remote_board_id = self.remote_packet["board_id"] if self.remote_packet else None
        result = {
            "local_board_id": self.local_board_id,
            "remote_board_id": remote_board_id,
            "candidates": [],
        }
        if not advance or self.local_packet is None or self.remote_packet is None:
            return result
        pairs = self.matcher.update(
            _matcher_observations(self.local_packet),
            _matcher_observations(self.remote_packet),
        )
        result["candidates"] = [
            {
                "local_track_id": pair["a_id"],
                "remote_track_id": pair["b_id"],
                "score": pair["score"],
                "status": pair["status"],
                "consecutive_hits": pair["consecutive_hits"],
                "candidate_label": pair["pair_label"],
            }
            for pair in pairs
            if pair["status"] in {"candidate", "confirmed_candidate"}
        ]
        return result


def _load_packet(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as source:
        return peer_protocol.validate_packet(json.load(source))


def _write_result(result: dict, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_name(f".{output_path.name}.tmp")
    temporary.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)


def serve(fusion: CrossCameraFusion, *, bind: str, port: int,
          local_input: Path, output: Path) -> None:
    """Keep fusion state while remote metadata arrives over the existing TCP framing."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((bind, port))
        listener.listen()
        print(f"PYNQ_CROSS_CAMERA_LISTENING={bind}:{port}", flush=True)
        while True:
            connection, address = listener.accept()
            with connection:
                try:
                    fusion.update_local(_load_packet(local_input))
                    result = fusion.update_remote(peer_protocol.read_packet(connection))
                    _write_result(result, output)
                    print(
                        f"PYNQ_CROSS_CAMERA_CANDIDATES={len(result['candidates'])} "
                        f"from={address[0]}",
                        flush=True,
                    )
                except (OSError, ValueError, json.JSONDecodeError) as error:
                    print(f"PYNQ_CROSS_CAMERA_REJECTED={address[0]}:{error}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    compare = commands.add_parser("compare", help="compare one pair of metadata files once")
    serve_parser = commands.add_parser("serve", help="keep fusion state while receiving peer TCP metadata")
    for command in (compare, serve_parser):
        command.add_argument("--local-board-id", required=True)
        command.add_argument("--local-input", type=Path, required=True,
                             help="latest validated metadata JSON from this board")
        command.add_argument("--output", type=Path, default=Path("cross_camera_candidates.json"))
        command.add_argument("--min-hits", type=int, default=3)
    compare.add_argument("--remote-input", type=Path, required=True,
                         help="validated metadata JSON received from the peer")
    serve_parser.add_argument("--bind", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=8791)
    args = parser.parse_args()
    if args.min_hits < 1 or (args.command == "serve" and not 1 <= args.port <= 65535):
        parser.error("--min-hits must be at least 1 and --port must be from 1 to 65535")
    fusion = CrossCameraFusion(args.local_board_id, min_hits=args.min_hits)
    if args.command == "serve":
        serve(fusion, bind=args.bind, port=args.port, local_input=args.local_input, output=args.output)
        return
    fusion.update_local(_load_packet(args.local_input))
    result = fusion.update_remote(_load_packet(args.remote_input))
    _write_result(result, args.output)
    print(f"PYNQ_CROSS_CAMERA_CANDIDATES={len(result['candidates'])}", flush=True)


if __name__ == "__main__":
    main()
