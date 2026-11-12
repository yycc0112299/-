#!/usr/bin/env python3
"""Report whether a host can build the matching PYNQ-ZU DPU Linux image.

This check covers the released DPUCZDX8G IP and Vitis AI 3.5 runtime/compiler
contract. Vitis AI 3.5 is verified against the 2023.1 Xilinx tool release. It
makes no downloads and changes no system configuration.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


SUPPORTED_VITIS_AI = "3.5"
SUPPORTED_XILINX_TOOLS = "2023.1"


def evaluate_build_contract(*, commands: dict[str, bool], has_arch_json: bool,
                            vitis_ai_version: str | None,
                            vivado_version: str | None,
                            petalinux_version: str | None) -> dict[str, object]:
    """Return the explicit build blockers for the DPU Linux-image contract."""
    blockers: list[str] = []
    if not (commands.get("docker") or commands.get("vai_c_xir")):
        blockers.append(
            "No Vitis AI compiler route: install Docker for the Vitis AI 3.5 container or expose vai_c_xir."
        )
    if not commands.get("petalinux-create"):
        blockers.append(
            "PetaLinux is unavailable; a matching boot image and DPU driver cannot be built on this host."
        )
    if not has_arch_json:
        blockers.append(
            "No DPU-generated arch.json was supplied; do not compile YOLOv8 for a guessed fingerprint."
        )
    if vitis_ai_version != SUPPORTED_VITIS_AI:
        blockers.append(
            "DPUCZDX8G 4.0 requires the verified Vitis AI 3.5 toolchain; provide --vitis-ai-version 3.5."
        )
    if vivado_version != SUPPORTED_XILINX_TOOLS or petalinux_version != SUPPORTED_XILINX_TOOLS:
        blockers.append(
            "Vitis AI 3.5 and its released DPU IP are verified for Vivado/PetaLinux 2023.1, "
            f"not {vivado_version if vivado_version != SUPPORTED_XILINX_TOOLS else petalinux_version}."
        )
    return {
        "status": "PASS" if not blockers else "FAIL",
        "required_vitis_ai": SUPPORTED_VITIS_AI,
        "required_vivado_and_petalinux": SUPPORTED_XILINX_TOOLS,
        "commands": commands,
        "has_arch_json": has_arch_json,
        "vitis_ai_version": vitis_ai_version,
        "vivado_version": vivado_version,
        "petalinux_version": petalinux_version,
        "blocking_reasons": blockers,
    }


def command_availability() -> dict[str, bool]:
    return {name: shutil.which(name) is not None for name in ("docker", "vai_c_xir", "petalinux-create")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arch-json", type=Path,
                        help="DPU IP-generated arch.json for this exact bitstream")
    parser.add_argument("--vitis-ai-version", help="installed/container Vitis AI release")
    parser.add_argument("--vivado-version", help="Vivado release used to build the DPU hardware")
    parser.add_argument("--petalinux-version", help="PetaLinux release used for the target image")
    arguments = parser.parse_args()
    report = evaluate_build_contract(
        commands=command_availability(),
        has_arch_json=arguments.arch_json is not None and arguments.arch_json.is_file(),
        vitis_ai_version=arguments.vitis_ai_version,
        vivado_version=arguments.vivado_version,
        petalinux_version=arguments.petalinux_version,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    print("PYNQ_ZU_DPU_BUILD_HOST_PASS" if report["status"] == "PASS"
          else "PYNQ_ZU_DPU_BUILD_HOST_FAIL")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
