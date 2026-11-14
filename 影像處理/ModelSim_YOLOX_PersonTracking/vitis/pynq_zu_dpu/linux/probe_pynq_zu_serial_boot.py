#!/usr/bin/env python3
"""Capture non-destructive PYNQ-ZU UART boot evidence from a known COM port.

This utility intentionally never logs in, sends shell commands, resets the
board, or writes a password.  By default it only reads UART bytes.  ``--wake``
is an explicit opt-in that sends one carriage return, which is useful after a
board has already booted and a Linux getty is waiting for input.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import time


BOOT_MARKERS = ("u-boot", "booting linux", "starting kernel", "linux version")
LOGIN_MARKERS = ("login:", "login :")


def classify_uart_text(text: str) -> str:
    """Return a stable evidence token without inferring a successful boot."""
    lowered = text.lower()
    if any(marker in lowered for marker in LOGIN_MARKERS):
        return "UART_LOGIN_PROMPT_SEEN"
    if any(marker in lowered for marker in BOOT_MARKERS):
        return "UART_BOOT_BANNER_SEEN"
    if text:
        return "UART_OUTPUT_UNCLASSIFIED"
    return "UART_NO_OUTPUT"


def capture_uart(serial_port: object, timeout_seconds: float) -> bytes:
    """Read bytes for a bounded interval without transmitting to the board."""
    deadline = time.monotonic() + timeout_seconds
    captured = bytearray()
    while time.monotonic() < deadline:
        waiting = int(getattr(serial_port, "in_waiting"))
        if waiting:
            captured.extend(serial_port.read(waiting))
        else:
            time.sleep(0.05)
    waiting = int(getattr(serial_port, "in_waiting"))
    if waiting:
        captured.extend(serial_port.read(waiting))
    return bytes(captured)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="explicit UART port, for example COM5")
    parser.add_argument("--baud", type=int, default=115200, help="UART baud rate (default: 115200)")
    parser.add_argument(
        "--timeout",
        type=float,
        default=8.0,
        help="seconds to read before classification (default: 8)",
    )
    parser.add_argument("--output", type=Path, help="optional UTF-8 capture file")
    parser.add_argument(
        "--wake",
        action="store_true",
        help="explicitly send one carriage return before capture; never sends credentials or shell commands",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero")

    try:
        import serial
    except ImportError as error:
        raise SystemExit("pyserial is required: install it in the Windows host Python environment") from error

    try:
        with serial.Serial(args.port, args.baud, timeout=0.25) as serial_port:
            serial_port.reset_input_buffer()
            if args.wake:
                serial_port.write(b"\r")
                serial_port.flush()
            captured = capture_uart(serial_port, args.timeout)
    except serial.SerialException as error:
        print(f"UART_OPEN_FAILED port={args.port} error={error}", file=sys.stderr)
        return 2

    text = captured.decode("utf-8", errors="replace")
    status = classify_uart_text(text)
    print(f"{status} port={args.port} baud={args.baud} bytes={len(captured)}")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="")
        print(f"UART_CAPTURE_WRITTEN path={args.output}")
    if text:
        print(text, end="" if text.endswith("\n") else "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
