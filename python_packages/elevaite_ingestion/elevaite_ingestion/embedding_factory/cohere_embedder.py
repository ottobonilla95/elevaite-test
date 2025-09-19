import os
from typing import List

try:
    import cohere
except Exception as e:  # pragma: no cover
    cohere = None  # type: ignore


def get_embedding(text: str, model: str | None = None) -> List[float]:
    """Generate an embedding using Cohere.

    Requires COHERE_API_KEY in the environment and the cohere package installed.
    """
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        raise ValueError("COHERE_API_KEY not found. Please set it in the environment variables.")
    if cohere is None:
        raise ImportError("cohere package is not installed. Please install cohere to use this provider.")

    client = cohere.ClientV2(api_key=api_key) if hasattr(cohere, "ClientV2") else cohere.Client(api_key)
    model_name = model or os.getenv("COHERE_EMBED_MODEL", "embed-english-v3.0")

    try:
        # Cohere v5 SDK (ClientV2)
        if hasattr(client, "embeddings") and hasattr(client.embeddings, "create"):
            resp = client.embeddings.create(model=model_name, input=text)
            # Attempt to support different response shapes
            if hasattr(resp, "embeddings") and len(resp.embeddings) > 0:
                vec = resp.embeddings[0]
                if hasattr(vec, "embedding"):
                    return list(vec.embedding)
                if isinstance(vec, (list, tuple)):
                    return list(vec)
        # Legacy SDK fallback
        if hasattr(client, "embed"):
            resp = client.embed(model=model_name, texts=[text])
            if hasattr(resp, "embeddings"):
                return list(resp.embeddings[0])
            if isinstance(resp, dict) and "embeddings" in resp:
                return list(resp["embeddings"][0])
        raise RuntimeError("Unexpected Cohere embeddings response shape")
    except Exception as e:  # pragma: no cover
        print(f"Cohere embedding error: {e}")
        raise

