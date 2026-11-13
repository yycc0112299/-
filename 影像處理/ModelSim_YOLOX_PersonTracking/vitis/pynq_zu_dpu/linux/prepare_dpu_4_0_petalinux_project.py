#!/usr/bin/env python3
"""Stage the official DPUCZDX8G 4.0 PetaLinux 2022.1 additions.

This intentionally operates on an external PetaLinux project.  It copies the
official kernel DPU compatibility patch/configuration and Vitis AI 2.5 recipes
from AMD's DPUCZDX8G reference tree; neither vendor tree belongs in Git.
"""

from __future__ import annotations

import argparse
import hashlib
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
PROJECT_PYTHON_RUNTIME_PACKAGES = (
    # NumPy/OpenCV and the deployed tracking launcher import standard-library
    # modules (for example json, pathlib and argparse) split out of Python by
    # the PetaLinux 2022.1 package feed.
    "python3-modules",
    "python3-numpy",
    "python3-opencv",
)
PROJECT_XMODEL_PACKAGE = "pynq-yolov8-model"
TARGET_XMODEL_NAME = "yolov8n_b512.xmodel"
PROJECT_RUNTIME_PACKAGE = "pynq-yolov8-runtime"
PROJECT_RUNTIME_TARGET_ROOT = "/opt/pynq-yolov8"
PROJECT_RUNTIME_SOURCE_FILES = (
    Path("person_tracking") / "pipeline.py",
    Path("person_tracking") / "pynq_yolov8_dpu_inference.py",
    Path("person_tracking") / "assets" / "yolov8.py",
    Path("person_tracking") / "assets" / "yolov8_vart.py",
)
USB_CAMERA_KERNEL_CONFIG = (
    "CONFIG_USB_SUPPORT=y",
    "CONFIG_USB=y",
    "CONFIG_USB_DWC3=y",
    "CONFIG_USB_DWC3_DUAL_ROLE=y",
    "CONFIG_USB_DWC3_OF_SIMPLE=y",
    "CONFIG_USB_DWC3_XILINX=y",
    "CONFIG_MEDIA_SUPPORT=y",
    "CONFIG_MEDIA_CAMERA_SUPPORT=y",
    "CONFIG_MEDIA_USB_SUPPORT=y",
    "CONFIG_VIDEO_DEV=y",
    "CONFIG_VIDEO_V4L2=y",
    "CONFIG_USB_VIDEO_CLASS=y",
    "CONFIG_USB_VIDEO_CLASS_INPUT_EVDEV=y",
)


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


def _install_runtime_packages(meta_user: Path, *, include_xmodel: bool = False,
                              include_project_runtime: bool = False) -> None:
    """Make silent PetaLinux image builds include DPU and project Python runtime."""
    image_dir = meta_user / "recipes-core" / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    package_names = RUNTIME_PACKAGE_NAMES + PROJECT_PYTHON_RUNTIME_PACKAGES
    if include_xmodel:
        package_names += (PROJECT_XMODEL_PACKAGE,)
    if include_project_runtime:
        package_names += (PROJECT_RUNTIME_PACKAGE,)
    packages = " ".join(package_names)
    (image_dir / "petalinux-image-minimal.bbappend").write_text(
        f'IMAGE_INSTALL:append = " {packages}"\n', encoding="utf-8"
    )


def hash_file(path: Path) -> str:
    """Return a streaming SHA-256 hash without keeping a model in memory."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stage_xmodel(meta_user: Path, xmodel: Path) -> dict[str, object]:
    """Install the exact compiled model under /opt/models in the target rootfs."""
    xmodel = xmodel.resolve()
    if xmodel.suffix != ".xmodel" or not xmodel.is_file() or xmodel.stat().st_size == 0:
        raise ValueError(f"A nonempty .xmodel is required for target deployment: {xmodel}")
    package_dir = meta_user / "recipes-apps" / PROJECT_XMODEL_PACKAGE
    files_dir = package_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(xmodel, files_dir / TARGET_XMODEL_NAME)
    (package_dir / f"{PROJECT_XMODEL_PACKAGE}.bb").write_text(
        "SUMMARY = \"Compiled original YOLOv8n model for the PYNQ-ZU DPU B512\"\n"
        "LICENSE = \"CLOSED\"\n"
        f'SRC_URI = "file://{TARGET_XMODEL_NAME}"\n'
        "S = \"${WORKDIR}\"\n\n"
        "do_install() {\n"
        "    install -d ${D}/opt/models\n"
        f"    install -m 0644 ${{WORKDIR}}/{TARGET_XMODEL_NAME} "
        f"${{D}}/opt/models/{TARGET_XMODEL_NAME}\n"
        "}\n\n"
        f'FILES:${{PN}} += "/opt/models/{TARGET_XMODEL_NAME}"\n',
        encoding="utf-8",
    )
    return {
        "target_path": f"/opt/models/{TARGET_XMODEL_NAME}",
        "bytes": xmodel.stat().st_size,
        "sha256": hash_file(xmodel),
    }


def _stage_project_runtime(meta_user: Path, runtime_source: Path) -> dict[str, object]:
    """Install only the Python files needed for first-stage DPU person tracking."""
    runtime_source = runtime_source.resolve()
    if not runtime_source.is_dir():
        raise ValueError(f"PYNQ YOLOv8 runtime source is missing: {runtime_source}")
    package_dir = meta_user / "recipes-apps" / PROJECT_RUNTIME_PACKAGE
    files_dir = package_dir / "files"
    source_uris: list[str] = []
    install_lines: list[str] = []
    file_hashes: dict[str, str] = {}
    for relative in PROJECT_RUNTIME_SOURCE_FILES:
        source = runtime_source / relative
        if not source.is_file():
            raise ValueError(f"PYNQ YOLOv8 runtime source is missing: {source}")
        destination = files_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        posix = relative.as_posix()
        source_uris.append(f"file://{posix}")
        target = f"{PROJECT_RUNTIME_TARGET_ROOT}/{posix}"
        install_lines.extend([
            f"    install -d ${{D}}/{Path(target).parent.as_posix().lstrip('/')}",
            f"    install -m 0644 ${{WORKDIR}}/{posix} ${{D}}{target}",
        ])
        file_hashes[posix] = hash_file(source)
    recipe = (
        "SUMMARY = \"PYNQ-ZU original YOLOv8 GraphRunner single-camera tracker\"\n"
        "LICENSE = \"CLOSED\"\n"
        "SRC_URI = \" " + " ".join(source_uris) + "\"\n"
        "S = \"${WORKDIR}\"\n\n"
        "do_install() {\n" + "\n".join(install_lines) + "\n}\n\n"
        f'FILES:${{PN}} += "{PROJECT_RUNTIME_TARGET_ROOT}"\n'
    )
    (package_dir / f"{PROJECT_RUNTIME_PACKAGE}.bb").write_text(recipe, encoding="utf-8")
    return {
        "target_root": PROJECT_RUNTIME_TARGET_ROOT,
        "files": file_hashes,
    }


def _enable_vitis_ai_library_python(meta_user: Path) -> None:
    """Enable Python bindings required by the target GraphRunner integration."""
    recipe = meta_user / "recipes-vitis-ai" / "vitis-ai-library"
    recipe.mkdir(parents=True, exist_ok=True)
    (recipe / "vitis-ai-library_2.5.bbappend").write_text(
        'PACKAGECONFIG:append = " python"\n', encoding="utf-8"
    )


def _enable_usb_camera_kernel(meta_user: Path) -> None:
    """Enable the PS USB host/UVC camera path as built-in kernel support."""
    config = meta_user / "recipes-kernel" / "linux" / "linux-xlnx" / "bsp.cfg"
    current = config.read_text(encoding="utf-8")
    lines = current.splitlines()
    for option in USB_CAMERA_KERNEL_CONFIG:
        if option not in lines:
            lines.append(option)
    config.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def stage_reference(project: Path, official_meta_user: Path,
                    *, xmodel: Path | None = None,
                    runtime_source: Path | None = None) -> dict[str, object]:
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
    _enable_usb_camera_kernel(target_meta_user)
    _append_rootfs_packages(target_meta_user / "conf" / "user-rootfsconfig")
    xmodel_manifest = _stage_xmodel(target_meta_user, xmodel) if xmodel is not None else None
    runtime_manifest = (_stage_project_runtime(target_meta_user, runtime_source)
                        if runtime_source is not None else None)
    _install_runtime_packages(
        target_meta_user,
        include_xmodel=xmodel_manifest is not None,
        include_project_runtime=runtime_manifest is not None,
    )

    manifest: dict[str, object] = {
        "dpu_ip_version": "4.0",
        "vitis_ai_version": "2.5",
        "staged_directories": ["recipes-kernel", "recipes-vitis-ai"],
        "rootfs_packages": list(ROOTFS_PACKAGES),
    }
    if xmodel_manifest is not None:
        manifest["xmodel"] = xmodel_manifest
    if runtime_manifest is not None:
        manifest["runtime"] = runtime_manifest
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
    parser.add_argument("--xmodel", type=Path,
                        help="optional compiled B512 .xmodel to install at /opt/models")
    parser.add_argument("--runtime-source", type=Path,
                        help="optional project root whose minimal GraphRunner tracker runs from the rootfs")
    arguments = parser.parse_args()

    detected = petalinux_version(arguments.petalinux_root / "settings.sh")
    if detected != "2022.1":
        raise SystemExit(
            f"PetaLinux 2022.1 is required for DPU 4.0/Vitis AI 2.5; detected {detected!r}."
        )
    manifest = stage_reference(arguments.project, arguments.official_meta_user,
                               xmodel=arguments.xmodel, runtime_source=arguments.runtime_source)
    print(f"PYNQ_ZU_DPU_PETALINUX_STAGE_PASS={arguments.project.resolve()}")
    print(json.dumps(manifest, sort_keys=True))


if __name__ == "__main__":
    main()
