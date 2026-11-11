#!/usr/bin/env python3
"""Verify the Linux prerequisites for the PYNQ-ZU DPU B512 design.

Run this *on the PYNQ-ZU Linux target* after booting a Linux image generated
from the same XSA as the DPU bitstream.  It performs no register writes and
does not program the FPGA, so it is safe to use as a deployment gate.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DPU_COMPATIBLE = "xlnx,dpuczdx8g-4.0"


def dpu_device_tree_nodes(root: Path = Path("/proc/device-tree")) -> list[str]:
    """Return DT node paths whose compatible property contains this DPU."""
    if not root.is_dir():
        return []
    nodes: list[str] = []
    for directory, _, filenames in os.walk(root):
        if "compatible" not in filenames:
            continue
        compatible = Path(directory) / "compatible"
        try:
            values = compatible.read_bytes().decode("ascii", errors="replace").split("\0")
        except OSError:
            continue
        if DPU_COMPATIBLE in values:
            nodes.append(str(Path(directory)))
    return sorted(nodes)


def command_result(command: list[str]) -> dict[str, object]:
    executable = shutil.which(command[0])
    if executable is None:
        return {"available": False, "command": command}
    completed = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, check=False)
    return {
        "available": True,
        "command": command,
        "returncode": completed.returncode,
        "output": completed.stdout[-2000:],
    }


def module_result(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
    except Exception as error:  # ImportError alone hides ABI/linker failures.
        return {"available": False, "error": f"{type(error).__name__}: {error}"}
    return {"available": True, "version": getattr(module, "__version__", None)}


def cma_total_kib() -> int | None:
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("CmaTotal:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        pass
    return None


def valid_xmodel(path: Path | None) -> bool:
    """Return whether an explicitly requested compiled model is nonempty."""
    if path is None or path.suffix != ".xmodel":
        return False
    try:
        return path.is_file() and path.stat().st_size > 0
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xmodel", type=Path,
                        help="require this compiled INT8 .xmodel file to exist")
    parser.add_argument("--require-camera", action="store_true",
                        help="require at least one /dev/video* node")
    arguments = parser.parse_args()

    device_nodes = dpu_device_tree_nodes()
    device_files = sorted(str(path) for path in Path("/dev").glob("dpu*"))
    vart = module_result("vart")
    xir = module_result("xir")
    xdputil = command_result(["xdputil", "query"])
    cameras = sorted(str(path) for path in Path("/dev").glob("video*"))
    model_ok = arguments.xmodel is None or valid_xmodel(arguments.xmodel)
    report = {
        "expected_compatible": DPU_COMPATIBLE,
        "device_tree_nodes": device_nodes,
        "device_files": device_files,
        "cma_total_kib": cma_total_kib(),
        "vart": vart,
        "xir": xir,
        "xdputil": xdputil,
        "camera_nodes": cameras,
        "xmodel": str(arguments.xmodel) if arguments.xmodel else None,
    }
    print(json.dumps(report, indent=2, sort_keys=True))

    required = [
        bool(device_nodes),
        bool(device_files),
        cma_total_kib() not in (None, 0),
        bool(vart["available"]),
        bool(xir["available"]),
        bool(xdputil.get("available")) and xdputil.get("returncode") == 0,
        model_ok,
    ]
    if arguments.require_camera:
        required.append(bool(cameras))
    if all(required):
        print("PYNQ_ZU_DPU_LINUX_RUNTIME_PASS")
        return 0
    print("PYNQ_ZU_DPU_LINUX_RUNTIME_FAIL", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
