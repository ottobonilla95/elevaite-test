import logging
import time
from typing import Dict, Any, Optional
import google.generativeai as genai

from .core.base import BaseTextGenerationProvider
from .core.interfaces import TextGenerationResponse


class GeminiTextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.client = genai

    def generate_text(
        self,
        model_name: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        sys_msg: Optional[str],
        prompt: Optional[str],
        retries: Optional[int],
        config: Optional[Dict[str, Any]],
    ) -> TextGenerationResponse:
        model_name = model_name or "gemini-1.5-flash"
        temperature = temperature or 0.5
        max_tokens = max_tokens or 100
        sys_msg = sys_msg or ""
        prompt = prompt or ""
        retries = retries or 5
        config = config or {}

        model = self.client.GenerativeModel(
            model_name=model_name, system_instruction=sys_msg
        )

        for attempt in range(retries):
            try:
                start_time = time.time()
                response = model.generate_content(
                    prompt,
                    generation_config=self.client.GenerationConfig(
                        temperature=temperature,
                        max_output_tokens=max_tokens,
                    ),
                )
                latency = time.time() - start_time

                if hasattr(response, "text") and response.text:
                    # Retrieve token counts from the Gemini API if available
                    tokens_in = getattr(response, "input_tokens", len(prompt.split()))
                    tokens_out = getattr(
                        response, "output_tokens", len(response.text.split())
                    )

                    return TextGenerationResponse(
                        text=response.text.strip(),
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        latency=latency,
                    )

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

        raise Exception

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
