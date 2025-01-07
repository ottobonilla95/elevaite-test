import logging
import time
from typing import Dict, Any
import openai

from .core.abstract import BaseTextGenerationProvider


class OpenAITextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, api_key: str):
        self.client = openai
        self.client.api_key = api_key

    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        """
        Generates text using the OpenAI API.
        :param prompt: The input text prompt.
        :param config: Configuration options (e.g., model, temperature, max_tokens).
        :return: Generated text.
        """
        model = config.get("model", "text-davinci-003")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 256)
        n_retries = config.get("retries", 5)

        for attempt in range(n_retries):
            try:
                response = self.client.Completion.create(
                    model=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response["choices"][0]["text"].strip()
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1} to generate text failed: {e}")
                if attempt == n_retries - 1:
                    raise RuntimeError(
                        f"Text generation failed after {n_retries} attempts: {e}"
                    )
                time.sleep((5 * attempt) + (6 / 1000))  # Exponential backoff

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validates the configuration for OpenAI text generation.
        :param config: Configuration options (e.g., model, temperature, max_tokens).
        :return: True if configuration is valid, False otherwise.
        """
        try:
            assert "model" in config, "Model name is required."
            assert isinstance(
                config.get("temperature", 0.7), (float, int)
            ), "Temperature must be a number."
            assert isinstance(
                config.get("max_tokens", 256), int
            ), "Max tokens must be an integer."
            return True
        except AssertionError as e:
            logging.error(f"OpenAI Provider Validation Failed: {e}")
            return False
