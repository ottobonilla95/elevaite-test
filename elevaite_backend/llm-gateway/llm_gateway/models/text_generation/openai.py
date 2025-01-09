import logging
import time
from typing import Dict, Any
import openai

from .core.base import BaseTextGenerationProvider


class OpenAITextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.client = openai

    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        model = config.get("model", "gpt-4o")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 256)
        retries = config.get("retries", 5)

        for attempt in range(retries):
            try:
                if model.startswith("gpt-"):
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    return (
                        response.choices[0].message.content.strip()
                        if response.choices[0].message.content
                        else ""
                    )

                else:
                    response = self.client.completions.create(
                        model=model,
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    return response.choices[0].text.strip()

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
