from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Union


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

    def __init__(self, factory: ModelProviderFactory = ModelProviderFactory()):
        self.factory = factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        provider = self.factory.get_provider(request.info.type)

        try:
            if not isinstance(provider, BaseEmbeddingProvider):
                raise TypeError(f"Provider is not a BaseEmbeddingProvider")
            return provider.embed_documents(request.texts, request.info)
        except Exception as e:
            error_msg = f"Error in embedding for provider {request.info.type}: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)


class TextGenerationService:
    """Service class to handle text generation requests."""

    def __init__(self, factory: ModelProviderFactory = ModelProviderFactory()):
        self.factory = factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate(
        self,
        prompt: str,
        config: Dict[str, Any],
        max_tokens: Optional[int] = None,
        model_name: Optional[str] = None,
        sys_msg: Optional[str] = None,
        retries: Optional[int] = None,
        temperature: Optional[float] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> TextGenerationResponse:
        provider = self.factory.get_provider(config["type"])

        try:
            if not isinstance(provider, BaseTextGenerationProvider):
                raise TypeError(f"Provider is not a BaseTextGenerationProvider")
            return provider.generate_text(
                prompt=prompt,
                config=config,
                max_tokens=max_tokens,
                model_name=model_name,
                sys_msg=sys_msg,
                retries=retries,
                temperature=temperature,
                tools=tools,
                tool_choice=tool_choice,
            )
        except Exception as e:
            error_msg = (
                f"Error in text generation for provider {config['type']}: {str(e)}"
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)


class VisionService:
    """Service class to handle image-to-text requests."""

    def __init__(self, factory: ModelProviderFactory = ModelProviderFactory()):
        self.factory = factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_images(
        self,
        prompt: str,
        images: List[Union[bytes, str]],
        config: Dict[str, Any],
        max_tokens: Optional[int] = None,
        model_name: Optional[str] = None,
        sys_msg: Optional[str] = None,
        retries: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> TextGenerationResponse:
        """
        Processes images and generates text based on a given prompt and configuration.

        :param prompt: The input text prompt.
        :param images: The input image(s).
        :param config: Configuration options like model name, temperature, etc.
        :param max_tokens: Maximum number of tokens in the generated output.
        :param model_name: The name of the model to use for text generation.
        :param sys_msg: A system-level message or instruction to guide text generation.
        :param retries: Number of retries in case of failure.
        :param temperature: Controls randomness of the output.
        :return: A `TextGenerationResponse` containing the generated text and metadata.
        """
        provider = self.factory.get_provider(config["type"])

        try:
            if not isinstance(provider, BaseVisionProvider):
                raise TypeError(f"Provider is not a BaseVisionProvider")
            return provider.generate_text(
                prompt=prompt,
                images=images,
                config=config,
                max_tokens=max_tokens,
                model_name=model_name,
                sys_msg=sys_msg,
                retries=retries,
                temperature=temperature,
            )
        except Exception as e:
            error_msg = (
                f"Error in processing images for provider {config['type']}: {str(e)}"
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)


class RequestType(str, Enum):
    EMBEDDING = "embedding"
    TEXT_GENERATION = "text_generation"
    VISION = "vision"


class UniversalService:
    """Service class to handle various types of AI operations."""

    def __init__(self):
        self.factory = ModelProviderFactory()
        self.logger = logging.getLogger(self.__class__.__name__)

    def handle_request(self, request_type: RequestType, provider_type, **kwargs) -> Any:
        """
        Handles the incoming request by delegating to the appropriate provider.

        Args:
            request_type (RequestType): Type of the request (e.g., TEXT_GENERATION, EMBEDDING, VISION).
            kwargs: Additional keyword arguments containing the request details.

        Returns:
            Any: The result from the provider.
        """
        provider = self.factory.get_provider(provider_type)

        try:
            if request_type == RequestType.EMBEDDING:
                if not isinstance(provider, BaseEmbeddingProvider):
                    raise TypeError(f"Provider is not a BaseEmbeddingProvider")
                return provider.embed_documents(kwargs["texts"], kwargs["info"])

            elif request_type == RequestType.TEXT_GENERATION:
                if not isinstance(provider, BaseTextGenerationProvider):
                    raise TypeError(f"Provider is not a BaseTextGenerationProvider")
                return provider.generate_text(
                    prompt=kwargs.get("prompt"),
                    config=kwargs.get("config"),
                    max_tokens=kwargs.get("max_tokens"),
                    model_name=kwargs.get("model_name"),
                    sys_msg=kwargs.get("sys_msg"),
                    retries=kwargs.get("retries"),
                    temperature=kwargs.get("temperature"),
                    tools=kwargs.get("tools"),
                    tool_choice=kwargs.get("tool_choice"),
                )

            elif request_type == RequestType.VISION:
                if not isinstance(provider, BaseVisionProvider):
                    raise TypeError(f"Provider is not a BaseVisionProvider")
                return provider.generate_text(
                    prompt=kwargs.get("prompt"),
                    images=kwargs["images"],
                    config=kwargs.get("config"),
                    max_tokens=kwargs.get("max_tokens"),
                    model_name=kwargs.get("model_name"),
                    sys_msg=kwargs.get("sys_msg"),
                    retries=kwargs.get("retries"),
                    temperature=kwargs.get("temperature"),
                )

            else:
                raise ValueError(f"Unsupported request type: {request_type}")

        except Exception as e:
            error_msg = f"Error in handling {request_type.name} request for provider {provider_type}: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
