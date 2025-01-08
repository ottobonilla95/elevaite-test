import logging
import time
from typing import Dict, Any
import openai

from .core.abstract import BaseTextGenerationProvider


class OpenAITextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, api_key: str):
        """
        Initializes the OpenAI text generation provider.
        :param api_key: OpenAI API key.
        """
        openai.api_key = api_key
        self.client = openai

    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        """
        Generates text using the OpenAI API.
        :param prompt: The input text prompt.
        :param config: Configuration options (e.g., model, temperature, max_tokens).
        :return: Generated text as a string.
        """
        model = config.get("model", "text-davinci-003")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 256)
        retries = config.get("retries", 5)

        for attempt in range(retries):
            try:
                response = self.client.completions.create(
                    model=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                response_dict = dict(
                    response
                )  # Safeguard against unexpected structures

                if "choices" in response_dict and len(response_dict["choices"]) > 0:
                    return response_dict["choices"][0]["text"].strip()

                raise ValueError(
                    "Invalid response structure: 'choices' key missing or empty"
                )

            except Exception as e:
                logging.warning(
                    f"Attempt {attempt + 1}/{retries} failed: {e}. Retrying..."
                )
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Text generation failed after {retries} attempts: {e}"
                    )
                time.sleep((2**attempt) * 0.5)
        return ""

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validates the configuration for OpenAI text generation.
        :param config: Configuration options (e.g., model, temperature, max_tokens).
        :return: True if configuration is valid, False otherwise.
        """
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
            assert "model" in config, "Model name is required in config"
            assert isinstance(config.get("model"), str), "Model name must be a string"
            assert isinstance(
                config.get("temperature", 0.7), (float, int)
            ), "Temperature must be a number"
            assert isinstance(
                config.get("max_tokens", 256), int
            ), "Max tokens must be an integer"
            return True
        except AssertionError as e:
            logging.error(f"OpenAI Provider Validation Failed: {e}")
            return False
