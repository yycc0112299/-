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
import re
import shutil
import subprocess
from pathlib import Path


SUPPORTED_CONTRACTS = {
    "4.0": {
        "vitis_ai": "2.5",
        "xilinx_tools": "2022.1",
        "docker_image": "xilinx/vitis-ai:2.5.0",
    },
    "4.1": {
        "vitis_ai": "3.5",
        "xilinx_tools": "2023.1",
        "docker_image": "xilinx/vitis-ai-pytorch-cpu:ubuntu2004-3.5.0.306",
    },
}


def required_docker_image(dpu_ip_version: str | None) -> str | None:
    """Return the fixed compiler image for a known DPU contract."""
    contract = SUPPORTED_CONTRACTS.get(dpu_ip_version or "")
    return None if contract is None else contract["docker_image"]


def petalinux_version_from_root(root: Path | None) -> str | None:
    """Read the authoritative PetaLinux release exported by settings.sh."""
    if root is None:
        return None
    settings = root / "settings.sh"
    try:
        contents = settings.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(r"^export PETALINUX_VER=([^\s#]+)$", contents, re.MULTILINE)
    return None if match is None else match.group(1)


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
    matching_docker_image = commands.get("matching_docker_image", False)
    if not (commands.get("vai_c_xir") or (commands.get("docker") and matching_docker_image)):
        blockers.append(
            f"No verified Vitis AI compiler route: pull {required_docker_image(dpu_ip_version)!r} "
            f"or expose vai_c_xir for Vitis AI {compiler_version}."
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
    return {name: shutil.which(name) is not None for name in ("docker", "vai_c_xir")}


def docker_image_available(image: str | None) -> bool:
    """Return True only if Docker can inspect the exact local compiler image."""
    if image is None or shutil.which("docker") is None:
        return False
    completed = subprocess.run(
        ["docker", "image", "inspect", image],
        capture_output=True,
        check=False,
        text=True,
    )
    return completed.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arch-json", type=Path,
                        help="DPU IP-generated arch.json for this exact bitstream")
    parser.add_argument("--dpu-ip-version", required=True,
                        help="exact DPUCZDX8G IP version from component.xml (for example 4.0)")
    parser.add_argument("--vitis-ai-version", help="installed/container Vitis AI release")
    parser.add_argument("--vivado-version", help="Vivado release used to build the DPU hardware")
    parser.add_argument("--petalinux-version", help="PetaLinux release used for the target image")
    parser.add_argument("--petalinux-root", type=Path,
                        help="PetaLinux installation root; validates settings.sh and its actual release")
    arguments = parser.parse_args()
    commands = command_availability()
    commands["matching_docker_image"] = docker_image_available(
        required_docker_image(arguments.dpu_ip_version)
    )
    detected_petalinux_version = petalinux_version_from_root(arguments.petalinux_root)
    if arguments.petalinux_root is not None:
        commands["petalinux-create"] = (
            (arguments.petalinux_root / "scripts" / "petalinux-create").is_file()
        )
    else:
        commands["petalinux-create"] = shutil.which("petalinux-create") is not None
    reported_petalinux_version = detected_petalinux_version or arguments.petalinux_version
    report = evaluate_build_contract(
        commands=commands,
        has_arch_json=arguments.arch_json is not None and arguments.arch_json.is_file(),
        dpu_ip_version=arguments.dpu_ip_version,
        vitis_ai_version=arguments.vitis_ai_version,
        vivado_version=arguments.vivado_version,
        petalinux_version=reported_petalinux_version,
    )
    report["petalinux_root"] = None if arguments.petalinux_root is None else str(arguments.petalinux_root)
    report["petalinux_version_from_root"] = detected_petalinux_version
    if (detected_petalinux_version is not None and arguments.petalinux_version is not None
            and arguments.petalinux_version != detected_petalinux_version):
        report["status"] = "FAIL"
        report["blocking_reasons"].append(
            f"PetaLinux root declares {detected_petalinux_version}, not supplied "
            f"{arguments.petalinux_version}."
        )
    print(json.dumps(report, indent=2, sort_keys=True))
    print("PYNQ_ZU_DPU_BUILD_HOST_PASS" if report["status"] == "PASS"
          else "PYNQ_ZU_DPU_BUILD_HOST_FAIL")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
