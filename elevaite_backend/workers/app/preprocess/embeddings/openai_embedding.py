import time
from typing import List

from elevaitedb.schemas.configuration import PreprocessEmbeddingInfo
import openai
from .base_embedding import BaseEmbedding


class OpenAIEmbedding(BaseEmbedding):
    def __init__(self, emb_info: PreprocessEmbeddingInfo) -> None:
        super().__init__(emb_info)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        result: List[List[float]] = []
        for text in texts:
            _res = self._embed_document(input=text, embedding_model=self.info.name)
            result.append(_res)
        return result

    def _embed_document(self, input: str, embedding_model: str, depth=0) -> List[float]:
        if depth > 10:
            raise Exception("Too many retries")
        try:
            time.sleep((5 * depth) + (6 / 1000))
            response = openai.Embedding.create(input=input, engine=embedding_model)
            return response["data"][0]["embedding"]  # type: ignore | It works
        except Exception as e:
            print(e)
            print(f"Depth: {depth}")
            return self._embed_document(input, embedding_model, depth=depth + 1)
