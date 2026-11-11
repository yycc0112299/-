"""Read-only dependency and asset check for a PYNQ-ZU dashboard deployment."""
from __future__ import annotations

import importlib
import platform
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "person_tracking" / "assets" / "yolov8n.onnx"


def require(module: str) -> None:
    try:
        loaded = importlib.import_module(module)
    except Exception as error:
        raise RuntimeError(f"Required Python module '{module}' is unavailable: {error}") from error
    version = getattr(loaded, "__version__", "unknown")
    print(f"PYNQ_MODULE_PASS name={module} version={version}")


def main() -> None:
    print(f"PYNQ_PYTHON={sys.version.split()[0]}")
    print(f"PYNQ_PLATFORM={platform.platform()}")
    for module in ("numpy", "cv2", "onnxruntime"):
        require(module)
    if not MODEL.is_file() or MODEL.stat().st_size == 0:
        raise RuntimeError(f"Required YOLOX model is missing or empty: {MODEL}")
    print(f"PYNQ_MODEL_PASS bytes={MODEL.stat().st_size}")
    try:
        require("pynq")
    except RuntimeError as error:
        print(f"PYNQ_OVERLAY_NOTE={error}")
    print("PYNQ_SYSTEM_PREFLIGHT_PASS")


if __name__ == "__main__":
    main()
