#!/usr/bin/env python3
"""Copy the exact Vivado-generated DPU architecture JSON for Vitis AI.

The compiler must use the fingerprint emitted by the DPU IP instance, never a
board-family example architecture file. This script is host-only and does not
program the FPGA or touch the board.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def export_architecture(source: Path, output: Path) -> str:
    """Validate and copy a generated DPU ``arch.json`` without rewriting it."""
    try:
        document = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read generated architecture JSON: {source}") from error
    fingerprint = document.get("fingerprint") if isinstance(document, dict) else None
    if not isinstance(fingerprint, str) or not fingerprint.startswith("0x") or len(fingerprint) <= 2:
        raise ValueError(f"generated architecture JSON has no valid fingerprint: {source}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"fingerprint": fingerprint}, separators=(",", ":")) + "\n",
                      encoding="utf-8")
    return fingerprint


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-dir", type=Path, required=True,
                        help="PYNQ_ZU_DPU_BUILD_DIR used by the Vivado Tcl scripts")
    parser.add_argument("--output", type=Path, required=True,
                        help="where to write the deployable architecture JSON")
    arguments = parser.parse_args()
    source = (arguments.build_dir / "project" / "pynq_zu_dpu.gen" / "sources_1" /
              "bd" / "pynq_zu_dpu" / "ip" / "pynq_zu_dpu_dpu_czdx8g_0_0" /
              "arch.json")
    fingerprint = export_architecture(source, arguments.output)
    print(f"PYNQ_ZU_DPU_ARCH_JSON_PASS={arguments.output.resolve()}")
    print(f"PYNQ_ZU_DPU_FINGERPRINT={fingerprint}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
