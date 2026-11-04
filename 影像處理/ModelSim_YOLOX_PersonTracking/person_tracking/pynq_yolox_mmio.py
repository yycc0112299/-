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
