import sys
from pathlib import Path

from pypdf import PdfReader


def clean(text):
    return " ".join((text or "").split())


def main():
    if len(sys.argv) < 4:
        print("usage: extract_pdf_pages.py <pdf> <start_page> <end_page>")
        raise SystemExit(1)

    path = Path(sys.argv[1])
    start = int(sys.argv[2])
    end = int(sys.argv[3])
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        reader.decrypt("")

    for page_num in range(start, min(end, len(reader.pages)) + 1):
        text = clean(reader.pages[page_num - 1].extract_text())
        print(f"\n--- page {page_num} chars={len(text)} ---")
        print(text[:3500])


if __name__ == "__main__":
    main()
