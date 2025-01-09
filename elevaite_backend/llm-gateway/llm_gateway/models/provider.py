import logging
import os
from typing import Dict, Union

from . import embeddings
from . import text_generation
from .embeddings.core.abstract import BaseEmbeddingProvider
from .text_generation.core.abstract import BaseTextGenerationProvider
from .text_generation.core.interfaces import TextGenerationType
from .embeddings.core.interfaces import EmbeddingType


class ModelProviderFactory:
    """Factory to initialize and manage providers for various tasks."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.providers: Dict[
            str, Union[BaseEmbeddingProvider, BaseTextGenerationProvider]
        ] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        if openai_api_key := os.getenv("OPENAI_API_KEY"):
            self.providers[EmbeddingType.OPENAI] = (
                embeddings.openai.OpenAIEmbeddingProvider(api_key=openai_api_key)
            )

            self.providers[TextGenerationType.OPENAI] = (
                text_generation.openai.OpenAITextGenerationProvider(
                    api_key=openai_api_key
                )
            )

        if bedrock_region := os.getenv("BEDROCK_REGION"):
            self.providers[EmbeddingType.BEDROCK] = (
                embeddings.bedrock.BedrockEmbeddingProvider(aws_region=bedrock_region)
            )

            # self.providers[TextGenerationType.BEDROCK] = (
            #     text_generation.bedrock.BedrockTextGenerationProvider(aws_region=bedrock_region)
            # )

        if (onprem_user := os.getenv("ONPREM_USER")) and (
            onprem_secret := os.getenv("ONPREM_SECRET")
        ):
            if onprem_endpoint := os.getenv("ONPREM_EMBED_ENDPOINT"):
                self.providers[EmbeddingType.ON_PREM] = (
                    embeddings.onprem.OnPremEmbeddingProvider(
                        api_url=onprem_endpoint, secret=onprem_secret, user=onprem_user
                    )
                )
            if onprem_endpoint := os.getenv("ONPREM_TEXTGEN_ENDPOINT"):
                self.providers[TextGenerationType.ON_PREM] = (
                    text_generation.onprem.OnPremTextGenerationProvider(
                        api_url=onprem_endpoint, secret=onprem_secret, user=onprem_user
                    )
                )

        if gemini_api_key := os.getenv("GEMINI_API_KEY"):
            self.providers[EmbeddingType.GEMINI] = (
                embeddings.gemini.GeminiEmbeddingProvider(api_key=gemini_api_key)
            )

            self.providers[TextGenerationType.GEMINI] = (
                text_generation.gemini.GoogleGeminiTextGenerationProvider(
                    api_key=gemini_api_key
                )
            )

        if not self.providers:
            raise EnvironmentError("No valid providers configured")

    def get_provider(self, task_type: str):
        provider = self.providers.get(task_type)
        if not provider:
            raise ValueError(f"No provider available for type {task_type}")
        if task_type in EmbeddingType.__members__.values():
            if not isinstance(provider, BaseEmbeddingProvider):
                raise TypeError(
                    f"Expected an EmbeddingProvider for {task_type}, got {type(provider)}"
                )
        elif task_type in TextGenerationType.__members__.values():
            if not isinstance(provider, BaseTextGenerationProvider):
                raise TypeError(
                    f"Expected a TextGenerationProvider for {task_type}, got {type(provider)}"
                )
        else:
            raise ValueError(f"Unknown task type: {task_type}")
        return provider
