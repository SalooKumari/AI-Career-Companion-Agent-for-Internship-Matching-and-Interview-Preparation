"""
Local embedding model wrapper (M2.2).

Uses sentence-transformers (all-MiniLM-L6-v2) instead of a paid embeddings
API — it runs fully offline after the first download, needs no extra API
key, and is more than accurate enough for matching short job-posting/
resume text. This keeps the RAG pipeline self-contained: the only paid API
call in the whole project is the OpenAI call for reasoning/extraction.
"""
from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    return SentenceTransformer(_MODEL_NAME)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts. Returns one embedding vector per text, in order."""
    model = _get_model()
    vectors = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    return vectors.tolist()


def embed_text(text: str) -> List[float]:
    """Embed a single text (e.g. a search query or a student profile summary)."""
    return embed_texts([text])[0]
