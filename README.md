# Praxis — Medical RAG Assistant

> AI-powered clinical assistant for medical students. Ask questions, upload documents or images, and get evidence-based answers grounded in your private knowledge base.

![Next.js](https://img.shields.io/badge/Next.js-16.2-black?logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688?logo=fastapi)
![Qdrant](https://img.shields.io/badge/Qdrant-Cloud-6C63FF?logo=qdrant)
![Groq](https://img.shields.io/badge/LLM-Llama%203.3%2070B-orange)
![Gemini](https://img.shields.io/badge/Vision-Gemini%202.0%20Flash-blue?logo=google)

---

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
                             ↓
               Next.js Frontend (SSE streaming)
```

---

## Project Structure

```
praxis/
├── backend/
│   ├── main.py                  # FastAPI app + CORS + health endpoint
│   ├── routers/
│   │   ├── chat.py              # POST /chat  (streaming SSE, text + optional file)
│   │   └── ingest.py            # POST /ingest (add PDFs to Qdrant)
│   ├── core/
│   │   ├── agent.py             # LangGraph: classify → generate → verify
│   │   ├── context_merger.py    # prompt assembly with token budgets
│   │   ├── file_processor.py    # PDF (pymupdf + PaddleOCR), DOCX, image→base64
│   │   ├── rag.py               # Qdrant retrieval (PubMedBERT embeddings)
│   │   ├── reranker.py          # BGE cross-encoder reranker (top-10 → top-4)
│   │   └── session.py           # in-memory multi-turn chat history per session
│   └── models/
│       └── schemas.py           # Pydantic request/response models
│
├── frontend-next/               # Next.js 16 + React 19 + Tailwind v4
│   ├── app/
│   │   ├── chat/page.tsx        # Main chat page
│   │   ├── api/
│   │   │   ├── chat/route.ts    # Proxy → backend /chat (SSE passthrough)
│   │   │   ├── ingest/route.ts  # Proxy → backend /ingest
│   │   │   └── health/route.ts  # Proxy → backend /health
│   │   └── layout.tsx
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx   # Message list + auto-scroll
│   │   │   ├── ChatInput.tsx    # Textarea, file attach, send (drag-and-drop)
│   │   │   └── MessageBubble.tsx# Markdown renderer with syntax highlighting
│   │   └── sidebar/
│   │       ├── Sidebar.tsx      # Session pill, health dot, new session
│   │       └── IngestPanel.tsx  # Drag-and-drop PDF ingestion UI
│   ├── hooks/
│   │   ├── useChat.ts           # SSE streaming hook + zustand integration
│   │   └── useHealth.ts         # Backend health polling hook
│   ├── store/
│   │   └── chatStore.ts         # Zustand store (messages, sessionId, loading)
│   └── lib/
│       ├── api.ts               # Typed API client
│       └── utils.ts
│
├── frontend/
│   └── app.py                   # Legacy Streamlit UI (superseded by frontend-next)
│
├── ingestion/
│   └── ingest_pipeline.py       # CLI: PDFs → Qdrant (Docling + PaddleOCR)
│
├── eval_medqa.py                # MedQA benchmark evaluation script
├── docker-compose.yml
├── Dockerfile.backend
├── .env.example
└── requirements.txt
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- A free [Qdrant Cloud](https://cloud.qdrant.io) cluster
- A free [Groq](https://console.groq.com) API key
- A free [Google AI Studio](https://aistudio.google.com/app/apikey) key (Gemini)

### 1. Clone & configure

```bash
git clone <repo-url>
cd praxis
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Edit `.env` and fill in your keys:

```env
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...
QDRANT_URL=https://<cluster>.qdrant.io
QDRANT_API_KEY=<your-qdrant-key>
```

---

### Option A — Docker *(recommended)*

```bash
docker compose up --build

# Backend  → http://localhost:8000/docs
# Frontend → http://localhost:3000
```

> **First start downloads model weights** (~2 GB total) into named Docker volumes — cached permanently after that.

```bash
docker compose up -d          # background
docker compose logs -f backend
docker compose down
```

---

### Option B — Local (two terminals)

**Terminal 1 — Backend**

```bash
python -m venv venv
venv\Scripts\Activate.ps1     # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend**

```bash
cd frontend-next
npm install
npm run dev
# → http://localhost:3000
```

---

## Ingesting Documents into the Knowledge Base

### Option A — In-app UI *(sidebar)*

Drag and drop PDFs into the **Knowledge Base** panel in the sidebar, then click **Ingest Files**.

### Option B — CLI *(batch, recommended for large sets)*

```bash
# Text PDFs (textbooks, papers)
python ingestion/ingest_pipeline.py --input-dir ./my_pdfs

# Scanned / image-only PDFs (runs PaddleOCR)
python ingestion/ingest_pipeline.py --input-dir ./scanned --use-ocr
```

**First run** downloads model weights automatically (cached after that):

| Model | Size |
|---|---|
| `NeuML/pubmedbert-base-embeddings` | ~400 MB |
| `BAAI/bge-reranker-large` | ~1.2 GB |
| PaddleOCR models | ~500 MB *(on first OCR use)* |

---

## API Reference

All frontend API calls are proxied through Next.js route handlers at `/api/*`.

### `POST /chat`

Streams a response as Server-Sent Events (SSE).

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | Form string | ✓ | The user's question |
| `session_id` | Form string | ✗ | Omit to start a new session |
| `file` | UploadFile | ✗ | PDF, DOCX, PNG, JPG, JPEG, WEBP |

```
data: partial token\n\n
data: [DONE]\n\n
```

> Runtime file uploads are **never stored in Qdrant** — they are injected directly into the prompt context for that query only.

### `POST /ingest`

| Field | Type | Required |
|---|---|---|
| `files` | List[PDF] | ✓ |

```json
{ "ingested": 2, "chunks": 120, "message": "Successfully ingested 2 file(s)" }
```

### `GET /health`

```json
{ "status": "healthy", "latency_ms": 42 }
```

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16.2, React 19, Tailwind CSS v4, Zustand, Radix UI |
| **Backend** | FastAPI, LangGraph, Python 3.10+ |
| **Text LLM** | Groq `llama-3.3-70b-versatile` |
| **Vision LLM** | Google `gemini-2.0-flash` |
| **Embeddings** | `NeuML/pubmedbert-base-embeddings` (768-dim, PubMed-trained) |
| **Reranker** | `BAAI/bge-reranker-large` (cross-encoder) |
| **Vector DB** | Qdrant Cloud (free tier) |
| **PDF ingestion** | Docling + PaddleOCR fallback |
| **Runtime PDF** | PyMuPDF + PaddleOCR |
| **Streaming** | Server-Sent Events (SSE), end-to-end |
| **Session state** | In-memory (backend) + `localStorage` UUID (frontend) |

---

## Notes

- **Session memory** is in-memory only — resets on backend restart. Replace `core/session.py` with a Redis-backed store for production.
- **Qdrant upserts are idempotent** — re-ingesting the same PDF will not create duplicate chunks (deterministic UUID keys).
- **PaddleOCR** runs on CPU by default. Set `use_gpu=True` in `file_processor.py` and `ingest_pipeline.py` if a CUDA GPU is available.
- **Dark mode** is the default theme, togglable via `next-themes`.
- The legacy **Streamlit frontend** (`frontend/app.py`) is preserved but superseded by `frontend-next`.
