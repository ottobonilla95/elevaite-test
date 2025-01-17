import base64
import json
import logging
import time
import requests
from typing import Any, Dict, List, Union

from ...utilities.tokens import count_tokens
from ..text_generation.core.interfaces import TextGenerationResponse
from .core.base import BaseVisionProvider


class OnPremVisionProvider(BaseVisionProvider):
    def __init__(self, api_url: str, user: str, secret: str):
        if not all([api_url, user, secret]):
            raise EnvironmentError(
                "ONPREM_VISION_ENDPOINT, ONPREM_USER, and ONPREM_SECRET must be set"
            )

        self.api_url = api_url
        self.user = user
        self.secret = secret

    def generate_text(
        self, prompt: str, images: List[Union[bytes, str]], config: Dict[str, Any]
    ) -> TextGenerationResponse:
        retries = config.get("retries", 5)
        max_tokens = config.get("max_tokens", 50)

        files = []
        for i, image in enumerate(images):
            if isinstance(image, bytes):
                files.append(
                    ("image_files", (f"image_{i + 1}.jpg", image, "image/jpeg"))
                )
            elif isinstance(image, str) and image.startswith("http"):
                files.append(
                    (
                        "image_files",
                        (
                            f"image_{i + 1}.jpg",
                            requests.get(image).content,
                            "image/jpeg",
                        ),
                    )
                )
            else:
                raise ValueError("Images must be Base64 bytes or valid URLs.")

        message_content = prompt + "\n"
        message_content += "Look at these images: " + ", ".join(
            str(i) for i in range(len(images))
        )
        message_content += "\nWhat is the difference between them?"

        messages = [
            {
                "type": "text",
                "role": "user",
                "content": [message_content, *range(len(images))],
            }
        ]

        kwargs = {"max_new_tokens": max_tokens}

        data = {
            "json_messages": json.dumps(messages),
            "json_kwargs": json.dumps(kwargs),
        }

        headers = {"Content-Type": "application/json"}
        auth_value = base64.b64encode(f"{self.user}:{self.secret}".encode()).decode(
            "utf-8"
        )
        headers["Authorization"] = f"Basic {auth_value}"

        for attempt in range(retries):
            try:
                start_time = time.time()
                response = requests.post(
                    self.api_url,
                    files=files,
                    data=data,
                    headers=headers,
                    auth=(self.user, self.secret),
                    verify=False,
                )
                latency = time.time() - start_time

                if response.status_code == 200:
                    data = response.json()
                    if "result" in data and len(data["result"]) > 0:
                        processed_output = (
                            data["result"][0].get("generated_text", "").strip()
                        )
                        tokens_in = count_tokens([response.text])
                        tokens_out = count_tokens([processed_output])

                        return TextGenerationResponse(
                            text=processed_output,
                            tokens_in=tokens_in,
                            tokens_out=tokens_out,
                            latency=latency,
                        )
                    else:
                        logging.error(
                            "Failed to find the expected 'result' in the response."
                        )
                        return TextGenerationResponse(
                            text="",
                            tokens_in=-1,
                            tokens_out=-1,
                            latency=latency,
                        )
                else:
                    logging.warning(
                        f"Attempt {attempt + 1}/{retries} failed: {response.text}. Retrying..."
                    )
                    if attempt == retries - 1:
                        raise RuntimeError(
                            f"Vision generation failed after {retries} attempts: {response.text}"
                        )
                time.sleep((2**attempt) * 0.5)

            except requests.exceptions.RequestException as e:
                logging.warning(
                    f"Attempt {attempt + 1}/{retries} failed: {e}. Retrying..."
                )
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Vision generation failed after {retries} attempts: {e}"
                    )
                time.sleep((2**attempt) * 0.5)

        raise RuntimeError("All retries failed for vision processing.")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validates the configuration for On-Prem vision generation.
        :param config: Configuration options (e.g., model, max_tokens, retries).
        :return: True if configuration is valid, False otherwise.
        """
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
            assert "model" in config, "Model name is required in config"
            assert isinstance(config.get("model"), str), "Model name must be a string"
            assert isinstance(
                config.get("max_tokens", 50), int
            ), "Max tokens must be an integer"
            assert isinstance(
                config.get("retries", 5), int
            ), "Retries must be an integer"
            return True
        except AssertionError as e:
            logging.error(f"On-Prem Vision Provider Validation Failed: {e}")
            return False
