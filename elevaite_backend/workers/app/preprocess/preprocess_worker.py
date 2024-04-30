import asyncio
from datetime import datetime
import io
import json
import os
from pprint import pprint
import sys
import threading
from elasticsearch import Elasticsearch
import lakefs
import redis
from unstructured.partition.html import partition_html
from unstructured.chunking.title import chunk_by_title

from elevaitedb.db.database import SessionLocal
from elevaitedb.crud import (
    instance as instance_crud,
    pipeline as pipeline_crud,
    collection as collection_crud,
    dataset as dataset_crud,
)
from elevaitedb.util import func as util_func
from elevaitedb.util.s3url import S3Url
from elevaitedb.schemas.instance import (
    InstancePipelineStepData,
    InstanceStatus,
    InstanceStepDataLabel,
    InstanceUpdate,
    InstanceChartData,
)
from elevaitedb.util.logger import ESLogger

from .preprocess import get_file_elements_from_url, get_file_elements_internal
from . import vectordb

from ..util.func import (
    get_repo_name,
    path_leaf,
    set_instance_running,
    set_pipeline_step_completed,
    set_pipeline_step_meta,
    set_redis_stats,
    set_pipeline_step_running,
    set_instance_completed,
    set_instance_chart_data,
)
from ..interfaces import PreProcessForm


def wrap_async_func(_data: PreProcessForm):
    asyncio.run(preprocess(_data))


def preprocess_callback(ch, method, properties, body):
    _data = json.loads(body)

    print(f" [x] Received {_data}")

    _formData = PreProcessForm(
        **_data["dto"],
        instanceId=_data["id"],
        applicationId=_data["application_id"],
    )

    t = threading.Thread(target=wrap_async_func, args=(_formData,))
    t.start()


async def preprocess(data: PreProcessForm) -> None:
    LAKEFS_ACCESS_KEY_ID = os.getenv("LAKEFS_ACCESS_KEY_ID")
    if LAKEFS_ACCESS_KEY_ID is None:
        raise Exception("LAKEFS_ACCESS_KEY_ID is null")
    LAKEFS_SECRET_ACCESS_KEY = os.getenv("LAKEFS_SECRET_ACCESS_KEY")
    if LAKEFS_SECRET_ACCESS_KEY is None:
        raise Exception("LAKEFS_SECRET_ACCESS_KEY is null")
    LAKEFS_ENDPOINT_URL = os.getenv("LAKEFS_ENDPOINT_URL")
    if LAKEFS_ENDPOINT_URL is None:
        raise Exception("LAKEFS_ENDPOINT_URL is null")
    REDIS_HOST = os.getenv("REDIS_HOST")
    if REDIS_HOST is None:
        raise Exception("REDIS_HOST is null")
    _REDIS_PORT = os.getenv("REDIS_PORT")
    if _REDIS_PORT is None:
        raise Exception("REDIS_PORT is null")
    try:
        REDIS_PORT = int(_REDIS_PORT)
    except ValueError:
        print("REDIS_PORT must be an integer")
    REDIS_USERNAME = os.getenv("REDIS_USERNAME")
    if REDIS_USERNAME is None:
        raise Exception("REDIS_USERNAME is null")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    if REDIS_PASSWORD is None:
        raise Exception("REDIS_PASSWORD is null")
    ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
    if ELASTIC_PASSWORD is None:
        raise Exception("ELASTIC_PASSWORD is null")
    ELASTIC_SSL_FINGERPRINT = os.getenv("ELASTIC_SSL_FINGERPRINT")
    if ELASTIC_SSL_FINGERPRINT is None:
        raise Exception("ELASTIC_SSL_FINGERPRINT is null")
    ELASTIC_HOST = os.getenv("ELASTIC_HOST")
    if ELASTIC_HOST is None:
        raise Exception("ELASTIC_HOST is null")
    try:

        db = SessionLocal()

        set_instance_running(
            db=db, application_id=data.applicationId, instance_id=data.instanceId
        )

        clt = lakefs.Client(
            host=LAKEFS_ENDPOINT_URL,
            username=LAKEFS_ACCESS_KEY_ID,
            password=LAKEFS_SECRET_ACCESS_KEY,
        )

        r = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            username=REDIS_USERNAME,
            password=REDIS_PASSWORD,
        )

        r.ping()

        # Create the client instance
        es = Elasticsearch(
            ELASTIC_HOST,
            ssl_assert_fingerprint=ELASTIC_SSL_FINGERPRINT,
            basic_auth=("elastic", ELASTIC_PASSWORD),
        )

        if not es.ping():
            raise Exception("Could not connect to ElasticSearch")

        logger = ESLogger(key=data.instanceId)
        logger.info(message="Initialized worker")

        if data.datasetId is None:
            raise Exception("No datasetId recieved")

        repo = None

        repo_name = get_repo_name(
            db=db, dataset_id=data.datasetId, project_id=data.projectId
        )

        for _repo in lakefs.repositories(client=clt):
            if _repo.id == repo_name:
                repo = _repo
                break
        if repo is None:
            raise Exception("LakeFS Repository not found")

        _version = (
            data.datasetVersion
            if data.datasetVersion
            else dataset_crud.get_max_version_of_dataset(
                db=db, datasetId=data.datasetId
            )
        )

        dataset_version = dataset_crud.get_dataset_version(
            db=db, datasetId=data.datasetId, version=_version
        )
        if dataset_version is None:
            raise Exception("Dataset Version not found.")
        ref = lakefs.Reference(repo.id, dataset_version.commitId, client=clt)

        logger.info(message="Dataset found")

        _collection = collection_crud.get_collection_by_id(
            db=db, collectionId=data.collectionId
        )
        collection_name = util_func.to_kebab_case(_collection.name)

        count = 0
        size = 0
        for o in ref.objects():
            count += 1
            size += o.size_bytes  # type: ignore | Typing seems to be wrong

        # size = sum(1 for _ in src_bucket.objects.all())

        avg_size = 0

        try:
            avg_size = size / count
        except:
            avg_size = 0

        set_redis_stats(
            r=r, instance_id=data.instanceId, count=count, avg_size=avg_size, size=size
        )

        _pipeline = pipeline_crud.get_pipeline_by_id(db, data.selectedPipelineId)
        _entry_step = None
        _first_step = None
        _second_step = None
        _final_step = None

        for s in _pipeline.steps:
            if s.id == _pipeline.entry:
                _entry_step = s
                break

        if _entry_step is None:
            raise Exception("Pipeline Entry step not found in steps")

        for s in _pipeline.steps:
            if _entry_step.id in s.previousStepIds:  # type: ignore | I mean... it works?
                _first_step = s
                break

        if _first_step is None:
            raise Exception("Pipeline first step not found in steps")

        for s in _pipeline.steps:
            if _first_step.id in s.previousStepIds:  # type: ignore | I mean... it works?
                _second_step = s
                break

        if _second_step is None:
            raise Exception("Pipeline second step not found in steps")

        for s in _pipeline.steps:
            if s.id == _pipeline.exit:
                _final_step = s
                break

        if _final_step is None:
            raise Exception("Pipeline Exit step not found in steps")

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=str(_entry_step.id)
        )

        set_pipeline_step_meta(
            db=db,
            instance_id=data.instanceId,
            step_id=str(_entry_step.id),
            meta=[
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.REPO_NAME, value=repo_name
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.DATASET_VERSION,
                    value=dataset_version.version,
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.INGEST_DATE,
                    value=dataset_version.createDate.isoformat(),
                ),
            ],
        )

        set_pipeline_step_running(
            db=db, instance_id=data.instanceId, step_id=str(_first_step.id)
        )

        logger.info(message="Completed Initialization")

        chunks_as_json = []
        page_as_json = []
        findex = 0
        logger.info(message="Starting file segmentation")
        total_chunk_size = 0
        avg_chunk_size = 0
        max_chunk_size = 0
        num_chunk = 0
        for object in ref.objects():
            # print(object)
            object.physical_address  # type: ignore | Typing seems to be wrong
            with ref.object(object.path).reader(pre_sign=False, mode="rb") as fd:
                r.json().set(data.instanceId, ".current_doc", path_leaf(object.path))
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
                r.json().numincrby(data.instanceId, ".ingested_size", object.size_bytes)  # type: ignore | Typing seems to be wrong
                r.json().numincrby(data.instanceId, ".ingested_items", 1)
                r.json().numincrby(
                    data.instanceId, ".ingested_chunks", len(file_chunks)
                )
            findex += 1
            if findex % 10 == 0:
                # print(findex)

                set_pipeline_step_meta(
                    db=db,
                    instance_id=data.instanceId,
                    step_id=str(_first_step.id),
                    meta=[
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.REPO_NAME, value=repo_name
                        ),
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.DATASET_VERSION,
                            value=dataset_version.version,
                        ),
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.INGEST_DATE,
                            value=dataset_version.createDate.isoformat(),
                        ),
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.TOTAL_CHUNK_SIZE,
                            value=total_chunk_size,
                        ),
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.AVG_CHUNK_SIZE,
                            value=avg_chunk_size,
                        ),
                        InstancePipelineStepData(
                            label=InstanceStepDataLabel.LRGST_CHUNK_SIZE,
                            value=max_chunk_size,
                        ),
                    ],
                )
        logger.info(message="Completed file segmentation")

        set_instance_chart_data(r=r, db=db, instance_id=data.instanceId)

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=str(_first_step.id)
        )

        set_pipeline_step_meta(
            db=db,
            instance_id=data.instanceId,
            step_id=str(_first_step.id),
            meta=[
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.REPO_NAME, value=repo_name
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.DATASET_VERSION,
                    value=dataset_version.version,
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.INGEST_DATE,
                    value=dataset_version.createDate.isoformat(),
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.TOTAL_CHUNK_SIZE,
                    value=total_chunk_size,
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.AVG_CHUNK_SIZE,
                    value=avg_chunk_size,
                ),
                InstancePipelineStepData(
                    label=InstanceStepDataLabel.LRGST_CHUNK_SIZE,
                    value=max_chunk_size,
                ),
            ],
        )

        set_pipeline_step_running(
            db=db, instance_id=data.instanceId, step_id=str(_second_step.id)
        )

        # print("Number of chunks " + str(len(chunks_as_json)))
        # payloads = json.load(chunks_as_json)
        logger.info(message="Recreating QDrant Collection")
        await vectordb.recreate_collection(
            collection_name=collection_name,
            size=(
                data.embedding_info.dimensions
                if data.embedding_info is not None
                else 1536
            ),
        )
        logger.info(message="Starting segment vectorization")
        await vectordb.insert_records(
            db=db,
            instance_id=data.instanceId,
            step_id=str(_second_step.id),
            collection=collection_name,
            payload_with_contents=chunks_as_json,
            emb_info=data.embedding_info,
        )
        logger.info(message="Completed segment vectorization")

        set_instance_chart_data(r=r, db=db, instance_id=data.instanceId)

        set_instance_completed(
            db=db, application_id=data.applicationId, instance_id=data.instanceId
        )

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=str(_second_step.id)
        )

        set_pipeline_step_running(
            db=db, instance_id=data.instanceId, step_id=str(_final_step.id)
        )

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=str(_final_step.id)
        )
        logger.info(message="Worker completed pre-process pipeline")
    except Exception as e:
        print("Error")
        print(e)
        logger.error(message="Error encountered, aborting pipeline")
        logger.error(message=str(e))
        instance_crud.update_instance(
            db,
            data.applicationId,
            data.instanceId,
            InstanceUpdate(
                status=InstanceStatus.FAILED,
                endTime=util_func.get_iso_datetime(),
                comment=str(e),
            ),
        )
