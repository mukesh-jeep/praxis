"""
Cross-encoder reranker — BAAI/bge-reranker-large.

Why BGE reranker:
  - Cross-encoder architecture: scores each (query, chunk) pair jointly, so it
    understands relevance far better than bi-encoder cosine similarity alone.
  - bge-reranker-large is the best open-source reranker as of 2025 benchmarks
    (BEIR, MS-MARCO) and works very well on domain-specific text like medical.

Pipeline position:
    [Qdrant retrieval: top-10 chunks]  →  [Reranker]  →  [LLM: top-4 chunks]

This two-stage approach means:
  - Qdrant fast-retrieves a wide candidate set (recall ↑)
  - Reranker picks the most relevant from that set (precision ↑)
"""

from typing import List, Tuple
from sentence_transformers import CrossEncoder

RERANKER_MODEL = "BAAI/bge-reranker-large"

# ── lazy singleton ────────────────────────────────────────────────────────────

_reranker: CrossEncoder | None = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(RERANKER_MODEL, max_length=512)
    return _reranker


# ── public API ────────────────────────────────────────────────────────────────

def rerank(query: str, chunks: List[str], top_k: int = 4) -> List[str]:
    """
    Score all (query, chunk) pairs and return the top_k by relevance.

    Parameters
    ----------
    query   : the user's question
    chunks  : candidate text chunks from the vector search
    top_k   : how many to return after reranking

    Returns
    -------
    List of chunk strings, sorted best-first, length ≤ top_k.
    """
    if not chunks:
        return []

    reranker = _get_reranker()

    pairs  : List[Tuple[str, str]] = [(query, chunk) for chunk in chunks]
    scores : List[float]           = reranker.predict(pairs).tolist()

    # Sort by score descending, keep top_k
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in ranked[:top_k]]
