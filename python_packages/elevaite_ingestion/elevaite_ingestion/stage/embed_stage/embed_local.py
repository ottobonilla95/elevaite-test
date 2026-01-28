from typing import List, Optional

# Simple local embedding wrapper that uses the package's embedding factory
# to embed a list of texts. This avoids S3 dependencies and provides a
# thin callable for in-process workflows.


def embed_texts(
    texts: List[str], provider: Optional[str] = None, model: Optional[str] = None
) -> List[List[float]]:
    """Return embeddings for a list of texts.

    Providers supported:
    - openai (default)
    - cohere
    - local (sentence-transformers)
    - bedrock
    """
    prov = (provider or "openai").lower()

    if prov == "openai":
        from elevaite_ingestion.embedding_factory.openai_embedder import get_embedding

        return [get_embedding(t, model=model) for t in texts]

    if prov == "cohere":
        from elevaite_ingestion.embedding_factory.cohere_embedder import get_embedding

        return [get_embedding(t, model=model) for t in texts]

    if prov in ("local", "sentence_transformers", "sentence-transformers"):
        from elevaite_ingestion.embedding_factory.sentence_transformers_embedder import (
            get_embedding,
        )

        return [get_embedding(t, model=model) for t in texts]

    if prov == "bedrock":
        from elevaite_ingestion.embedding_factory.bedrock_embedder import get_embedding

        return [get_embedding(t, model=model) for t in texts]

    raise ValueError(f"Unsupported embedding provider: {provider}")
