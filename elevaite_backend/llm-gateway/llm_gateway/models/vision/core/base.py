from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union

from ...text_generation.core.interfaces import TextGenerationResponse


class BaseVisionProvider(ABC):
    @abstractmethod
    def generate_text(
        self,
        model_name: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        sys_msg: Optional[str],
        prompt: Optional[str],
        images: List[Union[bytes, str]],
        retries: Optional[int],
        config: Optional[Dict[str, Any]],
    ) -> TextGenerationResponse:
        """
        Abstract method to generate text from a given prompt and images.

        :param model_name: The name of the model to use for text generation. Defaults to a set selected appropriate model.
        :param temperature: Controls the randomness of the output. A value of 1.0 means standard sampling; lower values make output deterministic. Defaults to 0.5.
        :param max_tokens: The maximum number of tokens in the generated output. Defaults to 100.
        :param sys_msg: A system-level message or instruction to guide text generation. Defaults to blank.
        :param prompt: The user-provided input text prompt. Defaults to blank.
        :param images: The input image(s) for vision processing.
        :param retries: The number of times to retry text generation in case of failure. Defaults to 5.
        :param config: Additional configuration options as a dictionary, e.g., {'role': assistant }. Defaults to {}.
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
