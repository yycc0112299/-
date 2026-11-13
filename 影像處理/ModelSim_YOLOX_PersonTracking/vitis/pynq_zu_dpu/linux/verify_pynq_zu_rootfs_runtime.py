#!/usr/bin/env python3
"""Verify the target Python runtime *inside* a PetaLinux rootfs archive.

This host-side gate deliberately does not execute ARM binaries.  It parses the
Python sources staged for the board, then verifies that their standard-library
and native Python binding imports are present in ``rootfs.tar.gz`` before an SD
card is written.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import tarfile
from pathlib import Path


PYTHON_LIBRARY_PREFIX = "usr/lib/python3.9/"
NATIVE_BINDINGS = {"cv2", "numpy", "vart", "xir", "vitis_ai_library"}
DEPLOYED_RUNTIME_FILES = (
    Path("pipeline.py"),
    Path("appearance_features.py"),
    Path("cross_camera.py"),
    Path("peer_protocol.py"),
    Path("pynq_cross_camera_fusion.py"),
    Path("pynq_yolov8_dpu_inference.py"),
    Path("pynq_yolov8_peer.py"),
    Path("pynq_wifi_peer_preflight.py"),
    Path("assets") / "yolov8.py",
    Path("assets") / "yolov8_vart.py",
)


def runtime_python_sources(source_root: Path) -> list[Path]:
    """Choose the exact four files staged by the PetaLinux runtime recipe.

    Tiny test fixtures and future callers may provide another directory shape;
    in that case checking all its Python files is the least surprising fallback.
    """
    deployed = [source_root / relative for relative in DEPLOYED_RUNTIME_FILES]
    return deployed if all(source.is_file() for source in deployed) else list(source_root.rglob("*.py"))


def imported_module_roots(source_root: Path) -> set[str]:
    """Return top-level imports from all Python sources below ``source_root``."""
    modules: set[str] = set()
    for source in runtime_python_sources(source_root):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.add(node.module.split(".")[0])
    return modules


def local_module_roots(source_root: Path) -> set[str]:
    """Return project-local roots that must not be mistaken for stdlib imports."""
    return {source.stem for source in source_root.rglob("*.py")} | {
        directory.name for directory in source_root.rglob("*") if directory.is_dir()
    }


def archive_members(rootfs: Path) -> set[str]:
    with tarfile.open(rootfs, "r:gz") as archive:
        return {member.name.lstrip("./") for member in archive.getmembers() if member.isfile()}


def _has_stdlib_module(members: set[str], module: str) -> bool:
    return (
        f"{PYTHON_LIBRARY_PREFIX}{module}.py" in members
        or f"{PYTHON_LIBRARY_PREFIX}{module}/__init__.py" in members
    )


def _has_binding(members: set[str], module: str) -> bool:
    package_prefix = f"{PYTHON_LIBRARY_PREFIX}site-packages/{module}"
    return any(member == f"{package_prefix}/__init__.py" or member.startswith(package_prefix + ".")
               or member.startswith(package_prefix + "/") for member in members)


def verify_rootfs_runtime(rootfs: Path, runtime_source: Path) -> dict[str, object]:
    """Return an archive-content report suitable for a no-write SD-image gate."""
    errors: list[str] = []
    if not rootfs.is_file():
        errors.append(f"missing rootfs archive: {rootfs}")
    if not runtime_source.is_dir():
        errors.append(f"missing runtime source directory: {runtime_source}")
    if errors:
        return {"rootfs": str(rootfs), "runtime_source": str(runtime_source),
                "imports": [], "missing": errors, "ok": False}

    members = archive_members(rootfs)
    imports = imported_module_roots(runtime_source)
    local_modules = local_module_roots(runtime_source)
    stdlib = (imports & set(sys.stdlib_module_names)) - set(sys.builtin_module_names)
    stdlib -= local_modules
    bindings = imports & NATIVE_BINDINGS
    missing = [f"stdlib:{module}" for module in sorted(stdlib)
               if not _has_stdlib_module(members, module)]
    missing.extend(f"binding:{module}" for module in sorted(bindings)
                   if not _has_binding(members, module))
    return {
        "rootfs": str(rootfs),
        "runtime_source": str(runtime_source),
        "imports": sorted(imports),
        "required_stdlib": sorted(stdlib),
        "required_bindings": sorted(bindings),
        "missing": missing,
        "ok": not missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rootfs", type=Path, required=True,
                        help="PetaLinux images/linux/rootfs.tar.gz")
    parser.add_argument("--runtime-source", type=Path, required=True,
                        help="directory containing Python sources staged for the target")
    arguments = parser.parse_args()
    report = verify_rootfs_runtime(arguments.rootfs, arguments.runtime_source)
    print(json.dumps(report, indent=2, sort_keys=True))
    print("PYNQ_ZU_ROOTFS_RUNTIME_PASS" if report["ok"]
          else "PYNQ_ZU_ROOTFS_RUNTIME_FAIL", file=sys.stderr if not report["ok"] else sys.stdout)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
