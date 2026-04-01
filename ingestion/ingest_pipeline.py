"""
Offline ingestion pipeline — Docling (text PDF) + PaddleOCR (scanned) → Qdrant.

Why Docling:
  - IBM research project built for scientific/medical PDFs
  - Handles multi-column layouts, tables, figures, footnotes natively
  - Outputs clean Markdown — preserves structure better than raw pymupdf text
  - Built-in page classification: routes text vs scanned pages automatically

Why PaddleOCR fallback:
  - Docling's internal OCR handles most scanned docs well
  - PaddleOCR here serves as a manual fallback for pages Docling marks as low-confidence

Usage:
    python ingestion/ingest_pipeline.py --input-dir ./my_pdfs [--use-ocr]

    --use-ocr : force PaddleOCR pass on every page regardless of text confidence
               (useful for mixed or fully scanned document sets)
"""

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.core.rag import add_chunks, collection_count

CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100


# ── chunker ───────────────────────────────────────────────────────────────────

def chunk_text(text: str) -> List[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start : start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c.strip() for c in chunks if c.strip()]


# ── Docling extraction ────────────────────────────────────────────────────────

def pdf_to_text_docling(path: Path) -> str:
    """
    Convert a PDF to clean Markdown using Docling.
    Docling internally runs layout analysis + OCR on scanned pages.
    """
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result    = converter.convert(str(path))
    return result.document.export_to_markdown()


# ── PaddleOCR extraction (manual / fallback) ──────────────────────────────────

def pdf_to_text_paddle(path: Path) -> str:
    """
    Convert a PDF page-by-page using PaddleOCR.
    Used when --use-ocr flag is set or as a fallback for fully scanned docs.
    """
    import fitz
    import numpy as np
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False, use_gpu=False)
    doc = fitz.open(str(path))

    pages = []
    for page in doc:
        text = page.get_text()
        if len(text.strip()) < 50:                # scanned page
            pix       = page.get_pixmap(dpi=200)
            img_array = __import__("numpy").frombuffer(
                pix.samples, dtype=__import__("numpy").uint8
            ).reshape(pix.height, pix.width, 3)

            result = ocr.ocr(img_array, cls=True)
            lines  = []
            if result:
                for block in result:
                    if block:
                        for item in block:
                            if item and len(item) >= 2:
                                lines.append(item[1][0])
            text = "\n".join(lines)
        pages.append(text)

    return "\n\n".join(pages)


# ── per-file ingestion ────────────────────────────────────────────────────────

def ingest_file(pdf_path: Path, force_ocr: bool = False) -> int:
    print(f"  Processing: {pdf_path.name}", end="", flush=True)

    raw = pdf_path.read_bytes()

    if force_ocr:
        print(" [PaddleOCR]", end="", flush=True)
        text = pdf_to_text_paddle(pdf_path)
    else:
        print(" [Docling]", end="", flush=True)
        try:
            text = pdf_to_text_docling(pdf_path)
            # If Docling returns very little text the doc may be fully scanned
            if len(text.strip()) < 200:
                print(" → sparse, retrying with PaddleOCR", end="", flush=True)
                text = pdf_to_text_paddle(pdf_path)
        except Exception as e:
            print(f" → Docling error ({e}), fallback to PaddleOCR", end="", flush=True)
            text = pdf_to_text_paddle(pdf_path)

    chunks = chunk_text(text)
    if not chunks:
        print(" ⚠ no text extracted")
        return 0

    file_hash = hashlib.sha256(raw).hexdigest()[:12]
    metas = [
        {"source": pdf_path.name, "chunk_index": i, "file_hash": file_hash}
        for i in range(len(chunks))
    ]

    add_chunks(chunks, metas)
    print(f" ✓ {len(chunks)} chunks")
    return len(chunks)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Ingest PDFs into Qdrant")
    parser.add_argument("--input-dir", required=True,
                        help="Directory containing PDF files")
    parser.add_argument("--use-ocr", action="store_true",
                        help="Force PaddleOCR on every page (for fully scanned sets)")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        print(f"Error: {input_dir} is not a directory.", file=sys.stderr)
        sys.exit(1)

    pdfs = list(input_dir.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in {input_dir}")
        sys.exit(0)

    mode = "PaddleOCR (forced)" if args.use_ocr else "Docling + PaddleOCR fallback"
    print(f"\nIngesting {len(pdfs)} PDF(s) | mode: {mode}\n")

    total = sum(ingest_file(p, force_ocr=args.use_ocr) for p in pdfs)

    print(f"\nDone — {total} chunks stored | collection total: {collection_count()}")


if __name__ == "__main__":
    main()
