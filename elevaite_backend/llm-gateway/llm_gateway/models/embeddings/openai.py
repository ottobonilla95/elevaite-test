import logging
import time
from typing import Any, Dict, List
from openai import OpenAI

from .core.base import BaseEmbeddingProvider
from .core.interfaces import EmbeddingInfo, EmbeddingResponse, EmbeddingType


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo
    ) -> EmbeddingResponse:
        total_tokens = 0
        embeddings = []
        start_time = time.time()

        for text in texts:
            result = self._embed_document(text, info.name)
            embeddings.append(result["embedding"])
            total_tokens += result["tokens"]

        latency = time.time() - start_time
        return EmbeddingResponse(
            latency=latency,
            embeddings=embeddings,
            tokens_in=total_tokens,
        )

    def _embed_document(
        self, text: str, embedding_model: str, max_retries: int = 3
    ) -> Dict[str, Any]:
        for attempt in range(max_retries):
            try:
                logging.info(
                    f"Embedding text: {text[:30]}... using model: {embedding_model}"
                )
                response = self.client.embeddings.create(
                    model=embedding_model, input=text
                )

                embedding = response.data[0].embedding
                tokens_used = (
                    response.usage.total_tokens if hasattr(response, "usage") else -1
                )

                return {
                    "embedding": embedding,
                    "tokens": tokens_used,
                }
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    raise RuntimeError(
                        f"Embedding failed after {max_retries} attempts: {e}"
                    )
                time.sleep(2**attempt)

        raise Exception("Embedding failed.")

    def validate_config(self, info: EmbeddingInfo) -> bool:
        try:
            assert info.type == EmbeddingType.OPENAI, "Invalid provider type"
            assert info.name, "Model name required"
            return True
        except AssertionError as e:
            logging.error(f"OpenAI Provider Validation Failed: {e}")
            return False
