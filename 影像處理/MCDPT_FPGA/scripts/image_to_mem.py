#!/usr/bin/env python3
"""Convert an image to a 160x120, 4-bit grayscale COE file (offline only)."""
import argparse
from pathlib import Path
from PIL import Image

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    im = Image.open(args.image).convert("L").resize((160, 120))
    values = [f"{p >> 4:X}" for p in im.getdata()]
    args.output.write_text("memory_initialization_radix=16;\nmemory_initialization_vector=\n" + ",\n".join(values) + ";\n", encoding="ascii")

if __name__ == "__main__":
    main()
