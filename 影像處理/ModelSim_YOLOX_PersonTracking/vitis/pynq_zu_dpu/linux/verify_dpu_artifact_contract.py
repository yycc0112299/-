#!/usr/bin/env python3
"""Fingerprint a DPU deployment artifact set before building an SD image.

This is a host-side, read-only integrity record. It proves which local DPU IP
metadata, architecture JSON, bitstream and XSA were selected together; it does
not prove the target Linux image has a driver, VART, or a runnable model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ElementTree


def sha256_file(path: Path) -> str:
    """Hash one required file without loading a bitstream into memory at once."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_artifact_contract(component_xml: Path, arch_json: Path,
                             bitstream: Path, xsa: Path) -> dict[str, object]:
    """Return the exact DPU IP version/fingerprint and file hashes, or errors."""
    errors: list[str] = []
    paths = {
        "component_xml": component_xml,
        "arch_json": arch_json,
        "bitstream": bitstream,
        "xsa": xsa,
    }
    hashes: dict[str, str] = {}
    for label, path in paths.items():
        if not path.is_file():
            errors.append(f"missing required {label}: {path}")
        else:
            hashes[label] = sha256_file(path)

    dpu_ip_version: str | None = None
    fingerprint: str | None = None
    if component_xml.is_file():
        try:
            root = ElementTree.parse(component_xml).getroot()
            names = [element.text for element in root.iter() if element.tag.endswith("name")]
            versions = [element.text for element in root.iter() if element.tag.endswith("version")]
            if "dpuczdx8g" not in names:
                errors.append("component.xml is not a DPUCZDX8G IP component")
            elif not versions or not versions[0]:
                errors.append("component.xml has no DPU IP version")
            else:
                dpu_ip_version = versions[0]
        except (ElementTree.ParseError, OSError) as error:
            errors.append(f"cannot parse component.xml: {type(error).__name__}: {error}")
    if arch_json.is_file():
        try:
            value = json.loads(arch_json.read_text(encoding="utf-8")).get("fingerprint")
            if not isinstance(value, str) or not value.startswith("0x"):
                errors.append("arch.json has no hexadecimal fingerprint")
            else:
                int(value, 16)
                fingerprint = value.lower()
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"cannot parse arch.json: {type(error).__name__}: {error}")
    return {
        "component_xml": str(component_xml),
        "arch_json": str(arch_json),
        "bitstream": str(bitstream),
        "xsa": str(xsa),
        "dpu_ip_version": dpu_ip_version,
        "fingerprint": fingerprint,
        "sha256": hashes,
        "errors": errors,
        "ok": not errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--component-xml", type=Path, required=True)
    parser.add_argument("--arch-json", type=Path, required=True)
    parser.add_argument("--bitstream", type=Path, required=True)
    parser.add_argument("--xsa", type=Path, required=True)
    arguments = parser.parse_args()
    report = verify_artifact_contract(arguments.component_xml, arguments.arch_json,
                                      arguments.bitstream, arguments.xsa)
    print(json.dumps(report, indent=2, sort_keys=True))
    print("PYNQ_ZU_DPU_ARTIFACT_CONTRACT_PASS" if report["ok"]
          else "PYNQ_ZU_DPU_ARTIFACT_CONTRACT_FAIL")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
