"""Versioned TCP exchange for one-board/one-camera person detections.

This deliberately transports compact inference results rather than USB video.
It is runnable on the PYNQ Linux image with the Python standard library, and
the same schema can be emitted by the current YOLOX code or a future YOLOv8
VART/DPU adapter.
"""
import argparse
import json
import socket
from pathlib import Path

SCHEMA = "pynq-person-detections-v1"
MAX_PACKET_BYTES = 64 * 1024


def _integer(value, field, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return value


def _number(value, field, minimum=None, maximum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be a number")
    value = float(value)
    if ((minimum is not None and value < minimum) or
            (maximum is not None and value > maximum)):
        raise ValueError(f"{field} is outside its allowed range")
    return value


def validate_packet(packet):
    """Return a normalized packet or raise ValueError before it reaches fusion."""
    if not isinstance(packet, dict) or packet.get("schema") != SCHEMA:
        raise ValueError("unsupported packet schema")
    board_id = packet.get("board_id")
    if not isinstance(board_id, str) or not board_id or len(board_id) > 64:
        raise ValueError("board_id must be a nonempty string of at most 64 characters")
    width = _integer(packet.get("image_width"), "image_width", 1)
    height = _integer(packet.get("image_height"), "image_height", 1)
    normalized = {
        "schema": SCHEMA,
        "board_id": board_id,
        "frame_id": _integer(packet.get("frame_id"), "frame_id"),
        "capture_monotonic_ns": _integer(packet.get("capture_monotonic_ns"), "capture_monotonic_ns"),
        "image_width": width,
        "image_height": height,
        "detections": [],
    }
    detections = packet.get("detections")
    if not isinstance(detections, list) or len(detections) > 256:
        raise ValueError("detections must be a list of at most 256 items")
    for index, detection in enumerate(detections):
        if not isinstance(detection, dict):
            raise ValueError(f"detections[{index}] must be an object")
        box = detection.get("box_xyxy")
        if not isinstance(box, list) or len(box) != 4:
            raise ValueError(f"detections[{index}].box_xyxy must have four coordinates")
        x0, y0, x1, y1 = (_integer(value, f"detections[{index}].box_xyxy") for value in box)
        if x0 >= x1 or y0 >= y1 or x1 > width or y1 > height:
            raise ValueError(f"detections[{index}].box_xyxy is outside the image")
        normalized["detections"].append({
            "track_id": _integer(detection.get("track_id"), f"detections[{index}].track_id", 1),
            "class_name": "person",
            "confidence": _number(detection.get("confidence"), f"detections[{index}].confidence", 0.0, 1.0),
            "box_xyxy": [x0, y0, x1, y1],
        })
        if detection.get("class_name") != "person":
            raise ValueError("only person detections are accepted by this protocol version")
    return normalized


def encode_packet(packet):
    payload = (json.dumps(validate_packet(packet), separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
    if len(payload) > MAX_PACKET_BYTES:
        raise ValueError("packet exceeds maximum size")
    return payload


def decode_packet(payload):
    if len(payload) > MAX_PACKET_BYTES:
        raise ValueError("packet exceeds maximum size")
    try:
        return validate_packet(json.loads(payload.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("packet is not valid UTF-8 JSON") from exc


def read_packet(connection):
    chunks = bytearray()
    while True:
        chunk = connection.recv(min(4096, MAX_PACKET_BYTES + 1 - len(chunks)))
        if not chunk:
            raise ValueError("peer disconnected before completing a packet")
        chunks.extend(chunk)
        if len(chunks) > MAX_PACKET_BYTES:
            raise ValueError("packet exceeds maximum size")
        newline = chunks.find(b"\n")
        if newline >= 0:
            return decode_packet(bytes(chunks[:newline]))


def send_packet(host, port, packet, timeout=5.0):
    with socket.create_connection((host, port), timeout=timeout) as connection:
        connection.sendall(encode_packet(packet))


def receive_forever(bind, port, output_path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((bind, port))
        listener.listen()
        print(f"PYNQ_PEER_LISTENING={bind}:{port}", flush=True)
        while True:
            connection, address = listener.accept()
            with connection:
                try:
                    packet = read_packet(connection)
                    output_path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
                    print(f"PYNQ_PEER_PACKET_ACCEPTED={packet['board_id']}:{packet['frame_id']} from {address[0]}", flush=True)
                except ValueError as exc:
                    print(f"PYNQ_PEER_PACKET_REJECTED={address[0]}:{exc}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="PYNQ two-board person-detection TCP protocol")
    commands = parser.add_subparsers(dest="command", required=True)
    receiver = commands.add_parser("receive", help="receive validated packets forever")
    receiver.add_argument("--bind", default="0.0.0.0")
    receiver.add_argument("--port", type=int, default=8790)
    receiver.add_argument("--output", type=Path, default=Path("peer_latest.json"))
    sender = commands.add_parser("send", help="send one JSON packet")
    sender.add_argument("--host", required=True)
    sender.add_argument("--port", type=int, default=8790)
    sender.add_argument("--input", type=argparse.FileType("r"), required=True)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be from 1 to 65535")
    if args.command == "send":
        try:
            send_packet(args.host, args.port, json.load(args.input))
        finally:
            args.input.close()
        print("PYNQ_PEER_SEND_PASS")
        return
    receive_forever(args.bind, args.port, args.output)


if __name__ == "__main__":
    main()
