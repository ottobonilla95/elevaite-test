import base64
import httpx
import logging
import time
from google import genai
from google.genai import types

from typing import Any, Dict, List, Optional, Union

from ..text_generation.core.interfaces import TextGenerationResponse
from .core.base import BaseVisionProvider


class GeminiVisionProvider(BaseVisionProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

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
        max_tokens = max_tokens or 100
        temperature = temperature or 0.5
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

        prepared_images + [prompt]

        # Create generation config
        generation_config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        # Create content with system instruction, text, and images
        parts = []

        # Add text part
        if sys_msg:
            parts.append(types.Part(text=f"System: {sys_msg}\n\nUser: {prompt}"))
        else:
            parts.append(types.Part(text=prompt))

        # Add image parts
        for image_data in prepared_images:
            parts.append(
                types.Part(
                    inline_data=types.Blob(
                        mime_type=image_data["mime_type"], data=image_data["data"]
                    )
                )
            )

        contents = [types.Content(role="user", parts=parts)]

        for attempt in range(retries):
            tokens_in = -1
            tokens_out = -1
            try:
                start_time = time.time()

                # Make the API call using the new client
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=generation_config,
                )

                latency = time.time() - start_time

                # Get text content
                text_content = ""
                if hasattr(response, "text") and response.text:
                    text_content = response.text

                # Get token counts (if available)
                tokens_in = getattr(response, "input_tokens", len(prompt.split()))
                tokens_out = getattr(
                    response,
                    "output_tokens",
                    len(text_content.split()) if text_content else 0,
                )

                return TextGenerationResponse(
                    text=text_content.strip() if text_content else "",
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
