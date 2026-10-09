"""
Vector store wrapper around ChromaDB (M2.2).

ChromaDB is used as a local, embedded vector database — no separate
server process to run, persisted to disk under backend/vector_store/,
which keeps the whole RAG pipeline runnable with nothing more than
`pip install` (unlike a hosted vector DB that needs its own service/account).

We store one vector per *chunk* (see services/chunking.py), with metadata
that lets us map a chunk hit back to its parent job posting and de-duplicate
multiple chunk hits from the same posting into one result.
"""
import os
import shutil
from typing import List, Dict

import chromadb

from app.services.embeddings import embed_texts, embed_text

VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "vector_store_v2")
COLLECTION_NAME = "job_posting_chunks"

_client = None
_collection = None


def _wipe_persisted_vector_store():
    """Remove stale local Chroma state when metadata has become corrupted."""
    global _client, _collection
    if not os.path.exists(VECTOR_STORE_DIR):
        return
    for entry in os.listdir(VECTOR_STORE_DIR):
        full_path = os.path.join(VECTOR_STORE_DIR, entry)
        if os.path.isdir(full_path):
            shutil.rmtree(full_path, ignore_errors=True)
        else:
            try:
                os.remove(full_path)
            except OSError:
                pass
    _client = None
    _collection = None


def _get_collection():
    global _client, _collection
    if _collection is not None:
        return _collection

    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    try:
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    except Exception:
        _wipe_persisted_vector_store()
        client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    _client = client
    _collection = collection
    return _collection


def reset_collection():
    """Drops and recreates the collection — used when re-indexing from scratch."""
    global _client, _collection
    _wipe_persisted_vector_store()
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    _client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def upsert_chunks(chunks: List[Dict]) -> None:
    """
    chunks: list of {chunk_id, job_posting_id, chunk_type, text, title,
    company, location, domain} — embeds `text` and stores the rest as
    metadata (Chroma requires flat, scalar metadata values).
    """
    if not chunks:
        return

    collection = _get_collection()
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)

    collection.upsert(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {
                "job_posting_id": c["job_posting_id"],
                "chunk_type": c["chunk_type"],
                "title": c.get("title", ""),
                "company": c.get("company", ""),
                "location": c.get("location", ""),
                "domain": c.get("domain", ""),
            }
            for c in chunks
        ],
    )


def semantic_search(query_text: str, top_k_jobs: int = 5, fetch_multiplier: int = 4) -> List[Dict]:
    """
    Embeds `query_text`, searches the chunk index, and returns up to
    `top_k_jobs` *unique job postings* (best-matching chunk per job kept),
    ranked by similarity descending.

    fetch_multiplier: how many raw chunk hits to pull before de-duplicating,
    since several chunks from the same job may all rank highly.
    """
    collection = _get_collection()
    query_embedding = embed_text(query_text)

    raw_k = max(top_k_jobs * fetch_multiplier, top_k_jobs)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=raw_k,
    )

    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    best_per_job: Dict[int, Dict] = {}
    for _id, distance, meta in zip(ids, distances, metadatas):
        similarity = 1 - distance  # cosine distance -> similarity
        job_id = meta["job_posting_id"]
        if job_id not in best_per_job or similarity > best_per_job[job_id]["similarity"]:
            best_per_job[job_id] = {
                "job_posting_id": job_id,
                "similarity": round(float(similarity), 4),
                "matched_chunk_type": meta["chunk_type"],
                "title": meta["title"],
                "company": meta["company"],
                "location": meta["location"],
                "domain": meta["domain"],
            }

    ranked = sorted(best_per_job.values(), key=lambda x: x["similarity"], reverse=True)
    return ranked[:top_k_jobs]
