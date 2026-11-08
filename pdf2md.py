"""Convert every PDF in a folder to a Markdown file with the same name.

Usage:
    pip install pymupdf4llm
    python pdf_to_markdown.py                      # uses ~/Downloads, writes next to the PDFs
    python pdf_to_markdown.py INPUT_DIR            # writes next to the PDFs
    python pdf_to_markdown.py INPUT_DIR OUTPUT_DIR # writes into OUTPUT_DIR
"""

import argparse
import sys
from pathlib import Path

import pymupdf4llm


def convert_pdf(pdf_path: Path, output_dir: Path) -> Path:
    """Convert one PDF to Markdown and return the path of the written file."""
    markdown = pymupdf4llm.to_markdown(str(pdf_path))
    md_path = output_dir / f"{pdf_path.stem}.md"
    md_path.write_text(markdown, encoding="utf-8")
    return md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert all PDFs in a folder to Markdown.")
    parser.add_argument(
        "input_dir",
        nargs="?",
        default=str(Path(__file__).resolve().parent),
        help="Folder containing the PDFs (default: ~/Downloads)",
    )
    parser.add_argument(
        "output_dir",
        nargs="?",
        default=None,
        help="Folder for the .md files (default: same as input folder)",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else input_dir

    if not input_dir.is_dir():
        print(f"Input folder not found: {input_dir}", file=sys.stderr)
        return 1
    output_dir.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")
    if not pdfs:
        print(f"No PDF files found in {input_dir}")
        return 0

    print(f"Found {len(pdfs)} PDF(s) in {input_dir}")
    failed = 0
    for pdf in pdfs:
        try:
            md_path = convert_pdf(pdf, output_dir)
            print(f"✓ {pdf.name} → {md_path}")
        except Exception as exc:  # keep going if one file is broken
            failed += 1
            print(f"✗ {pdf.name}: {exc}", file=sys.stderr)

    print(f"\nDone: {len(pdfs) - failed} converted, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())