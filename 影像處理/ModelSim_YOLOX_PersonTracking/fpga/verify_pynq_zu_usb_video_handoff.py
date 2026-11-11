#!/usr/bin/env python3
"""Read-only structural verifier for the PYNQ-ZU USB-video XSA handoff."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ElementTree
import zipfile


EXPECTED_ADDRESSES = {
    "axi_dma_0": "0xA0000000",
    "frame_id_gpio_0": "0xA0010000",
    "yolox_video_rtl_0": "0xA0020000",
}
REQUIRED_ARTIFACTS = (".bit", ".hwh", "sysdef.xml", "psu_init.c")
ARTIFACT_LABELS = {
    ".bit": "bitstream",
    ".hwh": "hardware handoff",
    "sysdef.xml": "system definition",
    "psu_init.c": "PS initialization source",
}


def _find_member(members: list[str], suffix: str) -> str | None:
    return next((member for member in members if member.lower().endswith(suffix.lower())), None)


def _module_addresses(hwh: bytes) -> dict[str, str]:
    root = ElementTree.fromstring(hwh)
    addresses: dict[str, str] = {}
    for module in root.findall(".//MODULE"):
        instance = module.get("INSTANCE")
        if not instance:
            continue
        base = module.find("./PARAMETERS/PARAMETER[@NAME='C_BASEADDR']")
        if base is not None and base.get("VALUE"):
            try:
                addresses[instance] = f"0x{int(base.get('VALUE'), 0):08X}"
            except ValueError:
                addresses[instance] = base.get("VALUE")
    return addresses


def verify_xsa(path: Path) -> dict[str, object]:
    """Return a JSON-serializable structural XSA verification report."""
    errors: list[str] = []
    addresses: dict[str, str] = {}
    members: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.namelist()
            for required in REQUIRED_ARTIFACTS:
                if _find_member(members, required) is None:
                    errors.append(f"XSA is missing required {ARTIFACT_LABELS[required]} artifact")
            hwh_member = _find_member(members, ".hwh")
            if hwh_member is not None:
                addresses = _module_addresses(archive.read(hwh_member))
    except (OSError, zipfile.BadZipFile, ElementTree.ParseError) as error:
        errors.append(f"Cannot read XSA: {type(error).__name__}: {error}")

    for instance, expected in EXPECTED_ADDRESSES.items():
        actual = addresses.get(instance)
        if actual is None:
            errors.append(f"HWH is missing {instance} C_BASEADDR")
        elif actual != expected:
            errors.append(f"{instance} base address is {actual}, expected {expected}")
    return {
        "xsa": str(path),
        "members": sorted(members),
        "addresses": addresses,
        "errors": errors,
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xsa", required=True, type=Path)
    arguments = parser.parse_args()
    report = verify_xsa(arguments.xsa)
    print(json.dumps(report, indent=2, sort_keys=True))
    print("PYNQ_ZU_USB_VIDEO_XSA_PASS" if report["ok"] else "PYNQ_ZU_USB_VIDEO_XSA_FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
