"""PYNQ MMIO writer for the RTL YOLOX bbox mailbox.

This is deliberately small and depends on ``pynq`` only when it is run on a
PYNQ image.  It turns the JSON packet emitted by dual_camera.py into the exact
AXI4-Lite writes expected by fpga/yolox_bbox_axilite.v.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Protocol


class MMIOWriter(Protocol):
    def write(self, offset: int, value: int) -> None: ...
    def read(self, offset: int) -> int: ...


CONTROL = 0x00
FRAME_ID = 0x04
A_X = 0x08
A_Y = 0x0C
B_X = 0x10
B_Y = 0x14
STATUS = CONTROL
PENDING = 0x1
PAIR_PRESENT = 0x2
OVERRUN = 0x4


def _validate_box(box: list[int], name: str) -> tuple[int, int, int, int]:
    if len(box) != 4 or any(not isinstance(value, int) for value in box):
        raise ValueError(f"{name} must be four integer x0,y0,x1,y1 values")
    x0, y0, x1, y1 = box
    if not (0 <= x0 < x1 <= 1023 and 0 <= y0 < y1 <= 1023):
        raise ValueError(f"{name} coordinates must be ordered 10-bit values: {box}")
    return x0, y0, x1, y1


def pack_pair(first: int, second: int) -> int:
    """Pack two 10-bit co-ordinates into the Verilog register layout."""
    return (first & 0x3FF) | ((second & 0x3FF) << 16)


@dataclass(frozen=True)
class YoloxRtlPacket:
    frame: int
    pair_present: bool
    a_box: tuple[int, int, int, int]
    b_box: tuple[int, int, int, int]

    @classmethod
    def from_json(cls, packet: dict[str, Any]) -> "YoloxRtlPacket":
        frame = packet.get("frame")
        if not isinstance(frame, int) or frame < 0:
            raise ValueError("packet.frame must be a non-negative integer")
        return cls(
            frame=frame,
            pair_present=bool(packet.get("pair_present")),
            a_box=_validate_box(packet["a"]["box"], "packet.a.box"),
            b_box=_validate_box(packet["b"]["box"], "packet.b.box"),
        )


def submit_packet(mmio: MMIOWriter, packet: YoloxRtlPacket) -> None:
    """Write payload first and CONTROL last, so hardware never sees a partial bbox."""
    if mmio.read(STATUS) & PENDING:
        raise RuntimeError("RTL mailbox is still pending; wait for video frame consumption")
    mmio.write(FRAME_ID, packet.frame)
    mmio.write(A_X, pack_pair(packet.a_box[0], packet.a_box[2]))
    mmio.write(A_Y, pack_pair(packet.a_box[1], packet.a_box[3]))
    mmio.write(B_X, pack_pair(packet.b_box[0], packet.b_box[2]))
    mmio.write(B_Y, pack_pair(packet.b_box[1], packet.b_box[3]))
    mmio.write(CONTROL, PENDING | (PAIR_PRESENT if packet.pair_present else 0))


def submit_json_packet(mmio: MMIOWriter, packet: dict[str, Any]) -> YoloxRtlPacket:
    parsed = YoloxRtlPacket.from_json(packet)
    submit_packet(mmio, parsed)
    return parsed


def load_packets(path: str | Path) -> list[YoloxRtlPacket]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("format") != "rtl-yolox-bbox-v1":
        raise ValueError("not an rtl-yolox-bbox-v1 packet file")
    return [YoloxRtlPacket.from_json(packet) for packet in data.get("packets", [])]


def open_pynq_mmio(base_address: int, length: int = 0x1000) -> MMIOWriter:
    """Create the real PYNQ MMIO object; call only after loading the overlay."""
    from pynq import MMIO  # installed only on the PYNQ-ZU image
    return MMIO(base_address, length)


def pack_dual_rgb888_frames(frame_a: Any, frame_b: Any):
    """Return little-endian uint64 words for ``axis_dual_rgb_stream_adapter``.

    Inputs must already be RGB (not OpenCV BGR), H×W×3 arrays with matching
    shapes.  Each word uses A RGB in bits 23:0 and B RGB in bits 55:32.
    ``axis_dual_rgb_stream_adapter`` treats every 640×480 words as one frame.
    """
    import numpy as np

    a = np.asarray(frame_a)
    b = np.asarray(frame_b)
    if a.shape != b.shape or a.ndim != 3 or a.shape[2] != 3:
        raise ValueError("frame_a and frame_b must be matching HxWx3 RGB arrays")
    if a.dtype != np.uint8 or b.dtype != np.uint8:
        raise ValueError("RGB frame arrays must have dtype uint8")
    a64 = a.astype(np.uint64)
    b64 = b.astype(np.uint64)
    words = ((a64[..., 0] << 16) | (a64[..., 1] << 8) | a64[..., 2] |
             (b64[..., 0] << 48) | (b64[..., 1] << 40) | (b64[..., 2] << 32))
    return words.reshape(-1)


def copy_dual_frame_to_dma_buffer(buffer: Any, frame_a: Any, frame_b: Any) -> int:
    """Pack two RGB frames into a PYNQ allocated uint64 DMA buffer in place."""
    words = pack_dual_rgb888_frames(frame_a, frame_b)
    if getattr(buffer, "dtype", None) is None or buffer.dtype.itemsize != 8:
        raise ValueError("DMA buffer must have an 8-byte element dtype")
    if buffer.size < words.size:
        raise ValueError(f"DMA buffer has {buffer.size} words; requires {words.size}")
    buffer.flat[:words.size] = words
    if hasattr(buffer, "flush"):
        buffer.flush()
    return int(words.size)
