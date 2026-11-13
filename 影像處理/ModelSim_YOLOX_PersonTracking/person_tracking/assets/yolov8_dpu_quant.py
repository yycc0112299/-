"""Prepare a Vitis-AI-2.5-compatible raw-head YOLOv8n calibration model.

Ultralytics YOLOv8's ``C2f`` blocks use ``torch.split``.  Vitis AI 2.5's
PyTorch quantizer cannot trace that operator in the stock model.  This module
replaces that split with two static channel slices, while retaining the same
C2f calculation and the three raw Detect feature heads required for later DPU
compilation.

Run this only in the Vitis AI 2.5 PyTorch container; the host project's normal
Python environment deliberately does not depend on Torch or Ultralytics.
"""

from __future__ import annotations

import argparse
import hashlib
import types
from pathlib import Path
from typing import Any, Callable


def split_c2f_projection(projected: Any, channels: int) -> tuple[Any, Any]:
    """Return the two C2f channel groups without emitting ``torch.split``."""
    return projected[:, :channels, ...], projected[:, channels:, ...]


def c2f_forward_without_split(block: Any, value: Any, concatenate: Callable[..., Any]) -> Any:
    """Equivalent C2f calculation using static slices and an injected concat."""
    projected = block.cv1(value)
    first, second = split_c2f_projection(projected, block.c)
    values = [first, second]
    values.extend(module(values[-1]) for module in block.m)
    return block.cv2(concatenate(values, 1))


def _torch_c2f_forward(self: Any, value: Any) -> Any:
    import torch

    return c2f_forward_without_split(self, value, torch.cat)


def patch_c2f_modules(model: Any) -> int:
    """Patch every Ultralytics C2f block and return the number patched."""
    count = 0
    for module in model.modules():
        if type(module).__name__ == "C2f":
            module.forward = types.MethodType(_torch_c2f_forward, module)
            count += 1
    if not count:
        raise RuntimeError("no C2f modules found; expected an Ultralytics YOLOv8 model")
    return count


def configure_raw_detect_outputs(model: Any) -> None:
    """Expose raw feature maps while leaving the rest of the model in eval mode."""
    model.eval()
    head = model.model[-1]
    if type(head).__name__ != "Detect":
        raise RuntimeError("expected an Ultralytics YOLOv8 Detect head")
    # Detect.forward returns raw heads when this module's own flag is true.
    # Do not call head.train(), which would also put BatchNorm layers into train mode.
    head.training = True


def replace_silu_modules(model: Any, make_activation: Callable[[], Any], *,
                         silu_type_name: str = "SiLU") -> int:
    """Replace only SiLU modules for separately fine-tuned DPU-ready weights."""
    replacements = 0
    for parent in model.modules():
        for name, child in parent.named_children():
            if type(child).__name__ == silu_type_name:
                setattr(parent, name, make_activation())
                replacements += 1
    return replacements


def export_deploy_artifact(quantizer: Any, quant_mode: str) -> None:
    """Write the artifact appropriate to the completed Vitis AI pass."""
    if quant_mode == "calib":
        quantizer.export_quant_config()
    elif quant_mode == "test":
        quantizer.export_xmodel()
    else:
        raise ValueError(f"unsupported quantization mode: {quant_mode!r}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--weights", type=Path, required=True,
                        help="local official yolov8n.pt weights")
    parser.add_argument("--calib-image", type=Path, required=True,
                        help="one RGB/BGR image used as a 640x640 calibration sample")
    parser.add_argument("--output", type=Path, required=True,
                        help="directory for Vitis AI quantization artifacts")
    parser.add_argument("--quant-mode", choices=("calib", "test"), default="calib")
    parser.add_argument("--activation", choices=("silu", "leakyrelu"), default="silu",
                        help="leakyrelu requires separately fine-tuned LeakyReLU weights")
    args = parser.parse_args()

    try:
        import cv2
        import torch
        from pytorch_nndct.apis import torch_quantizer
        from ultralytics import YOLO
    except ImportError as error:
        raise SystemExit(
            "Run inside xilinx/vitis-ai:2.5.0 with ultralytics==8.0.0 installed."
        ) from error

    if not args.weights.is_file():
        raise SystemExit(f"YOLOv8 weights not found: {args.weights}")
    image = cv2.imread(str(args.calib_image))
    if image is None:
        raise SystemExit(f"calibration image cannot be read: {args.calib_image}")
    image = cv2.resize(image, (640, 640), interpolation=cv2.INTER_LINEAR)
    input_tensor = torch.from_numpy(image[:, :, ::-1].copy()).permute(2, 0, 1).unsqueeze(0)
    input_tensor = input_tensor.float() / 255.0

    network = YOLO(str(args.weights)).model
    patched_count = patch_c2f_modules(network)
    activation_replacements = 0
    if args.activation == "leakyrelu":
        activation_replacements = replace_silu_modules(
            network, lambda: torch.nn.LeakyReLU(negative_slope=0.1015625, inplace=False)
        )
    configure_raw_detect_outputs(network)
    args.output.mkdir(parents=True, exist_ok=True)
    quantizer = torch_quantizer(args.quant_mode, network, (input_tensor,), output_dir=str(args.output))
    quantized = quantizer.quant_model
    with torch.no_grad():
        outputs = quantized(input_tensor)
    if not isinstance(outputs, (list, tuple)) or len(outputs) != 3:
        raise RuntimeError("expected the three raw YOLOv8 Detect feature heads")
    print("YOLOV8_DPU_QUANT_C2F_PATCHED=" + str(patched_count))
    print("YOLOV8_DPU_QUANT_LEAKYRELU_REPLACED=" + str(activation_replacements))
    print("YOLOV8_DPU_QUANT_RAW_HEAD_SHAPES=" + repr([tuple(value.shape) for value in outputs]))
    print("YOLOV8_DPU_QUANT_WEIGHTS_SHA256=" + _sha256(args.weights))
    export_deploy_artifact(quantizer, args.quant_mode)
    if args.quant_mode == "calib":
        print("YOLOV8_DPU_QUANT_CONFIG=" + str(args.output / "quant_info.json"))
    else:
        print("YOLOV8_DPU_XMODEL_EXPORTED=1")


if __name__ == "__main__":
    main()
