import base64
import json
import logging
import time
import requests
from typing import Any, Dict, List, Optional, Union


from ...utilities.onprem import get_model_endpoint
from ...utilities.tokens import count_tokens
from ..text_generation.core.interfaces import TextGenerationResponse
from .core.base import BaseVisionProvider


class OnPremVisionProvider(BaseVisionProvider):
    def __init__(self, user: str, secret: str):
        if not all([user, secret]):
            raise EnvironmentError(
                "ONPREM_VISION_ENDPOINT, ONPREM_USER, and ONPREM_SECRET must be set"
            )

        self.user = user
        self.secret = secret

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
        model_name = model_name or "MiniCPM-V-2_6"
        prompt = prompt or ""
        config = config or {}

        files = []
        for idx, img in enumerate(images):
            if isinstance(img, str):
                response = requests.get(img)
                if response.status_code == 200:
                    img_data = response.content
                    files.append(
                        ("image_files", (f"{idx}.jpg", img_data, "image/jpeg"))
                    )
                else:
                    raise ValueError(f"Failed to retrieve image from URL: {img}")
            elif isinstance(img, bytes):
                files.append(("image_files", (f"{idx}.jpg", img, "image/jpeg")))
            else:
                raise ValueError(
                    "Images must be either file paths (str) or image bytes (bytes)."
                )

        messages = [
            {"role": "user", "content": [prompt] + [idx for idx in range(len(images))]}
        ]

        data = {
            "json_messages": json.dumps(messages),
            "json_kwargs": json.dumps(config),
        }

        try:
            start_time = time.time()
            response = requests.post(
                get_model_endpoint(model_name),
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
