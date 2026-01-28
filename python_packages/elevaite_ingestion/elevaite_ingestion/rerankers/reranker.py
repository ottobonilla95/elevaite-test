from abc import ABC, abstractmethod
import os
import cohere
from scipy.stats import beta


class Reranker(ABC):
    subclasses = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.subclasses[cls.__name__] = cls

    def to_dict(self):
        return {
            "subclass_name": self.__class__.__name__,
        }

    @classmethod
    def from_dict(cls, config):
        subclass_name = config.pop("subclass_name", None)
        subclass = cls.subclasses.get(subclass_name)
        if subclass:
            return subclass(**config)
        else:
            raise ValueError(f"Unknown subclass: {subclass_name}")

    @abstractmethod
    def rerank_search_results(self, query: str, search_results: list) -> list:
        pass


class CohereReranker(Reranker):
    def __init__(self, model: str = "rerank-english-v3.0"):
        self.model = model
        cohere_api_key = os.environ["CO_API_KEY"]
        self.client = cohere.Client(api_key=cohere_api_key)

    def transform(self, x):
        """
        Maps absolute relevance values to a normalized range between 0 and 1
        """
        a, b = 0.4, 0.4
        return beta.cdf(x, a, b)

    def rerank_search_results(self, query: str, search_results: list) -> list:
        documents = [
            f"{result['metadata']['chunk_header']}\n\n{result['metadata']['chunk_text']}"
            for result in search_results
        ]
        reranked_results = self.client.rerank(
            model=self.model, query=query, documents=documents
        )

        results = reranked_results.results
        reranked_indices = [result.index for result in results]
        reranked_similarity_scores = [result.relevance_score for result in results]

        reranked_search_results = [search_results[i] for i in reranked_indices]
        for i, result in enumerate(reranked_search_results):
            result["similarity"] = self.transform(reranked_similarity_scores[i])

        return reranked_search_results

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({"model": self.model})
        return base_dict


class NoReranker(Reranker):
    def __init__(self, ignore_absolute_relevance: bool = False):
        self.ignore_absolute_relevance = ignore_absolute_relevance

    def rerank_search_results(self, query: str, search_results: list) -> list:
        if self.ignore_absolute_relevance:
            for result in search_results:
                result["similarity"] = 0.8
        return search_results

    def to_dict(self):
        base_dict = super().to_dict()
        base_dict.update({"ignore_absolute_relevance": self.ignore_absolute_relevance})
        return base_dict
