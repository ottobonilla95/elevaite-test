import logging
import time
from typing import Dict, Any, Optional
import openai

from .core.base import BaseTextGenerationProvider
from .core.interfaces import TextGenerationResponse


class OpenAITextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.client = openai

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
        model_name = model_name or "gpt-4o"
        temperature = temperature if temperature is not None else 0.5
        max_tokens = max_tokens if max_tokens is not None else 100
        sys_msg = sys_msg or ""
        prompt = prompt or ""
        retries = retries if retries is not None else 5
        config = config or {}
        role = config.get("role", "system")

        for attempt in range(retries):
            tokens_in = -1
            tokens_out = -1
            try:
                start_time = time.time()
                if model_name.startswith("gpt-"):
                    response = self.client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": role, "content": sys_msg},
                            {"role": "user", "content": prompt},
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    latency = time.time() - start_time
                    if response.usage:
                        tokens_in = response.usage.prompt_tokens
                        tokens_out = response.usage.completion_tokens

                    message_content = response.choices[0].message.content or ""
                    return TextGenerationResponse(
                        text=message_content.strip(),
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        latency=latency,
                    )

                else:
                    response = self.client.completions.create(
                        model=model_name,
                        prompt=prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    latency = time.time() - start_time

                    if response.usage:
                        tokens_in = response.usage.prompt_tokens
                        tokens_out = response.usage.completion_tokens

                    return TextGenerationResponse(
                        text=response.choices[0].text.strip(),
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        latency=latency,
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
