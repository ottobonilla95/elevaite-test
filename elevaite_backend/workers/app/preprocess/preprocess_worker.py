import asyncio
from datetime import datetime
import io
import json
import os
from pprint import pprint
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
    InstanceStatus,
    InstanceUpdate,
    InstanceChartData,
)
from elevaitedb.util.logger import ESLogger

from .preprocess import get_file_elements_from_url, get_file_elements_internal
from . import vectordb

from ..util.func import (
    get_repo_name,
    set_instance_running,
    set_pipeline_step_completed,
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
        configurationName=_data["configurationName"],
    )

    t = threading.Thread(target=wrap_async_func, args=(_formData,))
    t.start()


async def preprocess(data: PreProcessForm) -> None:
    LAKEFS_ACCESS_KEY_ID = os.getenv("LAKEFS_ACCESS_KEY_ID")
    LAKEFS_SECRET_ACCESS_KEY = os.getenv("LAKEFS_SECRET_ACCESS_KEY")
    LAKEFS_ENDPOINT_URL = os.getenv("LAKEFS_ENDPOINT_URL")
    LAKEFS_STORAGE_NAMESPACE = os.getenv("LAKEFS_STORAGE_NAMESPACE")
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_USERNAME = os.getenv("REDIS_USERNAME")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
    ELASTIC_SSL_FINGERPRINT = os.getenv("ELASTIC_SSL_FINGERPRINT")
    ELASTIC_HOST = os.getenv("ELASTIC_HOST")

    db = SessionLocal()

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

    repo = None

    repo_name = get_repo_name(
        db=db, dataset_id=data.datasetId, project_id=data.projectId
    )

    for _repo in lakefs.repositories(client=clt):
        if _repo.id == repo_name:
            repo = _repo

    _version = (
        data.datasetVersion
        if data.datasetVersion
        else dataset_crud.get_max_version_of_dataset(db=db, datasetId=data.datasetId)
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
        size += o.size_bytes

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

    for s in _pipeline.steps:
        if _entry_step.id in s.previousStepIds:
            _first_step = s
            break

    for s in _pipeline.steps:
        if _first_step.id in s.previousStepIds:
            _second_step = s
            break

    for s in _pipeline.steps:
        if s.id == _pipeline.exit:
            _final_step = s
            break

    set_instance_running(
        db=db, application_id=data.applicationId, instance_id=data.instanceId
    )

    set_pipeline_step_completed(
        db=db, instance_id=data.instanceId, step_id=_entry_step.id
    )

    set_pipeline_step_running(
        db=db, instance_id=data.instanceId, step_id=_first_step.id
    )

    logger.info(message="Completed Initialization")

    chunks_as_json = []
    page_as_json = []
    findex = 0
    try:
        logger.info(message="Starting file segmentation")
        for object in ref.objects():
            print(object)
            with ref.object(object.path).reader(pre_sign=False, mode="rb") as fd:
                # while fd.tell() < file_size:
                #     print(fd.read(10))
                #     fd.seek(10, os.SEEK_CUR)
                input = fd.read()
                file_chunks = get_file_elements_internal(
                    file=input,
                    filepath=object.path,
                    content_type=object.content_type,
                )
                chunks_as_json.extend(file_chunks)
                r.json().numincrby(data.instanceId, ".ingested_size", object.size_bytes)
                r.json().numincrby(data.instanceId, ".ingested_items", 1)
                r.json().numincrby(
                    data.instanceId, ".ingested_chunks", len(file_chunks)
                )
            findex += 1
            if findex % 10 == 0:
                print(findex)
        logger.info(message="Completed file segmentation")

        set_instance_chart_data(r=r, db=db, instance_id=data.instanceId)

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=_first_step.id
        )

        set_pipeline_step_running(
            db=db, instance_id=data.instanceId, step_id=_second_step.id
        )

        print("Number of chunks " + str(len(chunks_as_json)))
        # payloads = json.load(chunks_as_json)
        logger.info(message="Recreating QDrant Collection")
        await vectordb.recreate_collection(collection=collection_name)
        logger.info(message="Starting segment vectorization")
        await vectordb.insert_records(
            collection=collection_name, payload_with_contents=chunks_as_json
        )
        logger.info(message="Completed segment vectorization")

        set_instance_chart_data(r=r, db=db, instance_id=data.instanceId)

        set_instance_completed(
            db=db, application_id=data.applicationId, instance_id=data.instanceId
        )

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=_second_step.id
        )

        set_pipeline_step_running(
            db=db, instance_id=data.instanceId, step_id=_final_step.id
        )

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=_final_step.id
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
