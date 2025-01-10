import json
import logging
import time
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

from .core.base import BaseTextGenerationProvider


class BedrockTextGenerationProvider(BaseTextGenerationProvider):
    def __init__(
        self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str
    ):
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        model_name = config.get("model", "anthropic.claude-instant-v1")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 256)
        sys_msg = config.get("sys_msg", "")
        retries = config.get("retries", 5)

        formatted_prompt = f"Human: {prompt}\n\nAssistant:{sys_msg}"

        payload = {
            "prompt": formatted_prompt,
            "temperature": temperature,
            "max_tokens_to_sample": max_tokens,
        }

        for attempt in range(retries):
            try:
                response = self.client.invoke_model(
                    modelId=model_name,
                    body=json.dumps(payload),
                )

                response_body_raw = response["body"].read().decode("utf-8")
                logging.debug(f"Full response body: {response_body_raw}")
                response_body = json.loads(response_body_raw)

                if "completion" in response_body:
                    return response_body["completion"].strip()

                raise ValueError(
                    "Invalid response structure: Missing 'completion' key."
                )

            except ClientError as e:
                logging.warning(
                    f"Attempt {attempt + 1}/{retries} failed due to ClientError: {e}. Retrying..."
                )
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Text generation failed after {retries} attempts: {e}"
                    )
                time.sleep((2**attempt) * 0.5)

            except ValueError as ve:
                logging.error(f"ValueError encountered: {ve}")
                raise ve

        return ""

    def validate_config(self, config: Dict[str, Any]) -> bool:
        try:
            assert isinstance(config, dict), "Config must be a dictionary."
            assert "model" in config, "Model ID is required in the config."
            assert isinstance(config.get("model"), str), "Model ID must be a string."
            assert isinstance(
                config.get("temperature", 0.7), (float, int)
            ), "Temperature must be a number."
            assert isinstance(
                config.get("max_tokens", 256), int
            ), "Max tokens must be an integer."
            return True
        except AssertionError as e:
            logging.error(f"Amazon Bedrock Provider Validation Failed: {e}")
            return False
