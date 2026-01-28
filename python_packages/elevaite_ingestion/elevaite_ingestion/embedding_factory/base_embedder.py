from abc import ABC, abstractmethod
from typing import List


class BaseEmbedder(ABC):
    """Abstract base class for embedding models."""

    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        """Generate an embedding from text."""
        pass
