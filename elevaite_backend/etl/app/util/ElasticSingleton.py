import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from .SingletonMeta import SingletonMeta


class ElasticSingleton(metaclass=SingletonMeta):
    client: Elasticsearch = None  # type: ignore

    def __init__(self) -> None:
        load_dotenv()
        ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
        if ELASTIC_PASSWORD is None:
            raise Exception("Missing ELASTIC_PASSWORD from the environment")
        ELASTIC_SSL_FINGERPRINT = os.getenv("ELASTIC_SSL_FINGERPRINT")
        if ELASTIC_SSL_FINGERPRINT is None:
            raise Exception("Missing ELASTIC_SSL_FINGERPRINT from the environment")
        ELASTIC_HOST = os.getenv("ELASTIC_HOST")
        if ELASTIC_HOST is None:
            raise Exception("Missing ELASTIC_HOST from the environment")

        # Create the client instance
        self.client = Elasticsearch(
            ELASTIC_HOST,
            ssl_assert_fingerprint=ELASTIC_SSL_FINGERPRINT,
            basic_auth=("elastic", ELASTIC_PASSWORD),
        )

    def getAllInIndex(self, index: str, pagesize: int = 250, **kwargs):
        """
        Helper to iterate ALL values from
        Yields all the documents.
        """
        offset = 0
        while True:
            result = self.client.search(index=index, **kwargs, body={"size": pagesize, "from": offset})
            hits = result["hits"]["hits"]
            # Stop after no more docs
            if not hits:
                break
            # Yield each entry
            yield from (hit["_source"] for hit in hits)
            # Continue from there
            offset += pagesize

    def getAllInIndexPaginated(self, index: str, pagesize: int = 250, offset: int = 0, **kwargs):
        result = self.client.search(index=index, **kwargs, body={"size": pagesize, "from": offset})
        return result["hits"]["hits"]

    def getById(self, index: str, id: str):
        return self.client.get(index=index, id=id)
