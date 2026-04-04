
MAX_FILE_CHARS = 6_000   # ~1 500 tokens — safe for Groq flash context
MAX_RAG_CHARS  = 4_000   # top RAG chunks combined
MAX_HISTORY    = 6       # how many full turns (user + assistant pairs) to keep

SYSTEM_PROMPT = (
    "You are a medical assistant. "
    "Answer questions only from the context provided — either the uploaded document "
    "or knowledge-base excerpts. "
    "Always cite your source: use '[Uploaded document]' for files the user attached, "
    "or '[KB-N]' for knowledge-base chunk numbers. "
    "If no relevant context is available, say so explicitly — do not guess or fabricate."
)


def build_messages(
    session_history: list,
    user_query: str,
    uploaded_file: dict | None,
    rag_chunks: list,
) -> list:
    messages: list[dict] = []

    # ── 1. system prompt ──────────────────────────────────────────────────────
    messages.append({"role": "system", "content": SYSTEM_PROMPT})

    # ── 2. RAG context block ──────────────────────────────────────────────────
    if rag_chunks:
        rag_text = "\n\n".join(
            f"[KB-{i + 1}]: {chunk}" for i, chunk in enumerate(rag_chunks)
        )[:MAX_RAG_CHARS]
        messages.append({
            "role": "system",
            "content": f"Relevant knowledge-base excerpts:\n\n{rag_text}",
        })

    # ── 3. recent chat history ────────────────────────────────────────────────
    # keep the last MAX_HISTORY turns (each turn = 1 user + 1 assistant msg)
    recent = session_history[-(MAX_HISTORY * 2):]
    messages.extend(recent)

    # ── 4. current user turn ─────────────────────────────────────────────────
    if uploaded_file is None:
        messages.append({"role": "user", "content": user_query})

    elif uploaded_file["type"] == "text":
        truncated = uploaded_file["content"][:MAX_FILE_CHARS]
        messages.append({
            "role": "user",
            "content": (
                f"[Uploaded document]\n{truncated}\n\n"
                f"Question: {user_query}"
            ),
        })

    elif uploaded_file["type"] == "image":
        mime = uploaded_file.get("mime", "image/jpeg")
        messages.append({
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime};base64,{uploaded_file['content']}"
                    },
                },
                {"type": "text", "text": user_query},
            ],
        })

    return messages
