import logging
import boto3
import json
from typing import List
from .core.abstract import BaseEmbeddingProvider
from .core.interfaces import EmbeddingInfo, EmbeddingType


class BedrockEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, aws_region: str):
        self.client = boto3.client("bedrock-runtime", region_name=aws_region)

    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo
    ) -> List[List[float]]:
        return [self._embed_document(text, info.name) for text in texts]

    def _embed_document(self, text: str, embedding_model: str) -> List[float]:
        payload = json.dumps({"inputText": text})
        response = self.client.invoke_model(
            modelId=embedding_model,
            contentType="application/json",
            accept="application/json",
            body=payload,
        )
        result = json.loads(response["body"].read())
        return result["embedding"]

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
