"""Verify that the USB-video PYNQ overlay loads and exposes its control IPs.

Place this script beside the matching ``pynq_zu_usb_video.bit`` and ``.hwh``
files on an SD-booted PYNQ-ZU.  It intentionally never writes the mailbox
CONTROL register and therefore cannot enqueue a video command or start DMA.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable


FRAME_GPIO_BASE = 0xA001_0000
MAILBOX_BASE = 0xA002_0000
MMIO_LENGTH = 0x1000
FRAME_ID_OFFSET = 0x00
MAILBOX_FRAME_ID_OFFSET = 0x04
TEST_FRAME_ID = 0x5A17_C0DE


def verify_overlay(
    overlay_dir: Path,
    overlay_factory: Callable[..., Any],
    mmio_factory: Callable[..., Any],
) -> dict[str, int]:
    """Download the overlay and round-trip only inert frame-ID registers."""
    bit_path = overlay_dir / "pynq_zu_usb_video.bit"
    hwh_path = overlay_dir / "pynq_zu_usb_video.hwh"
    if not bit_path.is_file() or not hwh_path.is_file():
        raise FileNotFoundError(
            "Expected pynq_zu_usb_video.bit and pynq_zu_usb_video.hwh beside this script"
        )

    overlay_factory(str(bit_path), download=True)
    frame_gpio = mmio_factory(FRAME_GPIO_BASE, MMIO_LENGTH)
    mailbox = mmio_factory(MAILBOX_BASE, MMIO_LENGTH)
    initial_mailbox_control = mailbox.read(0)
    try:
        frame_gpio.write(FRAME_ID_OFFSET, TEST_FRAME_ID)
        observed_gpio = frame_gpio.read(FRAME_ID_OFFSET)
        mailbox.write(MAILBOX_FRAME_ID_OFFSET, TEST_FRAME_ID)
        observed_mailbox = mailbox.read(MAILBOX_FRAME_ID_OFFSET)
    finally:
        frame_gpio.write(FRAME_ID_OFFSET, 0)
        mailbox.write(MAILBOX_FRAME_ID_OFFSET, 0)

    if observed_gpio != TEST_FRAME_ID or observed_mailbox != TEST_FRAME_ID:
        raise RuntimeError(
            "USB-video frame-ID readback failed: "
            f"gpio=0x{observed_gpio:08x}, mailbox=0x{observed_mailbox:08x}"
        )
    return {
        "frame_id": TEST_FRAME_ID,
        "initial_mailbox_control": initial_mailbox_control,
    }


def main() -> None:
    # Import only on target: host tests do not require the PYNQ package.
    from pynq import MMIO, Overlay

    report = verify_overlay(Path(__file__).resolve().parent, Overlay, MMIO)
    print(
        "PYNQ_ZU_USB_VIDEO_OVERLAY_PASS "
        f"frame_id=0x{report['frame_id']:08x} "
        f"initial_control=0x{report['initial_mailbox_control']:08x}"
    )


if __name__ == "__main__":
    main()
