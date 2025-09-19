from typing import List

# Simple local embedding wrapper that uses the package's embedding factory
# to embed a list of texts. This avoids S3 dependencies and provides a
# thin callable for in-process workflows.

from elevaite_ingestion.embedding_factory.openai_embedder import get_embedding


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Return embeddings for a list of texts.

    Uses the package's configured OpenAI embedding client under the hood.
    """
    embeddings: List[List[float]] = []
    for t in texts:
        embeddings.append(get_embedding(t))
    return embeddings

