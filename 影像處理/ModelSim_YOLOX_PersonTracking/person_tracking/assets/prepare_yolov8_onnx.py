"""Export the official YOLOv8n detector to the PYNQ CPU fallback artifact.

Run on a development PC, not on the PYNQ. It requires the pinned exporter
environment used by this project: ``ultralytics==8.3.0``, ``onnx`` and Torch.
The generated model is intentionally ignored by Git; its checksum is printed
for deployment records.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
from pathlib import Path


DEFAULT_OUTPUT = Path(__file__).with_name("yolov8n.onnx")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        import onnx
        from ultralytics import YOLO
    except ImportError as error:
        raise SystemExit(
            "Install ultralytics==8.3.0 and onnx on the development PC before exporting."
        ) from error
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    original = Path.cwd()
    with tempfile.TemporaryDirectory(prefix="pynq_yolov8_export_") as directory:
        workspace = Path(directory)
        os.chdir(workspace)
        try:
            exported = Path(YOLO("yolov8n.pt").export(
                format="onnx", imgsz=640, opset=18, dynamic=False, simplify=False
            )).resolve()
        finally:
            os.chdir(original)
        model = onnx.load(str(exported))
        # PYNQ's verified ONNX Runtime 1.16.3 supports model IR <= 9. The
        # static export graph validates unchanged after this metadata downgrade.
        model.ir_version = 9
        onnx.checker.check_model(model)
        onnx.save(model, str(output))
    checked = onnx.load(str(output))
    print(f"PYNQ_YOLOV8_ONNX={output}")
    print(f"PYNQ_YOLOV8_ONNX_IR={checked.ir_version}")
    print(f"PYNQ_YOLOV8_ONNX_SHA256={sha256(output)}")


if __name__ == "__main__":
    main()
