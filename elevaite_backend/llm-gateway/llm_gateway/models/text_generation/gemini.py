import logging
import time
from typing import Dict, Any
import google.generativeai as genai

from .core.base import BaseTextGenerationProvider


class GeminiTextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.client = genai

    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        model_name = config.get("model", "gemini-1.5-flash")
        temperature = config.get("temperature", 0.7)
        max_output_tokens = config.get("max_tokens", 256)
        retries = config.get("retries", 5)

        model = self.client.GenerativeModel(model_name)

        for attempt in range(retries):
            try:
                response = model.generate_content(
                    prompt,
                    generation_config=self.client.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                    ),
                )

                if hasattr(response, "text") and response.text:
                    return response.text.strip()

                raise ValueError(
                    "Invalid response structure: 'text' attribute missing or empty"
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
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
            assert "model" in config, "Model name is required in config"
            assert isinstance(
                config.get("temperature", 0.7), (float, int)
            ), "Temperature must be a number"
            assert isinstance(
                config.get("max_tokens", 256), int
            ), "Max output tokens must be an integer"
            return True
        except AssertionError as e:
            logging.error(f"Google Gemini Provider Validation Failed: {e}")
            return False
