import logging
import subprocess
from typing import List
from .core.abstract import BaseEmbeddingProvider
from .core.interfaces import EmbeddingInfo, EmbeddingType


class OnPremLLMEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, model_path: str):
        self.model_path = model_path

    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo
    ) -> List[List[float]]:
        return [self._embed_document(text) for text in texts]

    def _embed_document(self, text: str) -> List[float]:
        result = subprocess.run(
            [
                "python",
                "local_inference.py",
                "--model",
                self.model_path,
                "--text",
                text,
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"Embedding failed: {result.stderr}")
        return list(map(float, result.stdout.strip().split(",")))

    def validate_config(self, info: EmbeddingInfo) -> bool:
        try:
            assert info.type == EmbeddingType.ON_PREM, "Invalid provider type"
            assert self.model_path is not None, "Model path required"
            return True
        except AssertionError as e:
            logging.error(f"On-Prem LLM Provider Validation Failed: {e}")
            return False
