# Medical RAG Assistant

AI-powered medical assistant for students — runtime document upload, multi-turn memory, and ChromaDB-free knowledge retrieval via Qdrant.

## Architecture

```
Runtime Upload (per query)              Knowledge Base (pre-ingested)
        ↓                                           ↓
  File Processor                            RAG Retrieval
(PDF→Docling/PaddleOCR, Image→base64) (query → Qdrant → top-10 chunks)
        ↓                                           ↓
  Session Context Builder               BGE Cross-Encoder Reranker
  (chat history + file content)              (top-10 → top-4)
        ↓                                           ↓
              ┌─────── Context Merger ───────┐
              │  (prompt assembly + budgets) │
              └──────────────┬──────────────┘
                             ↓
                     LangGraph Agent
                  (classify → route → verify)
              ↙                              ↘
    Groq llama-3.3-70b               Gemini 2.0 Flash
       (text / docs)                (image queries)
                             ↓
                     Streamed Response
```

## Project Structure

```
medical-rag/
├── backend/
│   ├── main.py                  # FastAPI app
│   ├── routers/
│   │   ├── chat.py              # POST /chat  (text + optional file)
│   │   └── ingest.py            # POST /ingest (add PDFs to Qdrant)
│   ├── core/
│   │   ├── file_processor.py    # PDF (pymupdf+PaddleOCR), DOCX, image→base64
│   │   ├── session.py           # in-memory chat history per session
│   │   ├── rag.py               # Qdrant retrieval (PubMedBERT embeddings)
│   │   ├── reranker.py          # BGE cross-encoder reranker
│   │   ├── context_merger.py    # assemble final prompt
│   │   └── agent.py             # LangGraph: classify→generate→verify
│   └── models/
│       └── schemas.py
├── frontend/
│   └── app.py                   # Streamlit chat UI
├── ingestion/
│   └── ingest_pipeline.py       # CLI: PDFs → Qdrant (Docling + PaddleOCR)
├── .env.example
└── requirements.txt
```

## Quick Start

### Option A — Docker *(recommended)*

```bash
# 1. Fill in your keys
copy .env.example .env   # then edit .env

# 2. Build and start both services
docker compose up --build

# Backend  → http://localhost:8000/docs
# Frontend → http://localhost:8501
```

> **First start downloads model weights** (~2 GB total) into named Docker volumes — cached permanently after that.

```bash
# Run in background
docker compose up -d

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop
docker compose down
```

---

### Option B — Local (venv)

```bash
python -m venv venv
venv\Scripts\Activate.ps1      # Windows
pip install -r requirements.txt
copy .env.example .env          # fill in keys
```

**Terminal 1 — backend:**
```bash
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — frontend:**
```bash
streamlit run frontend/app.py
```

---

## Ingesting Documents

### Option A — Streamlit sidebar *(runtime)*
Upload PDFs directly in the UI sidebar → click **Ingest Files**.

### Option B — CLI *(batch, recommended for large sets)*

```bash
# Text PDFs (textbooks, papers)
python ingestion/ingest_pipeline.py --input-dir ./my_pdfs

# Scanned / image-only PDFs
python ingestion/ingest_pipeline.py --input-dir ./scanned --use-ocr
```

**First run** downloads model weights automatically (cached after that):
- `NeuML/pubmedbert-base-embeddings` — ~400 MB
- `BAAI/bge-reranker-large` — ~1.2 GB
- PaddleOCR models — ~500 MB *(on first OCR use)*

---

## API Reference

### `POST /chat`

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | Form string | ✓ | The user's question |
| `session_id` | Form string | ✗ | Omit to start a new session |
| `file` | UploadFile | ✗ | PDF, DOCX, PNG, JPG, JPEG |

```json
{ "session_id": "uuid", "answer": "..." }
```

> Runtime file uploads are **never stored in Qdrant** — they go directly into the prompt.

### `POST /ingest`

| Field | Type | Required |
|---|---|---|
| `files` | List[PDF] | ✓ |

```json
{ "ingested": 2, "chunks": 120, "message": "..." }
```

---

## Technology Stack

| Layer | Tool |
|---|---|
| Text LLM | Groq `llama-3.3-70b-versatile` |
| Vision LLM | Google `gemini-2.0-flash` |
| Embeddings | `NeuML/pubmedbert-base-embeddings` (768-dim, PubMed-trained) |
| Reranker | `BAAI/bge-reranker-large` (cross-encoder) |
| Vector DB | Qdrant Cloud (free tier) |
| PDF ingestion | Docling + PaddleOCR fallback |
| Runtime PDF | pymupdf + PaddleOCR |
| Agent | LangGraph (`classify → generate → verify`) |
| Backend | FastAPI |
| Frontend | Streamlit |

---

## Notes

- **Session memory** is in-memory only — resets on backend restart. Replace `core/session.py` with a Redis-backed store for production.
- **Qdrant upserts are idempotent** — re-ingesting the same PDF will not create duplicate chunks (deterministic UUID keys).
- PaddleOCR runs on CPU by default. Set `use_gpu=True` in `file_processor.py` and `ingest_pipeline.py` if a CUDA GPU is available.
