
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import chat, ingest

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Preloading models and clients...")
    from backend.core.rag import _get_client, _get_embedder
    from backend.core.reranker import _get_reranker
    from backend.core.agent import _get_groq, _get_gemini

    # Calling the lazy loading functions will instantiate them globally
    _get_client()
    _get_embedder()
    _get_reranker()
    _get_groq()
    _get_gemini()
    print("Finished preloading models.")
    yield

app = FastAPI(
    title="Medical RAG Assistant",
    description=(
        "A medical AI assistant with runtime document upload, "
        "session memory, and ChromaDB-backed knowledge retrieval."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow all origins during development — restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(ingest.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "status": "ok",
        "message": "Medical RAG Assistant API is running. See /docs for endpoints.",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "healthy"}
