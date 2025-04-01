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
        temperature = temperature if temperature is not None else 0.5
        max_tokens = max_tokens if max_tokens is not None else 100
        sys_msg = sys_msg or ""
        prompt = prompt or ""
        retries = retries if retries is not None else 5
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
                raise ValueError("Images must be either URL strings or image bytes.")

        messages = [
            {"role": "user", "content": [prompt] + [idx for idx in range(len(images))]}
        ]

        onprem_generation_args = {
            "temperature": temperature,
            "max_new_tokens": max_tokens,
            "sys_msg": sys_msg,
            "prompt": prompt,
            "do_sample": config.get("do_sample", False),
        }

        # We dump the top-level generation arguments and include the original config
        data = {
            "json_messages": json.dumps(messages),
            "json_generation_args": json.dumps(onprem_generation_args),
            "json_kwargs": json.dumps(config),
        }

        for attempt in range(retries):
            try:
                if self.user is None or self.secret is None:
                    raise EnvironmentError("Missing required authentication details.")

                tokens_in = count_tokens([prompt])
                start_time = time.time()
                response = requests.post(
                    get_model_endpoint(model_name),
                    files=files,
                    data=data,
                    auth=(self.user, self.secret),
                    verify=True,
                )
                latency = time.time() - start_time

                if response.status_code == 200:
                    response_text = response.text.strip()
                    tokens_out = count_tokens([response_text])
                    return TextGenerationResponse(
                        text=response_text,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        latency=latency,
                    )
                else:
                    logging.warning(
                        f"Attempt {attempt + 1}/{retries} failed: {response.text}. Retrying..."
                    )
                    if attempt == retries - 1:
                        raise RuntimeError(
                            f"OnPrem vision call failed after {retries} attempts: {response.text}"
                        )
                time.sleep((2**attempt) * 0.5)
            except requests.exceptions.RequestException as e:
                logging.warning(
                    f"Attempt {attempt + 1}/{retries} failed: {e}. Retrying..."
                )
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"OnPrem vision call failed after {retries} attempts: {e}"
                    )
                time.sleep((2**attempt) * 0.5)

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
