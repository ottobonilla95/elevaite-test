import logging
import time
from typing import List

from google import genai

from ...utilities.tokens import count_tokens
from .core.base import BaseEmbeddingProvider
from .core.interfaces import EmbeddingInfo, EmbeddingResponse, EmbeddingType


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo
    ) -> EmbeddingResponse:
        total_tokens = 0
        embeddings = []
        start_time = time.time()

        for text in texts:
            embedding = self._embed_document(text, info.name)
            embeddings.append(embedding)
            total_tokens += count_tokens([text])

        latency = time.time() - start_time
        return EmbeddingResponse(
            latency=latency,
            embeddings=embeddings,
            tokens_in=total_tokens,
        )

    def _embed_document(
        self, text: str, embedding_model: str, max_retries: int = 5
    ) -> List[float]:
        """
        Embed a single document with retry logic.
        """
        for attempt in range(max_retries):
            try:
                time.sleep((1 * attempt) + (6 / 1000))
                result = self.client.models.embed_content(
                    model=embedding_model, content=text
                )
                return result.embedding
            except Exception as e:
                logging.warning(
                    f"Retrying embedding for '{text[:30]}...'. Attempt {attempt + 1}. Error: {e}"
                )

        raise RuntimeError(
            f"Failed to embed text after {max_retries} retries: '{text[:30]}...'"
        )

    def validate_config(self, info: EmbeddingInfo) -> bool:
        try:
            assert info.type == EmbeddingType.GEMINI, "Invalid provider type for Gemini"
            assert info.name is not None, "Model name required for Gemini embeddings"

            # Test embedding to ensure connectivity
            test_embedding = self._embed_document("Test connectivity", info.name)
            assert len(test_embedding) > 0, (
                "Embedding generation failed during validation"
            )

            return True
        except AssertionError as e:
            logging.error(f"Gemini Provider Validation Failed: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during Gemini validation: {e}")
            return False
