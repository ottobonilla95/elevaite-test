import json
from typing import List

from elevaitelib.schemas.configuration import PreprocessEmbeddingInfo
import requests
from .base_embedding import BaseEmbedding


class LocalEmbedding(BaseEmbedding):
    def __init__(self, emb_info: PreprocessEmbeddingInfo) -> None:
        super().__init__(emb_info)
        if emb_info.inference_url is None:
            raise ValueError("Inference Url is None for local embedding model")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # result: List[List[float]] = []
        if self.info.inference_url is None:
            raise ValueError("Inference Url is None for local embedding model")
        payload = {"args": [], "kwargs": {"sentences": texts}}
        _res = requests.post(url=self.info.inference_url, data=json.dumps(payload))
        if _res.ok:
            _res_json = _res.json()
            return _res_json["results"]
        raise Exception(_res)
