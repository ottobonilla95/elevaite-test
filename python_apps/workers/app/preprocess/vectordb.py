from typing import List, Optional
from elevaitelib.schemas.configuration import EmbeddingType, PreprocessEmbeddingInfo
from elevaitelib.schemas.instance import InstancePipelineStepData, InstanceStepDataLabel
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Batch
from qdrant_client.http.models import Distance, VectorParams
import os
import openai
import time
import tiktoken
import uuid
from sqlalchemy.orm import Session

from .embeddings.base_embedding import EMBEDDING_REGISTRY

from ..util.func import set_pipeline_step_meta

from .preprocess import ChunkAsJson


DEFAULT_INFO: PreprocessEmbeddingInfo = PreprocessEmbeddingInfo(
    inference_url=None,
    name="text-embedding-ada-002",
    type=EmbeddingType.OPENAI,
    dimensions=1536,
)


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


def get_embedding_model(emb_info: Optional[PreprocessEmbeddingInfo] = None):
    _info = emb_info if emb_info is not None else DEFAULT_INFO
    global EMBEDDING_REGISTRY
    return EMBEDDING_REGISTRY[_info.type](_info)


def get_vector_params(size, distance):
    return VectorParams(size=size, distance=distance)


def get_token_size(content) -> int | None:
    if content:
        encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(content))
        return num_tokens
    else:
        return None


async def recreate_collection(collection_name: str, size=1536, distance=Distance.COSINE):
    qdrant_conn = get_qdrant_connection(get_qdrant_url(), None)
    await qdrant_conn.recreate_collection(
        collection_name=collection_name,
        vectors_config=get_vector_params(size=size, distance=distance),
    )


async def insert_records(
    # db: Session,
    # instance_id: str,
    # step_id: str,
    collection=None,
    payload_with_contents: List[ChunkAsJson] | None = None,
    emb_info: Optional[PreprocessEmbeddingInfo] = None,
):
    if not payload_with_contents or not collection:
        return

    set_openai_api_key()
    embedding = get_embedding_model(emb_info)
    payloads = []
    vectors = []
    ids = []
    total_token_size = 0
    avg_token_size = 0
    max_token_size = 0
    min_token_size = 2 ^ 32 - 1
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
                if token_size < min_token_size:
                    min_token_size = token_size
                total_token_size += token_size
                avg_token_size = total_token_size / p_index
            payload.metadata["tokenSize"] = token_size if token_size else 0
            response = embedding.embed_documents([payload.page_content])
            # response = create_embedding(
            #     input=payload.page_content, embedding_model=embedding_model
            # )
            payloads.append(payload)
            vectors.extend(response)
            ids.append(str(uuid.uuid4()))
        if len(payloads) >= 64:
            await qdrant_client.upsert(
                collection_name=collection,
                points=Batch(ids=ids, payloads=payloads, vectors=vectors),
            )
            payloads.clear()
            vectors.clear()
            ids.clear()

            # set_pipeline_step_meta(
            #     db=db,
            #     instance_id=instance_id,
            #     step_id=step_id,
            #     meta=[
            #         InstancePipelineStepData(
            #             label=InstanceStepDataLabel.TOTAL_SEGMENTS_TOKENIZED,
            #             value=p_index,
            #         ),
            #         InstancePipelineStepData(
            #             label=InstanceStepDataLabel.LRGST_TOKEN_SIZE,
            #             value=max_token_size,
            #         ),
            #         InstancePipelineStepData(
            #             label=InstanceStepDataLabel.AVG_TOKEN_SIZE,
            #             value=str(avg_token_size),
            #         ),
            #         InstancePipelineStepData(
            #             label=InstanceStepDataLabel.EMB_MODEL,
            #             value=embedding.info.name,
            #         ),
            #         InstancePipelineStepData(
            #             label=InstanceStepDataLabel.EMB_MODEL_DIM,
            #             value=embedding.info.dimensions,
            #         ),
            #         InstancePipelineStepData(
            #             label=InstanceStepDataLabel.MIN_TOKEN_SIZE,
            #             value=min_token_size,
            #         ),
            #     ],
            # )
    if len(payloads) > 0:
        await qdrant_client.upsert(
            collection_name=collection,
            points=Batch(ids=ids, payloads=payloads, vectors=vectors),
        )

        # set_pipeline_step_meta(
        #     db=db,
        #     instance_id=instance_id,
        #     step_id=step_id,
        #     meta=[
        #         InstancePipelineStepData(
        #             label=InstanceStepDataLabel.TOTAL_SEGMENTS_TOKENIZED,
        #             value=p_index,
        #         ),
        #         InstancePipelineStepData(
        #             label=InstanceStepDataLabel.LRGST_TOKEN_SIZE,
        #             value=max_token_size,
        #         ),
        #         InstancePipelineStepData(
        #             label=InstanceStepDataLabel.AVG_TOKEN_SIZE,
        #             value=str(avg_token_size),
        #         ),
        #         InstancePipelineStepData(
        #             label=InstanceStepDataLabel.EMB_MODEL,
        #             value=embedding.info.name,
        #         ),
        #         InstancePipelineStepData(
        #             label=InstanceStepDataLabel.EMB_MODEL_DIM,
        #             value=embedding.info.dimensions,
        #         ),
        #     ],
        # )
    end_time = time.time()
    print("Qdrant insert time " + str(end_time - start_time))


def create_embedding(input, embedding_model, depth=0):
    if depth > 10:
        raise Exception("Too many retries")
    try:
        time.sleep((5 * depth) + (6 / 1000))
        response = openai.embeddings.create(input=input, model=embedding_model)
        return response
    except Exception as e:
        print(e)
        print(f"Depth: {depth}")
        return create_embedding(input, embedding_model, depth=depth + 1)
