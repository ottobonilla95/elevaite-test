from abc import ABC, abstractmethod
from typing import Dict, Any

from .interfaces import TextGenerationResponse


class BaseTextGenerationProvider(ABC):
    @abstractmethod
    def generate_text(
        self, prompt: str, config: Dict[str, Any]
    ) -> TextGenerationResponse:
        """
        Abstract method to generate text from a given prompt.
        :param prompt: The input text prompt.
        :param config: Configuration options like model name, temperature, etc.
        :return: A `TextGenerationResponse` containing:
                 - 'text': The generated text as a string.
                 - 'tokens_in': Number of input tokens.
                 - 'tokens_out': Number of output tokens.
                 - 'latency': The time taken for the response in seconds.
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate provider-specific configuration.
        :param config: Configuration options like model name, temperature, etc.
        :return: True if configuration is valid, False otherwise.
        """
        pass
