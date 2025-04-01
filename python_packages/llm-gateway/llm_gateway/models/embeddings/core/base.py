from abc import ABC, abstractmethod
from typing import List
from .interfaces import EmbeddingInfo, EmbeddingResponse


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def embed_documents(
        self, texts: List[str], info: EmbeddingInfo
    ) -> EmbeddingResponse:
        """
        Abstract method to embed a list of text documents into vector representations.
        :param texts: A list of strings representing the documents to be embedded.
        :param info: An instance of `EmbeddingInfo` containing metadata about the embedding process, such as:
            - 'model': The embedding model to use.
            - 'dimensions': The dimensionality of the embeddings.
            - 'context': Any additional context or configuration for embedding.
        :return: An `EmbeddingResponse` containing:
            - 'embeddings': A list of vectors representing the embeddings.
            - 'tokens': Number of tokens processed in the embedding request.
            - 'latency': Time taken to generate the embeddings, in seconds.
        """
        pass

    @abstractmethod
    def validate_config(self, info: EmbeddingInfo) -> bool:
        """
        Validate provider-specific configuration for embeddings.
        :param info: An instance of `EmbeddingInfo` containing configuration details.
        :return: True if the configuration is valid, False otherwise.
        """
        pass
