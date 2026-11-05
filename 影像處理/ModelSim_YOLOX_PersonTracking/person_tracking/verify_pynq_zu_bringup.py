"""On-board PYNQ-ZU AXI-Lite bring-up check for the generated overlay.

Copy this file plus pynq_zu_yolox.bit and pynq_zu_yolox.hwh to the same board
directory, then run it with the PYNQ image's Python.  It deliberately tests
only overlay download and the AXI-Lite mailbox read/write path; the current
bring-up bitstream intentionally holds the video inputs idle.
"""
from __future__ import annotations

from pathlib import Path

from pynq import MMIO, Overlay

MAILBOX_BASE = 0xA000_0000
MAILBOX_LENGTH = 0x1000
FRAME_ID = 0x04
TEST_FRAME_ID = 0x5A17_C0DE


def main() -> None:
    overlay_dir = Path(__file__).resolve().parent
    bit_path = overlay_dir / "pynq_zu_yolox.bit"
    hwh_path = overlay_dir / "pynq_zu_yolox.hwh"
    if not bit_path.is_file() or not hwh_path.is_file():
        raise FileNotFoundError(
            "Expected pynq_zu_yolox.bit and pynq_zu_yolox.hwh beside this script"
        )

    Overlay(str(bit_path), download=True)
    mailbox = MMIO(MAILBOX_BASE, MAILBOX_LENGTH)
    initial_control = mailbox.read(0x00)
    mailbox.write(FRAME_ID, TEST_FRAME_ID)
    observed = mailbox.read(FRAME_ID)
    mailbox.write(FRAME_ID, 0)
    if observed != TEST_FRAME_ID:
        raise RuntimeError(
            f"AXI-Lite mailbox readback failed: wrote 0x{TEST_FRAME_ID:08x}, "
            f"read 0x{observed:08x}"
        )
    print(
        "PYNQ_ZU_BRINGUP_PASS "
        f"base=0x{MAILBOX_BASE:08x} initial_control=0x{initial_control:08x}"
    )


if __name__ == "__main__":
    main()
