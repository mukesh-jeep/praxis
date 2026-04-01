"""
POST /chat

Pipeline:
  1. Process uploaded file (if any)
  2. Qdrant retrieval  — top 10 candidates
  3. BGE reranker      — narrow to top 4
  4. Context merger    — assemble prompt
  5. LangGraph agent   — Groq (text) or Gemini 2.0 Flash (vision)
"""

import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from backend.core.file_processor import process_uploaded_file
from backend.core.session import get_history, append_turn
from backend.core.rag import retrieve_chunks
from backend.core.reranker import rerank
from backend.core.context_merger import build_messages
from backend.core.agent import run_agent
from backend.models.schemas import ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    query: str = Form(...),
    session_id: str = Form(default=""),
    file: UploadFile = File(default=None),
):
    # ── session ────────────────────────────────────────────────────────────────
    sid = session_id.strip() or str(uuid.uuid4())

    # ── file processing ────────────────────────────────────────────────────────
    uploaded: dict | None = None
    if file and file.filename:
        try:
            file_bytes = await file.read()
            uploaded = process_uploaded_file(file.filename, file_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # ── RAG: retrieve → rerank ────────────────────────────────────────────────
    # Retrieve 10 candidates, rerank to top 4 for the prompt
    raw_chunks    = retrieve_chunks(query, top_k=10)
    reranked      = rerank(query, raw_chunks, top_k=4)

    # ── build prompt ───────────────────────────────────────────────────────────
    history  = get_history(sid)
    messages = build_messages(history, query, uploaded, reranked)

    # ── agent ──────────────────────────────────────────────────────────────────
    try:
        answer = await run_agent(messages)
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # ── persist turn ───────────────────────────────────────────────────────────
    if uploaded and uploaded["type"] == "image":
        user_content = f"[Image uploaded]\n{query}"
    elif uploaded and uploaded["type"] == "text":
        user_content = f"[Document uploaded]\n{query}"
    else:
        user_content = query

    append_turn(sid, "user", user_content)
    append_turn(sid, "assistant", answer)

    return ChatResponse(session_id=sid, answer=answer)
