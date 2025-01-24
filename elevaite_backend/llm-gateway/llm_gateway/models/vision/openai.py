import base64
import logging
import time
from typing import Any, Dict, List, Optional, Union
import openai

from ..text_generation.core.interfaces import TextGenerationResponse
from .core.base import BaseVisionProvider


class OpenAIVisionProvider(BaseVisionProvider):
    def __init__(self, api_key: str):
        openai.api_key = api_key
        self.client = openai

    def generate_text(
        self,
        images: List[Union[bytes, str]],
        model_name: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        sys_msg: Optional[str],
        prompt: Optional[str],
        retries: Optional[int],
        config: Optional[Dict[str, Any]],
    ) -> TextGenerationResponse:
        model_name = model_name or "gpt-4o-mini"
        prompt = prompt or ""
        retries = retries or 5
        max_tokens = max_tokens or 100
        temperature = temperature or 0.5
        config = config or {}
        role = config.get("role", "system")

        message_content = prompt + "\n"
        for i, image in enumerate(images):
            if isinstance(image, bytes):
                base64_image = base64.b64encode(image).decode("utf-8")
                message_content += (
                    f"Image {i + 1}: data:image/jpeg;base64,{base64_image}\n"
                )
            elif isinstance(image, str) and image.startswith("http"):
                message_content += f"Image {i + 1}: {image}\n"
            else:
                raise ValueError("Images must be Base64 bytes or valid URLs.")

        for attempt in range(retries):
            tokens_in = -1
            tokens_out = -1
            try:
                start_time = time.time()
                response = self.client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": role, "content": sys_msg},
                        {
                            "role": "user",
                            "content": message_content.strip(),
                        },
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                latency = time.time() - start_time

                if response.usage:
                    tokens_in = response.usage.prompt_tokens
                    tokens_out = response.usage.completion_tokens

                return TextGenerationResponse(
                    text=(
                        response.choices[0].message.content.strip()
                        if response.choices and response.choices[0].message.content
                        else ""
                    ),
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    latency=latency,
                )

            except Exception as e:
                logging.warning(
                    f"Attempt {attempt + 1}/{retries} to process images failed: {e}. Retrying..."
                )
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Image processing failed after {retries} attempts: {e}"
                    )
                time.sleep((2**attempt) * 0.5)

        raise RuntimeError("All retries failed for image processing.")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
            assert "model" in config, "Model name is required in config"
            assert isinstance(config.get("model"), str), "Model name must be a string"
            assert isinstance(
                config.get("max_tokens", 300), int
            ), "Max tokens must be an integer"
            assert isinstance(config.get("prompt", ""), str), "Prompt must be a string"
            return True
        except AssertionError as e:
            logging.error(f"OpenAI Vision Provider Validation Failed: {e}")
            return False
