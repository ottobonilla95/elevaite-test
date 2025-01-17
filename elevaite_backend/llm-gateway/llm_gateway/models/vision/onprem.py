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
        files = []
        for idx, img in enumerate(images):
            if isinstance(img, str):
                with open(img, "rb") as f:
                    files.append(
                        ("image_files", (f"{idx}.jpg", f.read(), "image/jpeg"))
                    )
            elif isinstance(img, bytes):
                files.append(("image_files", (f"{idx}.jpg", img, "image/jpeg")))
            else:
                raise ValueError(
                    "Images must be either file paths (str) or image bytes (bytes)."
                )

        messages = [
            {"role": "user", "content": [prompt] + [idx for idx in range(len(images))]}
        ]

        kwargs = config

        data = {
            "json_messages": json.dumps(messages),
            "json_kwargs": json.dumps(kwargs),
        }

        try:
            start_time = time.time()
            response = requests.post(
                self.api_url,
                files=files,
                data=data,
                auth=(self.user, self.secret),
                verify=False,
            )
            latency = time.time() - start_time

            if response.status_code == 200:
                response_text = response.text
                return TextGenerationResponse(
                    text=response_text,
                    tokens_in=count_tokens([prompt]),
                    tokens_out=count_tokens([response_text]),
                    latency=latency,
                )
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Request failed: {e}")

        raise RuntimeError("All retries failed for image processing.")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
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
