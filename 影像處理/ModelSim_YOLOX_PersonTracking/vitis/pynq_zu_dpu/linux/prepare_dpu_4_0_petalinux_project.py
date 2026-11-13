#!/usr/bin/env python3
"""Stage the official DPUCZDX8G 4.0 PetaLinux 2022.1 additions.

This intentionally operates on an external PetaLinux project.  It copies the
official kernel DPU compatibility patch/configuration and Vitis AI 2.5 recipes
from AMD's DPUCZDX8G reference tree; neither vendor tree belongs in Git.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


ROOTFS_PACKAGES = (
    "CONFIG_vart",
    "CONFIG_xir",
    "CONFIG_unilog",
    "CONFIG_target-factory",
    "CONFIG_vitis-ai-library",
)
RUNTIME_PACKAGE_NAMES = tuple(package.removeprefix("CONFIG_") for package in ROOTFS_PACKAGES)


def _require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise ValueError(f"Official DPU 4.0 reference is missing {description}: {path}")


def _validate_reference(meta_user: Path) -> None:
    kernel = meta_user / "recipes-kernel" / "linux"
    bbappend = kernel / "linux-xlnx_%.bbappend"
    _require_file(bbappend, "the Linux bbappend")
    kernel_files = kernel / "linux-xlnx"
    _require_file(kernel_files / "bsp.cfg", "the DPU kernel config")
    patch_names = re.findall(r"file://([^\"\s]+\.patch)", bbappend.read_text(encoding="utf-8"))
    if len(patch_names) != 1:
        raise ValueError("Official DPU 4.0 reference must declare exactly one driver patch")
    patch = kernel_files / patch_names[0]
    _require_file(patch, "the DPU 4.0 driver patch")
    if "xlnx,dpuczdx8g-4.0" not in patch.read_text(encoding="utf-8"):
        raise ValueError("Official DPU 4.0 reference patch does not support xlnx,dpuczdx8g-4.0")
    if "CONFIG_XILINX_DPU=y" not in (kernel_files / "bsp.cfg").read_text(encoding="utf-8"):
        raise ValueError("Official DPU 4.0 reference does not enable CONFIG_XILINX_DPU")

    recipes = meta_user / "recipes-vitis-ai"
    required_recipes = {
        "vart": "vart_2.5.bb",
        "xir": "xir_2.5.bb",
        "unilog": "unilog_2.5.bb",
        "target-factory": "target-factory_2.5.bb",
        "vitis-ai-library": "vitis-ai-library_2.5.bb",
    }
    for directory, recipe in required_recipes.items():
        _require_file(recipes / directory / recipe, f"Vitis AI recipe {directory}/{recipe}")


def _append_rootfs_packages(rootfs_config: Path) -> None:
    current = rootfs_config.read_text(encoding="utf-8") if rootfs_config.exists() else ""
    lines = current.splitlines()
    normalized = []
    for line in lines:
        if line.endswith("=y") and line[:-2] in ROOTFS_PACKAGES:
            line = line[:-2]
        if line not in normalized:
            normalized.append(line)
    lines = normalized
    existing = set(lines)
    for package in ROOTFS_PACKAGES:
        if package not in existing:
            lines.append(package)
            existing.add(package)
    rootfs_config.parent.mkdir(parents=True, exist_ok=True)
    rootfs_config.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _install_runtime_packages(meta_user: Path) -> None:
    """Make silent PetaLinux image builds include the staged Vitis AI packages."""
    image_dir = meta_user / "recipes-core" / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    packages = " ".join(RUNTIME_PACKAGE_NAMES)
    (image_dir / "petalinux-image-minimal.bbappend").write_text(
        f'IMAGE_INSTALL:append = " {packages}"\n', encoding="utf-8"
    )


def _enable_vitis_ai_library_python(meta_user: Path) -> None:
    """Enable Python bindings required by the target GraphRunner integration."""
    recipe = meta_user / "recipes-vitis-ai" / "vitis-ai-library"
    recipe.mkdir(parents=True, exist_ok=True)
    (recipe / "vitis-ai-library_2.5.bbappend").write_text(
        'PACKAGECONFIG:append = " python"\n', encoding="utf-8"
    )


def stage_reference(project: Path, official_meta_user: Path) -> dict[str, object]:
    """Copy the exact DPU 4.0 runtime additions into one PetaLinux project."""
    project = project.resolve()
    official_meta_user = official_meta_user.resolve()
    target_meta_user = project / "project-spec" / "meta-user"
    if not target_meta_user.is_dir():
        raise ValueError(f"PetaLinux project lacks project-spec/meta-user: {project}")
    _validate_reference(official_meta_user)

    for directory in ("recipes-kernel", "recipes-vitis-ai"):
        shutil.copytree(
            official_meta_user / directory,
            target_meta_user / directory,
            dirs_exist_ok=True,
        )
    _enable_vitis_ai_library_python(target_meta_user)
    _append_rootfs_packages(target_meta_user / "conf" / "user-rootfsconfig")
    _install_runtime_packages(target_meta_user)

    manifest: dict[str, object] = {
        "dpu_ip_version": "4.0",
        "vitis_ai_version": "2.5",
        "staged_directories": ["recipes-kernel", "recipes-vitis-ai"],
        "rootfs_packages": list(ROOTFS_PACKAGES),
    }
    (project / ".pynq_zu_dpu_4_0_stage.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def petalinux_version(settings: Path) -> str | None:
    """Read the installed PetaLinux release from its settings file."""
    if not settings.is_file():
        return None
    for line in settings.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("export PETALINUX_VER="):
            return line.split("=", 1)[1].strip().strip('"')
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True, help="external PetaLinux project root")
    parser.add_argument("--official-meta-user", type=Path, required=True,
                        help="official DPUCZDX8G 4.0 reference project-spec/meta-user")
    parser.add_argument("--petalinux-root", type=Path, required=True,
                        help="PetaLinux 2022.1 installation root")
    arguments = parser.parse_args()

    detected = petalinux_version(arguments.petalinux_root / "settings.sh")
    if detected != "2022.1":
        raise SystemExit(
            f"PetaLinux 2022.1 is required for DPU 4.0/Vitis AI 2.5; detected {detected!r}."
        )
    manifest = stage_reference(arguments.project, arguments.official_meta_user)
    print(f"PYNQ_ZU_DPU_PETALINUX_STAGE_PASS={arguments.project.resolve()}")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
