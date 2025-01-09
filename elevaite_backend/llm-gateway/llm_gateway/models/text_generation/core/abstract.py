from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTextGenerationProvider(ABC):
    @abstractmethod
    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        """
        Abstract method to generate text from a given prompt.
        :param prompt: The input text prompt.
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
