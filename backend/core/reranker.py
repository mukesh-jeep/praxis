

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
    if not chunks:
        return []

    reranker = _get_reranker()

    pairs  : List[Tuple[str, str]] = [(query, chunk) for chunk in chunks]
    scores : List[float]           = reranker.predict(pairs).tolist()

    # Sort by score descending, keep top_k
    ranked = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in ranked[:top_k]]
