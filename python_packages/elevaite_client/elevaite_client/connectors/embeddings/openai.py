import time
from typing import List

from .interfaces import EmbeddingInfo
from openai import OpenAI


def embed_documents(texts: List[str], info: EmbeddingInfo) -> List[List[float]]:
    result: List[List[float]] = []
    client = OpenAI()
    for text in texts:
        _res = _embed_document(client=client, input=text, embedding_model=info.name)
        result.append(_res)
    return result


def _embed_document(
    client: OpenAI, input: str, embedding_model: str, depth=0
) -> List[float]:
    if depth > 10:
        raise Exception("Too many retries")
    try:
        time.sleep((5 * depth) + (6 / 1000))
        response = client.embeddings.create(input=input, model=embedding_model)
        return response.data[0].embedding
    except Exception as e:
        print(e)
        print(f"Depth: {depth}")
        return _embed_document(client, input, embedding_model, depth=depth + 1)
