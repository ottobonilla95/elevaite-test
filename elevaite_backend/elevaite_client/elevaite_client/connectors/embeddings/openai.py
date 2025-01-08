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
        self, text: str, embedding_model: str, max_retries: int = 3
    ) -> List[float]:
        for attempt in range(max_retries):
            try:
                logging.info(
                    f"Embedding text: {text[:30]}... using model: {embedding_model}"
                )
                response = self.client.embeddings.create(
                    model=embedding_model, input=text, encoding_format="float"
                )
                logging.info(f"Embedding response: {response}")
                return response.data[0].embedding
            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    raise RuntimeError(
                        f"Embedding failed after {max_retries} attempts: {e}"
                    )
                time.sleep(2**attempt)
        raise Exception("Embedding failed..")

    def validate_config(self, info: EmbeddingInfo) -> bool:
        try:
            assert info.type == EmbeddingType.OPENAI, "Invalid provider type"
            assert info.name, "Model name required"
            return True
        except AssertionError as e:
            logging.error(f"OpenAI Provider Validation Failed: {e}")
            return False
