from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union

from ...text_generation.core.interfaces import TextGenerationResponse


class BaseVisionProvider(ABC):
    @abstractmethod
    def generate_text(
        self, prompt: str, images: List[Union[bytes, str]], config: Dict[str, Any]
    ) -> TextGenerationResponse:
        """
        Abstract method to generate text from a given prompt and image.
        :param prompt: The input text prompt.
        :param images: The input image(s).
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
