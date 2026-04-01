"""
POST /ingest — upload PDFs to the Qdrant knowledge base.
"""

import hashlib
from typing import List

import fitz  # pymupdf
from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.core.rag import add_chunks, collection_count
from backend.models.schemas import IngestResponse

router = APIRouter()

CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100


def _chunk_text(text: str) -> List[str]:
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start : start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c.strip() for c in chunks if c.strip()]


def _pdf_to_text(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    return "\n\n".join(page.get_text() for page in doc)


@router.post("/ingest", response_model=IngestResponse)
async def ingest(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    total_chunks = 0
    ingested = 0

    for upload in files:
        ext = (upload.filename or "").lower().rsplit(".", 1)[-1]
        if ext != "pdf":
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files are supported. Got: {upload.filename}",
            )

        raw    = await upload.read()
        text   = _pdf_to_text(raw)
        chunks = _chunk_text(text)

        if not chunks:
            continue

        file_hash = hashlib.sha256(raw).hexdigest()[:12]
        metas = [
            {"source": upload.filename, "chunk_index": i, "file_hash": file_hash}
            for i in range(len(chunks))
        ]

        add_chunks(chunks, metas)
        total_chunks += len(chunks)
        ingested += 1

    return IngestResponse(
        ingested=ingested,
        chunks=total_chunks,
        message=(
            f"Ingested {ingested} file(s) → {total_chunks} chunks. "
            f"Collection now has {collection_count()} total chunks."
        ),
    )
