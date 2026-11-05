"""Build a self-contained, local deployment tarball for the PYNQ-ZU dashboard.

The script only prepares a file on the development PC.  It never uploads to a
board.  It includes the two-camera web app, Python inference code, and the
locally verified YOLOX model when available.
"""
from __future__ import annotations

import argparse
import hashlib
import tarfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
TRACKING = PROJECT / "person_tracking"
MODEL = TRACKING / "assets" / "yolox.onnx"
MODEL_URL = (
    "https://media.githubusercontent.com/media/opencv/opencv_zoo/main/"
    "models/object_detection_yolox/object_detection_yolox_2022nov.onnx"
)
MODEL_SHA256 = "c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063"
REQUIRED = [
    ROOT / "dual_server.py", ROOT / "dual_index.html", ROOT / "start_pynq_dual.sh",
    ROOT / "pynq_usb_camera_preflight.py", ROOT / "pynq_system_preflight.py",
    TRACKING / "pipeline.py", TRACKING / "cross_camera.py", TRACKING / "dual_camera.py",
    TRACKING / "assets" / "yolox.py", MODEL,
    TRACKING / "verify_pynq_zu_bringup.py",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_model() -> None:
    """Fetch the ignored public model on a newly cloned PC, with integrity check."""
    if MODEL.is_file() and sha256(MODEL) == MODEL_SHA256:
        return
    temporary = MODEL.with_suffix(".onnx.download")
    try:
        print(f"Downloading YOLOX model for deployment: {MODEL_URL}")
        MODEL.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(MODEL_URL, timeout=120) as response, temporary.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        actual = sha256(temporary)
        if actual != MODEL_SHA256:
            raise RuntimeError(f"YOLOX model SHA-256 mismatch: {actual}")
        temporary.replace(MODEL)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("pynq_dual_dashboard.tar.gz"))
    parser.add_argument("--overlay-dir", type=Path,
                        help="optional directory containing pynq_zu_yolox.bit/.hwh")
    args = parser.parse_args()
    ensure_model()
    missing = [path for path in REQUIRED if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing bundle files: " + ", ".join(map(str, missing)))
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        for source in REQUIRED:
            archive.add(source, arcname=source.relative_to(PROJECT))
        if args.overlay_dir is not None:
            overlay_dir = args.overlay_dir.resolve()
            for name in ("pynq_zu_yolox.bit", "pynq_zu_yolox.hwh"):
                source = overlay_dir / name
                if not source.is_file():
                    raise FileNotFoundError(f"Missing overlay artifact: {source}")
                archive.add(source, arcname=Path("overlay") / name)
    print(f"PYNQ_DUAL_BUNDLE={output}")


if __name__ == "__main__":
    main()
