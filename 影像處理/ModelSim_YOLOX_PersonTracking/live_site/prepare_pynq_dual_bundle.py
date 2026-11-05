"""Build a self-contained, local deployment tarball for the PYNQ-ZU dashboard.

The script only prepares a file on the development PC.  It never uploads to a
board.  It includes the two-camera web app, Python inference code, and the
locally verified YOLOX model when available.
"""
from __future__ import annotations

import argparse
import tarfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
TRACKING = PROJECT / "person_tracking"
REQUIRED = [
    ROOT / "dual_server.py", ROOT / "dual_index.html", ROOT / "start_pynq_dual.sh",
    ROOT / "pynq_usb_camera_preflight.py",
    TRACKING / "pipeline.py", TRACKING / "cross_camera.py", TRACKING / "dual_camera.py",
    TRACKING / "assets" / "yolox.py", TRACKING / "assets" / "yolox.onnx",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("pynq_dual_dashboard.tar.gz"))
    parser.add_argument("--overlay-dir", type=Path,
                        help="optional directory containing pynq_zu_yolox.bit/.hwh")
    args = parser.parse_args()
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
