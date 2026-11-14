#!/usr/bin/env python3
"""Run the ordered PYNQ-ZU SD acceptance gates through an authenticated UART.

The caller must explicitly name a serial port, username, and environment
variable holding the one-time password.  The password is never an argument,
never written to a transcript, and never printed.  The runtime gate must pass
before the optional DPU camera/YOLOv8 three-frame gate can begin.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import time


TARGET_RUNTIME_DIRECTORY = "/opt/pynq-yolov8/person_tracking"
TARGET_XMODEL = "/opt/models/yolov8n_b512.xmodel"
RUNTIME_PASS_MARKER = "PYNQ_ZU_DPU_LINUX_RUNTIME_PASS"
CAMERA_PASS_MARKER = "PYNQ_YOLOV8_DPU_CAMERA_PASS"
COMMAND_RC_PREFIX = "PYNQ_ZU_HOST_HARNESS_RC="


def reject_line_breaks(value: str, label: str) -> str:
    if not value or "\r" in value or "\n" in value:
        raise ValueError(f"{label} must be nonempty and contain no line breaks")
    return value


def read_until(serial_port: object, markers: tuple[str, ...], timeout_seconds: float) -> str:
    """Return bounded target output once a marker appears; never transmit here."""
    deadline = time.monotonic() + timeout_seconds
    output = bytearray()
    while time.monotonic() < deadline:
        waiting = int(getattr(serial_port, "in_waiting"))
        if waiting:
            output.extend(serial_port.read(waiting))
            text = output.decode("utf-8", errors="replace")
            if any(marker in text for marker in markers):
                return text
        else:
            time.sleep(0.05)
    return output.decode("utf-8", errors="replace")


def send_line(serial_port: object, line: str) -> None:
    serial_port.write((line + "\n").encode("utf-8"))
    serial_port.flush()


def redacted(text: str, password: str) -> str:
    return text.replace(password, "<redacted>")


def command_with_rc(command: str) -> str:
    return f"{command}; rc=$?; printf '\\n{COMMAND_RC_PREFIX}%s\\n' \"$rc\""


def command_return_code(output: str) -> int | None:
    matches = re.findall(rf"{re.escape(COMMAND_RC_PREFIX)}(\d+)", output)
    return int(matches[-1]) if matches else None


def runtime_command() -> str:
    return command_with_rc(
        f"cd {TARGET_RUNTIME_DIRECTORY} && python3 verify_dpu_runtime.py "
        f"--xmodel {TARGET_XMODEL} --require-camera"
    )


def camera_command(camera: int) -> str:
    return command_with_rc(
        f"cd {TARGET_RUNTIME_DIRECTORY} && python3 pynq_yolov8_dpu_inference.py "
        f"--xmodel {TARGET_XMODEL} --camera {camera} --frames 3"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="explicit target UART, for example COM5")
    parser.add_argument("--username", required=True, help="target Linux account name")
    parser.add_argument(
        "--password-env",
        required=True,
        help="name of the environment variable holding the one-time target password",
    )
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--login-timeout", type=float, default=30.0)
    parser.add_argument("--command-timeout", type=float, default=45.0)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--run-camera", action="store_true",
                        help="after the runtime gate passes, run three DPU/YOLOv8 UVC frames")
    parser.add_argument("--output", type=Path,
                        help="optional redacted target transcript for hardware debugging")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.baud <= 0 or args.login_timeout <= 0 or args.command_timeout <= 0 or args.camera < 0:
        raise SystemExit("baud/timeouts must be positive and camera must be non-negative")
    try:
        username = reject_line_breaks(args.username, "username")
        password = reject_line_breaks(os.environ[args.password_env], "password")
    except KeyError:
        print(f"PASSWORD_ENV_MISSING name={args.password_env}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"LOGIN_INPUT_INVALID error={error}", file=sys.stderr)
        return 2

    try:
        import serial
    except ImportError as error:
        raise SystemExit("pyserial is required in the Windows host Python environment") from error

    transcript = ""
    try:
        with serial.Serial(args.port, args.baud, timeout=0.25) as serial_port:
            serial_port.reset_input_buffer()
            send_line(serial_port, "")
            transcript += read_until(serial_port, ("login:", "login :"), args.login_timeout)
            if "login:" not in transcript and "login :" not in transcript:
                print("UART_LOGIN_PROMPT_NOT_SEEN", file=sys.stderr)
                return 3

            send_line(serial_port, username)
            password_prompt = read_until(serial_port, ("Password:", "password:"), args.login_timeout)
            transcript += password_prompt
            if "Password:" not in password_prompt and "password:" not in password_prompt:
                print("UART_PASSWORD_PROMPT_NOT_SEEN", file=sys.stderr)
                return 3

            send_line(serial_port, password)
            shell_prompt = read_until(serial_port, ("$ ", "# "), args.login_timeout)
            transcript += shell_prompt
            if "$ " not in shell_prompt and "# " not in shell_prompt:
                print("UART_SHELL_PROMPT_NOT_SEEN", file=sys.stderr)
                return 3

            send_line(serial_port, runtime_command())
            runtime_output = read_until(serial_port, (COMMAND_RC_PREFIX,), args.command_timeout)
            transcript += runtime_output
            if RUNTIME_PASS_MARKER not in runtime_output or command_return_code(runtime_output) != 0:
                print("PYNQ_ZU_UART_RUNTIME_GATE_FAIL", file=sys.stderr)
                return 4
            print("PYNQ_ZU_UART_RUNTIME_GATE_PASS")

            if args.run_camera:
                send_line(serial_port, camera_command(args.camera))
                camera_output = read_until(serial_port, (COMMAND_RC_PREFIX,), args.command_timeout)
                transcript += camera_output
                if CAMERA_PASS_MARKER not in camera_output or command_return_code(camera_output) != 0:
                    print("PYNQ_ZU_UART_CAMERA_GATE_FAIL", file=sys.stderr)
                    return 5
                print("PYNQ_ZU_UART_CAMERA_GATE_PASS")
    except serial.SerialException as error:
        print(f"UART_OPEN_OR_IO_FAILED port={args.port} error={error}", file=sys.stderr)
        return 3
    finally:
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(redacted(transcript, password), encoding="utf-8", newline="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
