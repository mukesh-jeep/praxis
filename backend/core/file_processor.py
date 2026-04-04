
import io
import base64
from typing import Any

import fitz  # pymupdf
import docx2txt
from PIL import Image
import numpy as np

# ── PaddleOCR lazy singleton ──────────────────────────────────────────────────

_paddle_ocr: Any = None


def _get_paddle_ocr():
    global _paddle_ocr
    if _paddle_ocr is None:
        from paddleocr import PaddleOCR
        _paddle_ocr = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            show_log=False,         # suppress verbose paddle output
            use_gpu=True,          # set True if CUDA GPU available
        )
    return _paddle_ocr


def _paddle_ocr_page(pix: fitz.Pixmap) -> str:
    """Run PaddleOCR on a rendered PDF page pixmap."""
    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
        pix.height, pix.width, 3
    )
    ocr   = _get_paddle_ocr()
    result = ocr.ocr(img_array, cls=True)

    lines = []
    if result:
        for block in result:
            if block:
                for item in block:
                    # item = [[bbox], [text, confidence]]
                    if item and len(item) >= 2:
                        lines.append(item[1][0])
    return "\n".join(lines)


# ── file type processors ──────────────────────────────────────────────────────

def _process_pdf(file_bytes: bytes) -> dict:
    doc   = fitz.open(stream=file_bytes, filetype="pdf")
    pages = []
    for page in doc:
        text = page.get_text()
        if len(text.strip()) < 50:          # scanned — no usable text layer
            try:
                pix  = page.get_pixmap(dpi=200)
                text = _paddle_ocr_page(pix)
            except Exception as e:
                text = f"[scanned page — OCR failed: {e}]"
        pages.append(text)
    return {"type": "text", "content": "\n\n".join(pages)}


def _process_docx(file_bytes: bytes) -> dict:
    text = docx2txt.process(io.BytesIO(file_bytes))
    return {"type": "text", "content": text or ""}


def _process_image(file_bytes: bytes, mime: str = "image/jpeg") -> dict:
    b64 = base64.b64encode(file_bytes).decode()
    return {"type": "image", "content": b64, "mime": mime}


# ── public API ────────────────────────────────────────────────────────────────

_EXT_TO_MIME = {
    "png":  "image/png",
    "jpg":  "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


def process_uploaded_file(filename: str, file_bytes: bytes) -> dict:
    """
    Returns:
        {"type": "text",  "content": str}                    — for PDF/DOCX
        {"type": "image", "content": base64_str, "mime": str} — for images
    """
    ext = filename.lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        return _process_pdf(file_bytes)

    if ext in ("docx", "doc"):
        return _process_docx(file_bytes)

    if ext in _EXT_TO_MIME:
        return _process_image(file_bytes, _EXT_TO_MIME[ext])

    raise ValueError(f"Unsupported file type: .{ext}")
