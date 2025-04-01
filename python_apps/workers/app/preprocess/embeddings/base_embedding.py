from abc import ABC, abstractmethod
from typing import Dict, List

from elevaitelib.schemas.configuration import EmbeddingType, PreprocessEmbeddingInfo


EMBEDDING_REGISTRY: Dict[EmbeddingType, type["BaseEmbedding"]] = {}


def register_embedding(type: EmbeddingType, cls: type["BaseEmbedding"]):
    global EMBEDDING_REGISTRY
    if type in EMBEDDING_REGISTRY:
        raise ValueError(
            f"Error while registering class {cls.__name__} already taken by {EMBEDDING_REGISTRY[type].__name__}"
        )
    EMBEDDING_REGISTRY[type] = cls


class BaseEmbedding(ABC):
    """Interface for embedding models."""

    info: PreprocessEmbeddingInfo

    def __init__(self, emb_info: PreprocessEmbeddingInfo) -> None:
        super().__init__()
        self.info = emb_info

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs."""
