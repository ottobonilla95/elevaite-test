from typing import List
from elevaitedb.schemas.instance import InstancePipelineStepData, InstanceStepDataLabel
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Batch
from qdrant_client.http.models import Distance, VectorParams
import os
import openai
import time
import tiktoken
import uuid
from sqlalchemy.orm import Session

from elevaite_backend.workers.app.util.func import set_pipeline_step_meta

from .preprocess import ChunkAsJson


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


def get_token_size(content) -> int | None:
    if content:
        encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(content))
        return num_tokens
    else:
        return None


async def recreate_collection(
    collection_name: str, size=1536, distance=Distance.COSINE
):
    qdrant_conn = get_qdrant_connection(get_qdrant_url(), None)
    await qdrant_conn.recreate_collection(
        collection_name=collection_name,
        vectors_config=get_vector_params(size=size, distance=distance),
    )


async def insert_records(
    db: Session,
    instance_id: str,
    step_id: str,
    collection=None,
    payload_with_contents: List[ChunkAsJson] | None = None,
):
    if not payload_with_contents or not collection:
        return

    set_openai_api_key()
    embedding_model = get_embedding_model()
    payloads = []
    vectors = []
    ids = []
    total_token_size = 0
    avg_token_size = 0
    max_token_size = 0
    p_index = 0
    qdrant_client = get_qdrant_connection(get_qdrant_url(), None)
    start_time = time.time()
    for payload in payload_with_contents:
        p_index += 1
        if payload.page_content:
            token_size = get_token_size(payload.page_content)
            if token_size is not None:
                if token_size > max_token_size:
                    max_token_size = token_size
                total_token_size += token_size
                avg_token_size = total_token_size / p_index
            print(str(token_size))
            payload.metadata["tokenSize"] = token_size if token_size else 0
            response = create_embedding(
                input=payload.page_content, embedding_model=embedding_model
            )
            payloads.append(payload)
            _emb = response["data"][0]["embedding"]  # type: ignore | It works
            vectors.append(_emb)
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

            set_pipeline_step_meta(
                db=db,
                instance_id=instance_id,
                step_id=step_id,
                meta=[
                    InstancePipelineStepData(
                        label=InstanceStepDataLabel.TOTAL_SEGMENTS_TOKENIZED,
                        value=p_index,
                    ),
                    InstancePipelineStepData(
                        label=InstanceStepDataLabel.LRGST_TOKEN_SIZE,
                        value=max_token_size,
                    ),
                    InstancePipelineStepData(
                        label=InstanceStepDataLabel.AVG_TOKEN_SIZE,
                        value=str(avg_token_size),
                    ),
                    InstancePipelineStepData(
                        label=InstanceStepDataLabel.EMB_MODEL,
                        value=embedding_model,
                    ),
                    InstancePipelineStepData(
                        label=InstanceStepDataLabel.EMB_MODEL_DIM,
                        value=1536,
                    ),
                ],
            )
    if len(payloads) > 0:
        print("Last Embeddings Created " + str(len(vectors)))
        print("Last Payloads Created " + str(len(payloads)))
        await qdrant_client.upsert(
            collection_name=collection,
            points=Batch(ids=ids, payloads=payloads, vectors=vectors),
        )

        set_pipeline_step_meta(
            db=db,
            instance_id=instance_id,
            step_id=step_id,
            meta=[
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.TOTAL_SEGMENTS_TOKENIZED,
                    value=p_index,
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.LRGST_TOKEN_SIZE,
                    value=max_token_size,
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.AVG_TOKEN_SIZE,
                    value=str(avg_token_size),
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.EMB_MODEL,
                    value=embedding_model,
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.EMB_MODEL_DIM,
                    value=1536,
                ),
            ],
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
