import logging
from aiohttp import ClientError
import boto3
import json
from typing import List
from .core.base import BaseEmbeddingProvider
from .core.interfaces import EmbeddingInfo, EmbeddingType


class BedrockEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(
        self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str
    ):
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo
    ) -> List[List[float]]:
        return [self._embed_document(text, info.name) for text in texts]

    def _embed_document(self, text: str, embedding_model: str) -> List[float]:
        formatted_prompt = f"Human: {text}\n\nAssistant:"

        payload = {
            "prompt": formatted_prompt,
            "max_tokens_to_sample": 1024,
        }

        try:
            response = self.client.invoke_model(
                modelId=embedding_model,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload),
            )

            response_body_raw = response["body"].read().decode("utf-8")
            logging.debug(f"Full response body: {response_body_raw}")
            response_body = json.loads(response_body_raw)

            logging.debug(f"Bedrock Embedding Response: {response_body}")

            if "completion" in response_body:
                return self.text_to_embedding(response_body["completion"])

            raise ValueError("Embedding or completion key not found in the response")

        except ClientError as e:
            logging.error(f"Error occurred while invoking Bedrock API: {e}")
            raise RuntimeError(f"Embedding generation failed due to ClientError: {e}")
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            raise RuntimeError(
                f"Embedding generation failed due to unexpected error: {e}"
            )

    def text_to_embedding(self, text: str) -> List[float]:
        return [float(ord(char)) for char in text]

    def validate_config(self, info: EmbeddingInfo) -> bool:
        try:
            assert info.type == EmbeddingType.BEDROCK, "Invalid provider type"
            assert info.name is not None, "Model name required"
            test_embedding = self._embed_document("Test connectivity", info.name)
            assert len(test_embedding) > 0, "Embedding generation failed"
            return True
        except AssertionError as e:
            logging.error(f"Bedrock Provider Validation Failed: {e}")
            return False
