import logging
import time
from typing import List
from openai import OpenAI

from .core.abstract import BaseEmbeddingProvider
from .core.interfaces import EmbeddingInfo, EmbeddingType


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo
    ) -> List[List[float]]:
        return [self._embed_document(text, info.name) for text in texts]

    def _embed_document(
        self, text: str, embedding_model: str, max_retries: int = 10
    ) -> List[float]:
        document = []
        for attempt in range(max_retries):
            try:
                time.sleep((5 * attempt) + (6 / 1000))
                response = self.client.embeddings.create(
                    input=text, model=embedding_model
                )
                document = response.data[0].embedding
            except Exception as e:
                if attempt == max_retries - 1:
                    raise RuntimeError(
                        f"Embedding failed after {max_retries} attempts: {e}"
                    )
        return document

    def validate_config(self, info: EmbeddingInfo) -> bool:
        try:
            assert info.type == EmbeddingType.OPENAI, "Invalid provider type"
            assert info.name is not None, "Model name required"

            # FIXME: Comment out on prod?
            # Test embedding to confirm connectivity
            test_embedding = self._embed_document("Test connectivity", info.name)
            assert len(test_embedding) > 0, "Embedding generation failed"

            return True
        except AssertionError as e:
            logging.error(f"OpenAI Provider Validation Failed: {e}")
            return False
