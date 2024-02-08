from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Batch
from qdrant_client.http.models import Distance, VectorParams
import os
import openai
import time
import tiktoken
import uuid


def get_qdrant_connection(qdrant_url, api_key):
    if api_key:
        return AsyncQdrantClient(url=qdrant_url, api_key=api_key)
    else:
        return AsyncQdrantClient(url=qdrant_url)


def set_openai_api_key():
    openai.api_key = os.environ["OPENAI_API_KEY"]


def get_qdrant_api_key():
    return os.environ["QDRANT_API_KEY"]


def get_qdrant_url():
    return os.environ["QDRANT_URL"]


def get_embedding_model():
    return "text-embedding-ada-002"


def get_vector_params(size, distance):
    return VectorParams(size=size, distance=distance)


def get_token_size(content):
    if content:
        encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(content))
        return num_tokens
    else:
        return None


async def recreate_collection(collection=None, size=1536, distance=Distance.COSINE):
    qdrant_conn = get_qdrant_connection(get_qdrant_url(), None)
    await qdrant_conn.recreate_collection(
        collection_name=collection,
        vectors_config=get_vector_params(size=size, distance=distance),
    )


async def insert_records(collection=None, payload_with_contents=None):
    if not payload_with_contents or not collection:
        return

    set_openai_api_key()
    embedding_model = get_embedding_model()
    payloads = []
    vectors = []
    ids = []
    qdrant_client = get_qdrant_connection(get_qdrant_url(), None)
    start_time = time.time()
    for payload in payload_with_contents:
        if payload["page_content"]:
            token_size = get_token_size(payload["page_content"])
            print(str(token_size))
            payload["metadata"]["tokenSize"] = token_size if token_size else 0
            response = create_embedding(
                input=payload["page_content"], embedding_model=embedding_model
            )
            payloads.append(payload)
            vectors.append(response["data"][0]["embedding"])
            ids.append(str(uuid.uuid4()))
        if len(payloads) >= 50:
            print("Print Embeddings Created " + str(len(vectors)))
            print("Print Payloads Created " + str(len(payloads)))
            await qdrant_client.upsert(
                collection_name=collection,
                points=Batch(ids=ids, payloads=payloads, vectors=vectors),
            )
            payloads.clear()
            vectors.clear()
            ids.clear()
    if len(payloads) > 0:
        print("Last Embeddings Created " + str(len(vectors)))
        print("Last Payloads Created " + str(len(payloads)))
        await qdrant_client.upsert(
            collection_name=collection,
            points=Batch(ids=ids, payloads=payloads, vectors=vectors),
        )
    end_time = time.time()
    print("Qdrant insert time " + str(end_time - start_time))


def create_embedding(input, embedding_model, depth=0):
    if depth > 3:
        raise Exception("Too many retries")
    try:
        time.sleep((5 * depth) + (6 / 1000))
        response = openai.Embedding.create(input=input, engine=embedding_model)
        return response
    except:
        return create_embedding(input, embedding_model, depth=depth + 1)
