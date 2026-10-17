"""
Local embedding wrapper (M2.2).

Uses the ONNX build of all-MiniLM-L6-v2 that ships with ChromaDB. Same model
as sentence-transformers, but without torch, so it fits in 512 MB of RAM.
"""
from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = ONNXMiniLM_L6_V2()
    return _model


def embed_texts(texts):
    """Embed a batch of texts. Returns one vector per text, in order."""
    if not texts:
        return []
    vectors = _get_model()(list(texts))
    return [[float(x) for x in v] for v in vectors]


def embed_text(text):
    return embed_texts([text])[0]