from typing import Any, Mapping
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
import os
from uuid import uuid4
from . import func as util_func


class ESLogger:
    client: Elasticsearch
    index: str

    def __init__(
        self,
        key: str,
        password: str | None = None,
        fingerprint: str | None = None,
        username: str | None = None,
        host: str | None = None,
    ) -> None:
        load_dotenv()
        ELASTIC_PASSWORD = (
            password if password is not None else os.getenv("ELASTIC_PASSWORD")
        )
        if ELASTIC_PASSWORD is None:
            raise Exception("ELASTIC_PASSWORD is null")
        ELASTIC_SSL_FINGERPRINT = (
            fingerprint
            if fingerprint is not None
            else os.getenv("ELASTIC_SSL_FINGERPRINT")
        )
        if ELASTIC_SSL_FINGERPRINT is None:
            raise Exception("ELASTIC_SSL_FINGERPRINT is null")
        ELASTIC_USERNAME = (
            username if username is not None else os.getenv("ELASTIC_USERNAME")
        )
        if ELASTIC_USERNAME is None:
            raise Exception("ELASTIC_USERNAME is null")
        ELASTIC_HOST = host if host is not None else os.getenv("ELASTIC_HOST")
        self.client = Elasticsearch(
            ELASTIC_HOST,
            ssl_assert_fingerprint=ELASTIC_SSL_FINGERPRINT,
            basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD),
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
            id=str(uuid4()),
            document={
                "timestamp": util_func.get_iso_datetime(),
                "message": message,
                "level": "info",
            },
        )

    def error(self, message: str):
        self.client.create(
            index=self.index,
            id=str(uuid4()),
            document={
                "timestamp": util_func.get_iso_datetime(),
                "message": message,
                "level": "error",
            },
        )

    def destroy(self):
        self.client.close()
