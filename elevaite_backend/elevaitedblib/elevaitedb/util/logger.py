from typing import Any, Mapping
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
import os
import func as util_func


class ESLogger:
    client: Elasticsearch
    index: str

    def __init__(self, key: str) -> None:
        load_dotenv()
        ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
        ELASTIC_SSL_FINGERPRINT = os.getenv("ELASTIC_SSL_FINGERPRINT")
        ELASTIC_HOST = os.getenv("ELASTIC_HOST")
        self.client = Elasticsearch(
            ELASTIC_HOST,
            ssl_assert_fingerprint=ELASTIC_SSL_FINGERPRINT,
            basic_auth=("elastic", ELASTIC_PASSWORD),
        )
        self.index = key

        mappings: Mapping[str, Any] = {
            "properties": {
                "timestamp": {"type": "text"},
                "message": {"type": "text"},
                "level": {"type": "keyword"},
            }
        }

        self.client.indices.create(index=key, mappings=mappings)

    def info(self, message: str):
        self.client.create(
            index=self.index,
            document={
                "timestamp": util_func.get_iso_datetime(),
                "message": message,
                "level": "info",
            },
        )
