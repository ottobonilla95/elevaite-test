"Prebuilt workflow, preprocessing documents"

import sys
import time
from typing import Any, Dict, List
from elevaite_client.connectors.embeddings import EmbeddingInfo, EmbeddingType
from elevaite_client.connectors.qdrant import get_qdrant_connection
from flytekit import task, workflow
from pydantic import BaseModel
from unstructured.partition.html import partition_html
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Element

from elevaite_client.rpc.client import RPCClient, RPCLogger, RedisRPCHelper
from elevaite_client.rpc.interfaces import (
    GetCollectionNameInput,
    RepoNameInput,
    SetInstanceChartDataInput,
    MaxDatasetVersionInput,
    GetDatasetVersionCommitIdInput,
)
from elevaite_client.connectors import lakefs as lakefs_conn, embeddings, qdrant
from elevaite_client.connectors.embeddings import ChunkAsJson
from ..util.func import get_secrets, path_leaf


class DocumentPreprocessData(BaseModel):
    projectId: str
    instanceId: str
    collectionId: str
    datasetId: str
    datasetVersion: int | None
    embedding_info: EmbeddingInfo = EmbeddingInfo(
        inference_url=None,
        name="text-embedding-ada-002",
        type=EmbeddingType.OPENAI,
        dimensions=1536,
    )
    queue: str
    maxIdleTime: str


def get_filename(filepath):
    return filepath.split("/")[-1]


def get_document_title(source):
    return source.split(".")[0]


def get_chunk_as_json(source: str, chunk: Element) -> ChunkAsJson:
    chunk_with_no_tabs = str(chunk).replace("\t", "")
    page_metadata = ChunkAsJson(metadata={}, page_content="")
    page_metadata.metadata["source"] = source
    page_metadata.metadata["document_title"] = get_document_title(source)
    page_metadata.metadata["page_title"] = page_metadata.metadata["document_title"]

    page_content_title = []
    if page_metadata.metadata["document_title"]:
        page_content_title.append(str(page_metadata.metadata["document_title"]))
    if page_metadata.metadata["page_title"]:
        page_content_title.append(str(page_metadata.metadata["page_title"]))
    content_title = " ".join(page_content_title)
    page_metadata.page_content = content_title + " " + str(chunk_with_no_tabs)
    return page_metadata


def get_file_elements_internal(
    file, filepath, content_type: str | None = None
) -> List[ChunkAsJson]:
    elements = partition_html(file=file, content_type=content_type)
    # elements = partition(file=file, content_type=content_type)
    source = get_filename(filepath)
    chunks = chunk_by_title(elements=elements, max_characters=2000)
    chunks_as_json: List[ChunkAsJson] = []
    for idx, chunk in enumerate(chunks):
        chunk_as_json = get_chunk_as_json(source=source, chunk=chunk)
        chunks_as_json.append(chunk_as_json)
    return chunks_as_json


@task
def segment_documents(_data: Dict[str, str | int | bool | Any]) -> List[ChunkAsJson]:
    "segmenting"
    data = DocumentPreprocessData.parse_obj(_data)
    secrets = get_secrets()
    LAKEFS_ACCESS_KEY_ID = secrets.LAKEFS_ACCESS_KEY_ID
    LAKEFS_SECRET_ACCESS_KEY = secrets.LAKEFS_SECRET_ACCESS_KEY
    LAKEFS_ENDPOINT_URL = secrets.LAKEFS_ENDPOINT_URL
    LAKEFS_STORAGE_NAMESPACE = secrets.LAKEFS_STORAGE_NAMESPACE
    rpc_client = RPCClient()
    r = RedisRPCHelper(key=data.instanceId, client=rpc_client)
    logger = RPCLogger(key=data.instanceId, client=rpc_client)

    repo_name = rpc_client.get_repo_name(
        RepoNameInput(dataset_id=data.datasetId, project_id=data.projectId)
    )

    dataset_version = (
        data.datasetVersion
        if data.datasetVersion is not None
        else rpc_client.get_max_version_of_dataset(
            input=MaxDatasetVersionInput(dataset_id=data.datasetId)
        )
    )

    commit_id = rpc_client.get_dataset_version_commit_id(
        input=GetDatasetVersionCommitIdInput(
            dataset_id=data.datasetId, version=dataset_version
        )
    )

    ref = lakefs_conn.get_lakefs_ref(
        repo_name=repo_name,
        commit_id=commit_id,
        options={
            "key_id": LAKEFS_ACCESS_KEY_ID,
            "secret_key": LAKEFS_SECRET_ACCESS_KEY,
            "endpoint": LAKEFS_ENDPOINT_URL,
            "namespace": LAKEFS_STORAGE_NAMESPACE,
        },
    )
    chunks_as_json: List[ChunkAsJson] = []
    findex = 0
    logger.info(msg="Starting file segmentation")

    total_chunk_size = 0
    avg_chunk_size = 0
    max_chunk_size = 0
    num_chunk = 0
    for object in ref.objects():
        # print(object)
        object.physical_address  # type: ignore | Typing seems to be wrong
        with ref.object(object.path).reader(pre_sign=False, mode="rb") as fd:
            r.set_value(path=".currentFile", obj=path_leaf(object.path))
            input = fd.read()
            file_chunks = get_file_elements_internal(
                file=input,
                filepath=object.path,
                content_type=object.content_type,  # type: ignore | Typing seems to be wrong
            )
            chunks_as_json.extend(file_chunks)
            for chunk in file_chunks:
                _chunk_size = sys.getsizeof(chunk.page_content)
                num_chunk += 1
                total_chunk_size += _chunk_size
                avg_chunk_size = str(total_chunk_size / num_chunk)
                if _chunk_size > max_chunk_size:
                    max_chunk_size = _chunk_size
            r.set_value(path=".ingested_size", obj=object.size_bytes)  # type: ignore
            r.set_value(path=".ingested_items", obj=1)
            r.set_value(path=".ingested_chunks", obj=len(file_chunks))

        findex += 1
        # if findex % 10 == 0:
        #     print(findex)

        #     set_pipeline_step_meta(
        #         db=self.db,
        #         instance_id=self.data.instanceId,
        #         step_id=self.step_id,
        #         meta=[
        #             InstancePipelineStepData(
        #                 label=InstanceStepDataLabel.REPO_NAME, value=repo_name
        #             ),
        #             InstancePipelineStepData(
        #                 label=InstanceStepDataLabel.DATASET_VERSION,
        #                 value=dataset_version.version,
        #             ),
        #             InstancePipelineStepData(
        #                 label=InstanceStepDataLabel.INGEST_DATE,
        #                 value=dataset_version.createDate.isoformat(),
        #             ),
        #             InstancePipelineStepData(
        #                 label=InstanceStepDataLabel.TOTAL_CHUNK_SIZE,
        #                 value=total_chunk_size,
        #             ),
        #             InstancePipelineStepData(
        #                 label=InstanceStepDataLabel.AVG_CHUNK_SIZE,
        #                 value=avg_chunk_size,
        #             ),
        #             InstancePipelineStepData(
        #                 label=InstanceStepDataLabel.LRGST_CHUNK_SIZE,
        #                 value=max_chunk_size,
        #             ),
        #         ],
        #     )

    logger.info(msg="Completed file segmentation")

    rpc_client.set_instance_chart_data(
        input=SetInstanceChartDataInput(instance_id=data.instanceId)
    )

    # set_pipeline_step_completed(
    #     db=self.db, instance_id=self.data.instanceId, step_id=self.step_id
    # )

    # set_pipeline_step_meta(
    #     db=self.db,
    #     instance_id=self.data.instanceId,
    #     step_id=self.step_id,
    #     meta=[
    #         InstancePipelineStepData(
    #             label=InstanceStepDataLabel.REPO_NAME, value=repo_name
    #         ),
    #         InstancePipelineStepData(
    #             label=InstanceStepDataLabel.DATASET_VERSION,
    #             value=dataset_version.version,
    #         ),
    #         InstancePipelineStepData(
    #             label=InstanceStepDataLabel.INGEST_DATE,
    #             value=dataset_version.createDate.isoformat(),
    #         ),
    #         InstancePipelineStepData(
    #             label=InstanceStepDataLabel.TOTAL_CHUNK_SIZE,
    #             value=total_chunk_size,
    #         ),
    #         InstancePipelineStepData(
    #             label=InstanceStepDataLabel.AVG_CHUNK_SIZE,
    #             value=avg_chunk_size,
    #         ),
    #         InstancePipelineStepData(
    #             label=InstanceStepDataLabel.LRGST_CHUNK_SIZE,
    #             value=max_chunk_size,
    #         ),
    #     ],
    # )
    return chunks_as_json


@task
def vectorize_segments(
    _data: Dict[str, str | int | bool | Any], payload_with_contents: List[ChunkAsJson]
):
    rpc_client = RPCClient()
    data = DocumentPreprocessData.parse_obj(_data)
    logger = RPCLogger(key=data.instanceId, client=rpc_client)
    collection_name = rpc_client.get_collection_name(
        input=GetCollectionNameInput(collection_id=data.collectionId)
    )
    payloads: List[Dict[str, Any]] = []
    vectors: List[List[float]] = []
    ids: List[qdrant.ExtendedPointId] = []

    total_token_size = 0
    avg_token_size = 0
    max_token_size = 0
    min_token_size = 2 ^ 32 - 1
    p_index = 0

    qdrant_client = get_qdrant_connection()
    logger.info(msg="Starting file segmentation")
    start_time = time.time()

    _embeddings = embeddings.embed_documents(
        payloads_with_content=payload_with_contents, info=data.embedding_info
    )

    for embedding in _embeddings:
        p_index += 1
        embedding.token_size
        if embedding.token_size > max_token_size:
            max_token_size = embedding.token_size
        if embedding.token_size < min_token_size:
            min_token_size = embedding.token_size
        total_token_size += embedding.token_size
        avg_token_size = total_token_size / p_index

        payloads.append(embedding.payload.dict())
        vectors.extend(embedding.vectors)
        ids.append(embedding.id)
        if len(payloads) >= 64:
            qdrant.upsert_records(
                connection=qdrant_client,
                collection_name=collection_name,
                ids=ids,
                payloads=payloads,
                vectors=vectors,
            )
            payloads.clear()
            vectors.clear()
            ids.clear()

    if len(payloads) > 0:
        qdrant.upsert_records(
            connection=qdrant_client,
            collection_name=collection_name,
            ids=ids,
            payloads=payloads,
            vectors=vectors,
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
    logger.info(msg="Completed file segmentation")
    logger.info(msg="Qdrant insert time " + str(end_time - start_time))


@workflow
def document_preprocess_workflow(data: Dict[str, str | int | bool | Any]):
    vectorize_segments(_data=data, payload_with_contents=segment_documents(_data=data))  # type: ignore
