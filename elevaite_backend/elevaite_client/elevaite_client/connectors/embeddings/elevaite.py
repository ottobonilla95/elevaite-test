import json
from typing import List

import requests

from .interfaces import EmbeddingInfo


def embed_documents(texts: List[str], info: EmbeddingInfo) -> List[List[float]]:
    # result: List[List[float]] = []
    if info.inference_url is None:
        raise ValueError("Inference Url is None for local embedding model")
    payload = {"args": [], "kwargs": {"sentences": texts}}
    _res = requests.post(url=info.inference_url, data=json.dumps(payload))
    if _res.ok:
        _res_json = _res.json()
        return _res_json["results"]
    raise Exception(_res)
