from abc import ABC, abstractmethod
from typing import List
from .interfaces import EmbeddingInfo


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo
    ) -> List[List[float]]:
        """Abstract method for embedding documents"""
        pass

    @abstractmethod
    def validate_config(self, info: EmbeddingInfo) -> bool:
        """Validate provider configuration"""
        pass
