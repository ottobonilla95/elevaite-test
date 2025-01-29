import json
import boto3
import httpx
import base64
import logging
import time
from botocore.exceptions import ClientError
from typing import Any, Dict, List, Optional, Union

from ..text_generation.core.interfaces import TextGenerationResponse
from .core.base import BaseVisionProvider


class BedrockVisionProvider(BaseVisionProvider):
    def __init__(
        self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str
    ):
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

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
        model_name = model_name or "anthropic.claude-3-5-sonnet-20240620-v1:0"
        prompt = prompt or ""
        config = config or {}
        retries = retries or 5
        max_tokens = max_tokens or 100

        prepared_image_data = []
        for image in images:
            if isinstance(image, bytes):
                prepared_image_data.append(base64.b64encode(image).decode("utf-8"))
            elif isinstance(image, str) and image.startswith("http"):
                try:
                    response = httpx.get(image)
                    response.raise_for_status()
                    prepared_image_data.append(
                        base64.b64encode(response.content).decode("utf-8")
                    )
                except Exception as e:
                    raise ValueError(f"Failed to fetch image from URL {image}: {e}")
            else:
                raise ValueError("Images must be Base64 bytes or valid URLs.")

        formatted_prompt = "Human: " + prompt + "\n\n"

        for i, image_data in enumerate(prepared_image_data):
            formatted_prompt += f"Image {i + 1} (Base64): {image_data}\n\n"

        if sys_msg:
            formatted_prompt = f"{sys_msg}\n\n{formatted_prompt}"

        formatted_prompt += "Assistant:"

        payload = {
            "prompt": formatted_prompt,
            "max_tokens_to_sample": max_tokens,
        }

        for attempt in range(retries):
            tokens_in = -1
            tokens_out = -1
            try:
                start_time = time.time()
                response = self.client.invoke_model_with_response_stream(
                    modelId=model_name,
                    body=json.dumps(payload),
                )

                latency = time.time() - start_time

                response_body_raw = response["body"].read().decode("utf-8")
                logging.debug(f"Full response body: {response_body_raw}")
                response_body = json.loads(response_body_raw)

                if "completion" in response_body:
                    completion_text = response_body["completion"].strip()

                    tokens_in = response_body.get("input_tokens", len(prompt.split()))
                    tokens_out = response_body.get(
                        "output_tokens", len(completion_text.split())
                    )

                    return TextGenerationResponse(
                        text=completion_text,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        latency=latency,
                    )

                raise ValueError(
                    "Invalid response structure: Missing 'completion' key."
                )

            except ClientError as e:
                logging.warning(
                    f"Attempt {attempt + 1}/{retries} failed due to ClientError: {e}. Retrying..."
                )
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Vision processing failed after {retries} attempts: {e}"
                    )
                time.sleep((2**attempt) * 0.5)

            except ValueError as ve:
                logging.error(f"ValueError encountered: {ve}")
                raise ve

        raise RuntimeError("All retries failed for vision processing.")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        try:
            assert isinstance(config, dict), "Config must be a dictionary."
            assert "model" in config, "Model ID is required in the config."
            assert isinstance(config.get("model"), str), "Model ID must be a string."
            assert isinstance(
                config.get("max_tokens", 300), int
            ), "Max tokens must be an integer."
            return True
        except AssertionError as e:
            logging.error(f"Amazon Bedrock Vision Provider Validation Failed: {e}")
            return False
