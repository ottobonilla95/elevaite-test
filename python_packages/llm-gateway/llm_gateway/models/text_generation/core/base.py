from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Iterable

from .interfaces import TextGenerationResponse


class BaseTextGenerationProvider(ABC):
    @abstractmethod
    def generate_text(
        self,
        model_name: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        sys_msg: Optional[str],
        prompt: Optional[str],
        retries: Optional[int],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        files: Optional[List[str]] = None,
    ) -> TextGenerationResponse:
        """
        Abstract method to generate text based on a given prompt and configuration.

        :param model_name: The name of the model to use for text generation. Defaults to a set selected appropriate model.
        :param temperature: Controls the randomness of the output. A value of 1.0 means standard sampling; lower values make output deterministic. Defaults to 0.5.
        :param max_tokens: The maximum number of tokens in the generated output. Defaults to 100.
        :param sys_msg: A system-level message or instruction to guide text generation. Defaults to blank.
        :param prompt: The user-provided input text prompt. Defaults to blank.
        :param retries: The number of times to retry text generation in case of failure. Defaults to 5.
        :param config: Additional configuration options as a dictionary, e.g., {'role': assistant }. Defaults to {}.
        :param tools: List of tool/function definitions available to the model. Defaults to None.
        :param tool_choice: How the model should choose tools ('auto', 'none', or specific tool name). Defaults to None.
        :param files: List of file paths to upload for file search. Only supported by OpenAI provider. Defaults to None.
        :return: A `TextGenerationResponse` containing:
                 - 'text': The generated text as a string.
                 - 'tokens_in': Number of input tokens.
                 - 'tokens_out': Number of output tokens.
                 - 'latency': The time taken for the response in seconds.
                 - 'tool_calls': List of tool calls made by the model (if any).
                 - 'finish_reason': Reason the model stopped generating ('stop', 'tool_calls', etc.).
        """
        pass

    def stream_text(
        self,
        model_name: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        sys_msg: Optional[str],
        prompt: Optional[str],
        retries: Optional[int],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        files: Optional[List[str]] = None,
    ) -> Iterable[Dict[str, Any]]:
        """Optional streaming interface. Default raises NotImplementedError.
        Yields dict events: {"type": "delta", "text": str} ... and a final
        {"type": "final", "response": TextGenerationResponse.model_dump()}.

        :param files: List of file paths to upload for file search. Only supported by OpenAI provider. Defaults to None.
        """
        raise NotImplementedError("Streaming not implemented for this provider")

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate provider-specific configuration.
        :param config: Configuration options like model name, temperature, etc.
        :return: True if configuration is valid, False otherwise.
        """
        pass
