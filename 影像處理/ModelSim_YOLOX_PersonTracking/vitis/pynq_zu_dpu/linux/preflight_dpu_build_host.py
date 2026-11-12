#!/usr/bin/env python3
"""Report whether a host can build the matching PYNQ-ZU DPU Linux image.

The DPU IP version is part of the deployment contract: AMD pairs DPUCZDX8G
4.0 with Vitis AI 2.5 / Xilinx 2022.1, and DPUCZDX8G 4.1 with Vitis AI 3.5 /
Xilinx 2023.1.  The check makes no downloads and changes no system
configuration.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


SUPPORTED_CONTRACTS = {
    "4.0": {"vitis_ai": "2.5", "xilinx_tools": "2022.1"},
    "4.1": {"vitis_ai": "3.5", "xilinx_tools": "2023.1"},
}


def evaluate_build_contract(*, commands: dict[str, bool], has_arch_json: bool,
                            dpu_ip_version: str | None,
                            vitis_ai_version: str | None,
                            vivado_version: str | None,
                            petalinux_version: str | None) -> dict[str, object]:
    """Return the explicit build blockers for the DPU Linux-image contract."""
    blockers: list[str] = []
    contract = SUPPORTED_CONTRACTS.get(dpu_ip_version or "")
    if contract is None:
        blockers.append(
            f"Unsupported or unspecified DPUCZDX8G IP version {dpu_ip_version!r}; "
            "supply the exact generated IP version rather than guessing a toolchain."
        )
        compiler_version = "matching"
        tools_version = "matching"
    else:
        compiler_version = contract["vitis_ai"]
        tools_version = contract["xilinx_tools"]
    if not (commands.get("docker") or commands.get("vai_c_xir")):
        blockers.append(
            f"No Vitis AI compiler route: install Docker for the Vitis AI {compiler_version} container or expose vai_c_xir."
        )
    if not commands.get("petalinux-create"):
        blockers.append(
            "PetaLinux is unavailable; a matching boot image and DPU driver cannot be built on this host."
        )
    if not has_arch_json:
        blockers.append(
            "No DPU-generated arch.json was supplied; do not compile YOLOv8 for a guessed fingerprint."
        )
    if contract is not None and vitis_ai_version != compiler_version:
        blockers.append(
            f"DPUCZDX8G {dpu_ip_version} is paired with Vitis AI {compiler_version}; "
            f"provide --vitis-ai-version {compiler_version}."
        )
    if contract is not None and (vivado_version != tools_version or petalinux_version != tools_version):
        blockers.append(
            f"DPUCZDX8G {dpu_ip_version} with Vitis AI {compiler_version} is verified for "
            f"Vivado/PetaLinux {tools_version}, not "
            f"{vivado_version if vivado_version != tools_version else petalinux_version}."
        )
    return {
        "status": "PASS" if not blockers else "FAIL",
        "dpu_ip_version": dpu_ip_version,
        "required_vitis_ai": compiler_version,
        "required_vivado_and_petalinux": tools_version,
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
    parser.add_argument("--dpu-ip-version", required=True,
                        help="exact DPUCZDX8G IP version from component.xml (for example 4.0)")
    parser.add_argument("--vitis-ai-version", help="installed/container Vitis AI release")
    parser.add_argument("--vivado-version", help="Vivado release used to build the DPU hardware")
    parser.add_argument("--petalinux-version", help="PetaLinux release used for the target image")
    arguments = parser.parse_args()
    report = evaluate_build_contract(
        commands=command_availability(),
        has_arch_json=arguments.arch_json is not None and arguments.arch_json.is_file(),
        dpu_ip_version=arguments.dpu_ip_version,
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
