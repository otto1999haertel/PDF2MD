"""Convert PDFs to Markdown for RAG, with page markers and quality warnings.

Usage:
    pip install pymupdf4llm
    python pdf_to_markdown.py INPUT_DIR [OUTPUT_DIR] [--recursive] [--overwrite]
"""

import argparse
import sys
from pathlib import Path

import pymupdf4llm

MIN_CHARS_PER_PAGE = 200  # below this average, the PDF is probably scanned or image-only


def convert_pdf(pdf_path: Path, out_path: Path) -> tuple[int, int]:
    """Write Markdown with a <!-- page N --> marker per page. Returns (pages, characters)."""
    pages = pymupdf4llm.to_markdown(str(pdf_path), page_chunks=True)
    parts = [f"---\nsource: {pdf_path.name}\npages: {len(pages)}\n---\n"]
    chars = 0
    for i, page in enumerate(pages, start=1):
        text = page["text"].strip()
        chars += len(text)
        parts.append(f"<!-- page {i} -->\n\n{text}\n")
    out_path.write_text("\n".join(parts), encoding="utf-8")
    return len(pages), chars


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert PDFs to Markdown for RAG.")
    ap.add_argument("input_dir")
    ap.add_argument("output_dir", nargs="?")
    ap.add_argument("--recursive", action="store_true")
    ap.add_argument("--overwrite", action="store_true", help="replace existing .md files")
    args = ap.parse_args()

    in_dir = Path(args.input_dir).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else in_dir
    if not in_dir.is_dir():
        print(f"Input folder not found: {in_dir}", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)

    files = in_dir.rglob("*") if args.recursive else in_dir.iterdir()
    pdfs = sorted(p for p in files if p.is_file() and p.suffix.lower() == ".pdf")
    print(f"Found {len(pdfs)} PDF(s) in {in_dir}")

    failed = warned = skipped = 0
    for pdf in pdfs:
        rel = pdf.relative_to(in_dir).with_suffix(".md")
        out_path = out_dir / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists() and not args.overwrite:
            skipped += 1
            print(f"- {pdf.name}: skipped, {out_path.name} exists (use --overwrite)")
            continue
        try:
            pages, chars = convert_pdf(pdf, out_path)
        except Exception as exc:
            failed += 1
            print(f"x {pdf.name}: {exc}", file=sys.stderr)
            continue
        if pages and chars / pages < MIN_CHARS_PER_PAGE:
            warned += 1
            print(f"! {pdf.name}: only {chars} chars on {pages} page(s), check it (scanned? needs OCR)")
        else:
            print(f"ok {pdf.name} -> {out_path} ({pages} pages)")

    print(f"\nDone: {len(pdfs) - failed - skipped} written, {skipped} skipped, "
          f"{warned} need a look, {failed} failed.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())