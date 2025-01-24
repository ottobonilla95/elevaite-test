import base64
import httpx
import logging
import time
import google.generativeai as genai

from typing import Any, Dict, List, Optional, Union

from ..text_generation.core.interfaces import TextGenerationResponse
from .core.base import BaseVisionProvider


class GeminiVisionProvider(BaseVisionProvider):
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.client = genai

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
        model_name = model_name or "gemini-1.5-pro"
        prompt = prompt or ""
        retries = retries or 5

        prepared_images = []
        for image in images:
            if isinstance(image, bytes):
                prepared_images.append(
                    {
                        "mime_type": "image/jpeg",
                        "data": base64.b64encode(image).decode("utf-8"),
                    }
                )
            elif isinstance(image, str) and image.startswith("http"):
                try:
                    response = httpx.get(image)
                    response.raise_for_status()
                    prepared_images.append(
                        {
                            "mime_type": "image/jpeg",
                            "data": base64.b64encode(response.content).decode("utf-8"),
                        }
                    )
                except Exception as e:
                    raise ValueError(f"Failed to fetch image from URL {image}: {e}")
            else:
                raise ValueError("Images must be Base64 bytes or valid URLs.")

        input_data = prepared_images + [prompt]

        for attempt in range(retries):
            tokens_in = -1
            tokens_out = -1
            try:
                start_time = time.time()
                response = self.client.GenerativeModel(
                    model_name=model_name, system_instruction=sys_msg
                ).generate_content(input_data)
                latency = time.time() - start_time

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
            return True
        except AssertionError as e:
            logging.error(f"Gemini Vision Provider Validation Failed: {e}")
            return False
