"""Read-only dependency and asset check for a PYNQ-ZU dashboard deployment."""
from __future__ import annotations

import argparse
import importlib
import platform
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "person_tracking" / "assets" / "yolov8n.onnx"
DPU_MODEL = Path("/opt/models/yolov8n_b512.xmodel")


def required_modules(*, dpu_runtime: bool) -> tuple[str, ...]:
    """Return only the module set required by the selected inference backend."""
    if dpu_runtime:
        return ("numpy", "cv2", "vart", "xir", "vitis_ai_library")
    return ("numpy", "cv2", "onnxruntime")


def model_path(*, dpu_runtime: bool) -> Path:
    """Keep DPU deployment on the immutable SD-image model path."""
    return DPU_MODEL if dpu_runtime else MODEL


def require(module: str) -> None:
    try:
        loaded = importlib.import_module(module)
    except Exception as error:
        raise RuntimeError(f"Required Python module '{module}' is unavailable: {error}") from error
    version = getattr(loaded, "__version__", "unknown")
    print(f"PYNQ_MODULE_PASS name={module} version={version}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dpu-runtime", action="store_true",
                        help="check GraphRunner and /opt/models instead of CPU ONNX Runtime")
    arguments = parser.parse_args()
    print(f"PYNQ_PYTHON={sys.version.split()[0]}")
    print(f"PYNQ_PLATFORM={platform.platform()}")
    for module in required_modules(dpu_runtime=arguments.dpu_runtime):
        require(module)
    model = model_path(dpu_runtime=arguments.dpu_runtime)
    if not model.is_file() or model.stat().st_size == 0:
        raise RuntimeError(f"Required model is missing or empty: {model}")
    print(f"PYNQ_MODEL_PASS backend={'dpu' if arguments.dpu_runtime else 'onnx'} bytes={model.stat().st_size}")
    try:
        require("pynq")
    except RuntimeError as error:
        print(f"PYNQ_OVERLAY_NOTE={error}")
    print("PYNQ_SYSTEM_PREFLIGHT_PASS")


if __name__ == "__main__":
    main()
