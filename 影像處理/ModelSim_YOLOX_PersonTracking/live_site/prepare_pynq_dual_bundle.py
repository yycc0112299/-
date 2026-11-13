"""Build a self-contained, local deployment tarball for the PYNQ-ZU dashboard.

The script only prepares a file on the development PC.  It never uploads to a
board.  It includes the two-camera web app, Python inference code, and the
locally verified YOLOX model when available.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
TRACKING = PROJECT / "person_tracking"
MODEL = TRACKING / "assets" / "yolov8n.onnx"
EXPORTER = TRACKING / "assets" / "prepare_yolov8_onnx.py"

def runtime_sources(*, dpu_runtime: bool = False) -> list[Path]:
    """Return all tracked runtime sources needed by either PYNQ board role."""
    sources = [
        ROOT / "dual_server.py", ROOT / "dual_index.html", ROOT / "start_pynq_dual.sh",
        ROOT / "pynq_usb_camera_preflight.py", ROOT / "pynq_system_preflight.py",
        TRACKING / "pipeline.py", TRACKING / "appearance_features.py",
        TRACKING / "cross_camera.py", TRACKING / "pynq_cross_camera_fusion.py",
        TRACKING / "dual_camera.py",
        TRACKING / "peer_protocol.py", TRACKING / "pynq_yolov8_peer.py",
        TRACKING / "pynq_wifi_peer_preflight.py",
        TRACKING / "pynq_yolov8_dpu_inference.py",
        TRACKING / "assets" / "yolov8.py", TRACKING / "assets" / "yolov8_vart.py",
        TRACKING / "verify_pynq_zu_bringup.py",
        TRACKING / "verify_pynq_zu_usb_video_overlay.py",
    ]
    if not dpu_runtime:
        sources.append(MODEL)
    return sources

def ensure_model() -> None:
    """Build the ignored, pinned YOLOv8 ONNX artifact on a deployment PC."""
    if MODEL.is_file() and MODEL.stat().st_size > 0:
        return
    if not EXPORTER.is_file():
        raise FileNotFoundError(f"Missing YOLOv8 exporter: {EXPORTER}")
    subprocess.run([sys.executable, str(EXPORTER), "--output", str(MODEL)], check=True)
    if not MODEL.is_file() or MODEL.stat().st_size == 0:
        raise RuntimeError(f"YOLOv8 exporter did not create a model: {MODEL}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("pynq_dual_dashboard.tar.gz"))
    parser.add_argument("--overlay-dir", type=Path,
                        help="optional directory containing pynq_zu_yolox.bit/.hwh")
    parser.add_argument("--usb-video-overlay-dir", type=Path,
                        help="optional directory containing pynq_zu_usb_video.bit/.hwh")
    parser.add_argument("--dpu-runtime", action="store_true",
                        help="use /opt/models/yolov8n_b512.xmodel from the DPU SD image")
    args = parser.parse_args()
    if not args.dpu_runtime:
        ensure_model()
    sources = runtime_sources(dpu_runtime=args.dpu_runtime)
    missing = [path for path in sources if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing bundle files: " + ", ".join(map(str, missing)))
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        for source in sources:
            archive.add(source, arcname=source.relative_to(PROJECT))
        if args.overlay_dir is not None:
            overlay_dir = args.overlay_dir.resolve()
            for name in ("pynq_zu_yolox.bit", "pynq_zu_yolox.hwh"):
                source = overlay_dir / name
                if not source.is_file():
                    raise FileNotFoundError(f"Missing overlay artifact: {source}")
                archive.add(source, arcname=Path("overlay") / name)
        if args.usb_video_overlay_dir is not None:
            overlay_dir = args.usb_video_overlay_dir.resolve()
            for name in ("pynq_zu_usb_video.bit", "pynq_zu_usb_video.hwh"):
                source = overlay_dir / name
                if not source.is_file():
                    raise FileNotFoundError(f"Missing USB-video overlay artifact: {source}")
                archive.add(source, arcname=Path("overlay_usb_video") / name)
    print(f"PYNQ_DUAL_BUNDLE={output}")


if __name__ == "__main__":
    main()
