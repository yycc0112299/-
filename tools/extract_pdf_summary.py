from pathlib import Path

from pypdf import PdfReader


def main():
    pdf_dir = Path("論文的簡報")
    for path in sorted(pdf_dir.glob("*.pdf")):
        print(f"\n=== {path} ===")
        reader = PdfReader(str(path))
        print(f"encrypted={reader.is_encrypted} pages={len(reader.pages)}")
        if reader.is_encrypted:
            try:
                print(f"decrypt={reader.decrypt('')}")
            except Exception as exc:
                print(f"decrypt_error={exc}")
        for page_index in range(min(len(reader.pages), 8)):
            try:
                text = reader.pages[page_index].extract_text() or ""
            except Exception as exc:
                text = f"extract_error={exc}"
            text = " ".join(text.split())
            print(f"--- page {page_index + 1} chars={len(text)}")
            print(text[:1400].encode("utf-8", errors="replace").decode("utf-8"))


if __name__ == "__main__":
    main()
