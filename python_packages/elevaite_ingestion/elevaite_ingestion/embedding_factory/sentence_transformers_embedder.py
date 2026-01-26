from typing import List, Optional

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover
    SentenceTransformer = None  # type: ignore


_model_cache = {}


def _get_model(model_name: str):
    if model_name in _model_cache:
        return _model_cache[model_name]
    if SentenceTransformer is None:
        raise ImportError(
            "sentence_transformers is not installed. Install sentence-transformers to use local embeddings."
        )
    m = SentenceTransformer(model_name)
    _model_cache[model_name] = m
    return m


def get_embedding(text: str, model: Optional[str] = None) -> List[float]:
    """Generate an embedding using a local SentenceTransformer model.

    Defaults to all-MiniLM-L6-v2 if no model provided.
    """
    model_name = model or "all-MiniLM-L6-v2"
    mdl = _get_model(model_name)
    vec = mdl.encode(text)
    return vec.tolist() if hasattr(vec, "tolist") else list(vec)
