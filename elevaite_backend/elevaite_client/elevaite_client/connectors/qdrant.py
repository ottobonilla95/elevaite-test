import os
from typing import List, Optional, Union

from pydantic import StrictInt, StrictStr
from ..connectors.embeddings import EmbeddingInfo, EmbeddingResult
from qdrant_client import AsyncQdrantClient, QdrantClient
from qdrant_client.http.models import (
    Batch,
    Distance,
    VectorParams,
    ExtendedPointId,
    BatchVectorStruct,
    Payload,
)


def get_qdrant_api_key() -> str | None:
    return os.getenv("QDRANT_API_KEY")


def get_qdrant_url() -> str | None:
    return os.getenv("QDRANT_URL")


def get_async_qdrant_connection() -> AsyncQdrantClient:
    qdrant_url: str | None = get_qdrant_url()

    api_key: str | None = get_qdrant_api_key()
    if api_key:
        return AsyncQdrantClient(url=qdrant_url, api_key=api_key)
    else:
        return AsyncQdrantClient(url=qdrant_url)


def get_qdrant_connection() -> QdrantClient:
    qdrant_url: str | None = get_qdrant_url()

    api_key: str | None = get_qdrant_api_key()
    if api_key:
        return QdrantClient(url=qdrant_url, api_key=api_key)
    else:
        return QdrantClient(url=qdrant_url)


def get_vector_params(size, distance):
    return VectorParams(size=size, distance=distance)


async def async_recreate_collection(
    collection_name: str, size=1536, distance=Distance.COSINE
):
    qdrant_conn = get_async_qdrant_connection()
    await qdrant_conn.recreate_collection(
        collection_name=collection_name,
        vectors_config=get_vector_params(size=size, distance=distance),
    )


def recreate_collection(
    collection_name: str, size: int = 1536, distance: Distance = Distance.COSINE
):
    qdrant_conn = get_qdrant_connection()
    qdrant_conn.recreate_collection(
        collection_name=collection_name,
        vectors_config=get_vector_params(size=size, distance=distance),
    )


def upsert_records(
    connection: QdrantClient,
    collection_name: str,
    ids: List[Union[StrictStr, StrictInt]],
    payloads: Optional[List[Payload]],
    vectors: BatchVectorStruct,
):
    return connection.upsert(
        collection_name=collection_name,
        points=Batch(ids=ids, payloads=payloads, vectors=vectors),
    )
