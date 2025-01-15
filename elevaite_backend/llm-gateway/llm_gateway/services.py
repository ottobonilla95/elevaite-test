import logging
from typing import Any, Dict, List, Union


from .models.provider import ModelProviderFactory
from .models.embeddings.core.base import BaseEmbeddingProvider
from .models.vision.core.base import BaseVisionProvider
from .models.text_generation.core.base import BaseTextGenerationProvider
from .models.text_generation.core.interfaces import TextGenerationResponse
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
            if not isinstance(provider, BaseEmbeddingProvider):
                raise TypeError
            return provider.embed_documents(request.texts, request.info)
        except Exception as e:
            error_msg = f"Error in embedding for provider {request.info.type}: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)


class TextGenerationService:
    """Service class to handle text generation requests."""

    def __init__(self, factory: ModelProviderFactory):
        self.factory = factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_text(
        self, prompt: str, config: Dict[str, Any]
    ) -> TextGenerationResponse:
        provider = self.factory.get_provider(config.get("type") or "")

        try:
            if not isinstance(provider, BaseTextGenerationProvider):
                raise TypeError
            return provider.generate_text(prompt, config)
        except Exception as e:
            error_msg = (
                f"Error in text generation for provider {config.get('type')}: {str(e)}"
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)


class VisionService:
    """Service class to handle image-to-text requests."""

    def __init__(self, factory: ModelProviderFactory):
        self.factory = factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_images(
        self, prompt: str, images: List[Union[bytes, str]], config: Dict[str, Any]
    ) -> TextGenerationResponse:
        provider = self.factory.get_provider(config.get("type") or "")

        try:
            if not isinstance(provider, BaseVisionProvider):
                raise TypeError

            return provider.generate_text(prompt=prompt, images=images, config=config)

        except Exception as e:
            error_msg = f"Error in processing images for provider {config.get('type')}: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
