
import os
import uuid
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
)

load_dotenv()

# ── configuration ─────────────────────────────────────────────────────────────

COLLECTION_NAME  = "medical_docs"
EMBEDDING_MODEL  = "NeuML/pubmedbert-base-embeddings"
EMBEDDING_DIM    = 768          # PubMedBERT base output dimension

# ── lazy singletons ───────────────────────────────────────────────────────────

_client: QdrantClient | None = None
_embedder: SentenceTransformer | None = None


def _get_client() -> QdrantClient:
    global _client
    if _client is not None:
        return _client

    url     = os.getenv("QDRANT_URL", "").strip()
    api_key = os.getenv("QDRANT_API_KEY", "").strip()

    if not url:
        raise EnvironmentError(
            "QDRANT_URL is not set. Add it to your .env file.\n"
            "Get a free cluster at https://cloud.qdrant.io"
        )

    _client = QdrantClient(url=url, api_key=api_key or None)
    _ensure_collection(_client)
    return _client


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL)
    return _embedder


def _ensure_collection(client: QdrantClient) -> None:
    """Create the collection if it does not exist yet."""
    existing = {c.name for c in client.get_collections().collections}
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


# ── public API ────────────────────────────────────────────────────────────────

def retrieve_chunks(query: str, top_k: int = 10) -> List[str]:
    client   = _get_client()
    embedder = _get_embedder()

    count = client.count(collection_name=COLLECTION_NAME).count
    if count == 0:
        return []

    query_vector = embedder.encode(query).tolist()

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=min(top_k, count),
        with_payload=True,
    )
    results = response.points

    return [hit.payload.get("text", "") for hit in results if hit.payload]


def add_chunks(texts: List[str], metadatas: List[dict] | None = None) -> None:
    client   = _get_client()
    embedder = _get_embedder()

    if not texts:
        return

    vectors = embedder.encode(texts, show_progress_bar=True).tolist()
    metas   = metadatas or [{}] * len(texts)

    points = []
    for i, (vec, text, meta) in enumerate(zip(vectors, texts, metas)):
        # Deterministic ID: combine source file hash + chunk index
        source = meta.get("source", "unknown")
        chunk_i = meta.get("chunk_index", i)
        point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{source}__{chunk_i}"))
        payload = {**meta, "text": text}
        points.append(PointStruct(id=point_id, vector=vec, payload=payload))

    batch_size = 100
    for i in range(0, len(points), batch_size):
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points[i : i + batch_size]
        )


def collection_count() -> int:
    try:
        return _get_client().count(collection_name=COLLECTION_NAME).count
    except Exception:
        return 0
