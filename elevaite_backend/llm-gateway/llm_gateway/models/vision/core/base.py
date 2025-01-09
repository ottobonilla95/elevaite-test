from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union


class BaseVisionProvider(ABC):
    @abstractmethod
    def generate_text(
        self, prompt: str, images: List[Union[bytes, str]], config: Dict[str, Any]
    ) -> str:
        """
        Abstract method to generate text from a given prompt and image.
        :param prompt: The input text prompt.
        :param images: The input image(s).
        :param config: Configuration options like model name, temperature, etc.
        :return: The generated text as a string.
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
