import json
import logging
import time
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

from .core.abstract import BaseTextGenerationProvider


class BedrockTextGenerationProvider(BaseTextGenerationProvider):
    def __init__(
        self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str
    ):
        """
        Initializes the Amazon Bedrock text generation provider.
        :param aws_access_key_id: AWS access key ID.
        :param aws_secret_access_key: AWS secret access key.
        :param region_name: AWS region name.
        """
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        """
        Generates text using the Amazon Bedrock API.
        :param prompt: The input text prompt.
        :param config: Configuration options (e.g., model, temperature, max_tokens).
        :return: Generated text as a string.
        """
        model_id = config.get("model_id", "titan-text-express-v1")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 256)
        retries = config.get("retries", 5)

        payload = {
            "inputText": prompt,
            "textGenerationConfig": {
                "temperature": temperature,
                "maxTokenCount": max_tokens,
            },
        }

        for attempt in range(retries):
            try:
                response = self.client.invoke_model(
                    modelId=model_id, body=json.dumps(payload)
                )

                response_body = json.loads(response["body"])

                if "results" in response_body and len(response_body["results"]) > 0:
                    return response_body["results"][0]["outputText"].strip()

                raise ValueError(
                    "Invalid response structure: 'results' key missing or empty"
                )

            except ClientError as e:
                logging.warning(
                    f"Attempt {attempt + 1}/{retries} failed: {e}. Retrying..."
                )
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Text generation failed after {retries} attempts: {e}"
                    )
                time.sleep((2**attempt) * 0.5)
        return ""

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validates the configuration for Amazon Bedrock text generation.
        :param config: Configuration options (e.g., model_id, temperature, max_tokens).
        :return: True if configuration is valid, False otherwise.
        """
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
            assert "model_id" in config, "Model ID is required in config"
            assert isinstance(
                config.get("temperature", 0.7), (float, int)
            ), "Temperature must be a number"
            assert isinstance(
                config.get("max_tokens", 256), int
            ), "Max tokens must be an integer"
            return True
        except AssertionError as e:
            logging.error(f"Amazon Bedrock Provider Validation Failed: {e}")
            return False
