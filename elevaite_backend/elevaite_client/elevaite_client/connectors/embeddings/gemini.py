import logging
import time
from typing import List
import google.generativeai as genai

from .core.abstract import BaseEmbeddingProvider
from .core.interfaces import EmbeddingInfo, EmbeddingType


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, api_key: str):
        """
        Initialize the GeminiEmbeddingProvider with the API key.
        Args:
            api_key (str): API key for Gemini embedding service.
        """
        genai.configure(api_key=api_key)

    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo
    ) -> List[List[float]]:
        """
        Embed multiple documents using the Gemini embedding service.
        Args:
            texts (List[str]): Text documents to be embedded.
            info (EmbeddingInfo): Embedding metadata including model information.
        Returns:
            List[List[float]]: A list of embedding vectors for the texts.
        """
        return [self._embed_document(text, info.name) for text in texts]

    def _embed_document(
        self, text: str, embedding_model: str, max_retries: int = 5
    ) -> List[float]:
        """
        Embed a single document with retry logic.
        """
        for attempt in range(max_retries):
            try:
                time.sleep((1 * attempt) + (6 / 1000))
                result = genai.embed_content(model=embedding_model, content=text)
                return result["embedding"]
            except Exception as e:
                logging.warning(
                    f"Retrying embedding for '{text[:30]}...'. Attempt {attempt + 1}. Error: {e}"
                )

        raise RuntimeError(
            f"Failed to embed text after {max_retries} retries: '{text[:30]}...'"
        )

    def validate_config(self, info: EmbeddingInfo) -> bool:
        """
        Validate the embedding configuration for Gemini.
        Args:
            info (EmbeddingInfo): Information about the embedding (type, model).
        Returns:
            bool: Whether the configuration is valid.
        """
        try:
            assert info.type == EmbeddingType.GEMINI, "Invalid provider type for Gemini"
            assert info.name is not None, "Model name required for Gemini embeddings"

            # Test embedding to ensure connectivity
            test_embedding = self._embed_document("Test connectivity", info.name)
            assert (
                len(test_embedding) > 0
            ), "Embedding generation failed during validation"

            return True
        except AssertionError as e:
            logging.error(f"Gemini Provider Validation Failed: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during Gemini validation: {e}")
            return False
