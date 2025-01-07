import logging
import requests
import json
from typing import List

from .core.abstract import BaseEmbeddingProvider
from .core.interfaces import EmbeddingInfo, EmbeddingType


class CustomLLMEmbeddingProvider(BaseEmbeddingProvider):
    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo
    ) -> List[List[float]]:
        if info.inference_url is None:
            raise ValueError("Inference Url is None for local embedding model")
        payload = {"args": [], "kwargs": {"sentences": texts}}
        _res = requests.post(url=info.inference_url, data=json.dumps(payload))
        if _res.ok:
            _res_json = _res.json()
            return _res_json["results"]
        raise Exception(f"Embedding request failed: {_res.text}")

    def _embed_document(self, text: str, embedding_model: str) -> List[float]:
        raise NotImplementedError(
            "elevAIte does not support single-document embedding."
        )

    def validate_config(self, info: EmbeddingInfo) -> bool:
        try:
            assert info.type == EmbeddingType.LOCAL, "Invalid provider type"
            assert info.inference_url is not None, "Inference URL required"

            test_payload = {"args": [], "kwargs": {"sentences": ["Test connectivity"]}}
            _res = requests.post(url=info.inference_url, data=json.dumps(test_payload))
            assert _res.ok and "results" in _res.json(), "Embedding generation failed"

            return True
        except AssertionError as e:
            logging.error(f"elevAIte Provider Validation Failed: {e}")
            return False
