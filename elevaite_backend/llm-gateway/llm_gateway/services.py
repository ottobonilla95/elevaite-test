import logging
from typing import Any, Dict

from .models.provider import ModelProviderFactory
from .models.embeddings.core.base import BaseEmbeddingProvider
from .models.text_generation.core.base import BaseTextGenerationProvider
from .models.embeddings.core.interfaces import (
    EmbeddingRequest,
    EmbeddingResponse,
)


class EmbeddingService:
    """Service class to handle embedding requests."""

    def __init__(self, factory: ModelProviderFactory):
        self.factory = factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        provider = self.factory.get_provider(request.info.type)

        try:
            if isinstance(provider, BaseTextGenerationProvider):
                raise TypeError
            vectors = provider.embed_documents(request.texts, request.info)
            return EmbeddingResponse(vectors=vectors, metadata=request.metadata)
        except Exception as e:
            error_msg = f"Error in embedding for provider {request.info.type}: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)


class TextGenerationService:
    """Service class to handle text generation requests."""

    def __init__(self, factory: ModelProviderFactory):
        self.factory = factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        provider = self.factory.get_provider(config.get("type") or "")

        try:
            if isinstance(provider, BaseEmbeddingProvider):
                raise TypeError
            return provider.generate_text(prompt, config)
        except Exception as e:
            error_msg = (
                f"Error in text generation for provider {config.get('type')}: {str(e)}"
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
