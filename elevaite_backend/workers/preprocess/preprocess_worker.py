import asyncio
from datetime import datetime
import json
import os
from pprint import pprint
import threading
from elasticsearch import Elasticsearch
import lakefs
import redis
from unstructured.partition.html import partition_html
from unstructured.chunking.title import chunk_by_title

from .preprocess import get_file_elements_internal
from . import vectordb

from elevaitedb.db.database import SessionLocal
from elevaitedb.crud import (
    project as project_crud,
    instance as instance_crud,
    application as application_crud,
    pipeline as pipeline_crud,
)
from elevaitedb.util import func as util_func
from elevaitedb.util.s3url import S3Url
from elevaitedb.schemas.instance import (
    InstanceStatus,
    InstanceUpdate,
    InstanceChartData,
    InstancePipelineStepStatusUpdate,
)
from elevaitedb.schemas.pipeline import PipelineStepStatus


class PreProcessForm:
    creator: str
    name: str
    projectId: str
    version: str | None
    parent: str | None
    outputURI: str | None
    datasetId: str | None
    selectedPipelineId: str
    configurationName: str
    isTemplate: bool
    datasetVersion: str | None
    queue: str
    maxIdleTime: str
    instanceId: str
    applicationId: int

    def __init__(
        self,
        creator: str,
        name: str,
        projectId: str,
        version: str | None,
        parent: str | None,
        outputURI: str | None,
        datasetId: str | None,
        selectedPipelineId: str,
        configurationName: str,
        isTemplate: bool,
        type: str,
        datasetVersion: str | None,
        queue: str,
        maxIdleTime: str,
        instanceId: str,
        applicationId: int,
    ) -> None:
        self.creator = creator
        self.name = name
        self.projectId = projectId
        self.version = version
        self.parent = parent
        self.outputURI = outputURI
        self.datasetId = datasetId
        self.selectedPipelineId = selectedPipelineId
        self.configurationName = configurationName
        self.isTemplate = isTemplate
        self.datasetVersion = datasetVersion
        self.queue = queue
        self.maxIdleTime = maxIdleTime
        self.instanceId = instanceId
        self.applicationId = applicationId


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

    repo = None

    _project = project_crud.get_project_by_id(db, data.projectId)
    project_name = util_func.to_kebab_case(_project.name)

    for _repo in lakefs.repositories(client=clt):
        if _repo.id == project_name:
            repo = _repo

    count = 0
    size = 0
    for o in repo.branch("main").objects():
        count += 1
        size += o.size_bytes

    # size = sum(1 for _ in src_bucket.objects.all())

    avg_size = 0

    try:
        avg_size = size / count
    except:
        avg_size = 0

    _data = {
        "total_items": count,
        "ingested_items": 0,
        "ingested_size": 0,
        "avg_size": avg_size,
        "total_size": size,
        "ingested_chunks": 0,
    }

    r.json().set(data.instanceId, ".", _data)

    _application = application_crud.get_application_by_id(db, data.applicationId)
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

    _instance = instance_crud.get_instance_by_id(
        db, data.applicationId, data.instanceId
    )
    instance_crud.update_instance(
        db,
        data.applicationId,
        data.instanceId,
        InstanceUpdate(status=InstanceStatus.RUNNING),
    )
    instance_crud.update_pipeline_step(
        db,
        data.instanceId,
        _entry_step.id,
        InstancePipelineStepStatusUpdate(
            status=PipelineStepStatus.COMPLETED, endTime=util_func.get_iso_datetime()
        ),
    )
    instance_crud.update_pipeline_step(
        db,
        data.instanceId,
        _first_step.id,
        InstancePipelineStepStatusUpdate(
            status=PipelineStepStatus.RUNNING, startTime=util_func.get_iso_datetime()
        ),
    )

    chunks_as_json = []
    page_as_json = []
    findex = 0
    try:
        for object in repo.branch("main").objects():
            with repo.branch("main").object(object.path).reader(pre_sign=False) as fd:
                # while fd.tell() < file_size:
                #     print(fd.read(10))
                #     fd.seek(10, os.SEEK_CUR)
                file_chunks = get_file_elements_internal(
                    file=fd.read(), filepath=object.path
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

        res = r.json().get(data.instanceId)

        instance_crud.update_instance_chart_data(
            db,
            data.instanceId,
            InstanceChartData(
                totalItems=res["total_items"],
                ingestedItems=res["ingested_items"],
                avgSize=res["avg_size"],
                totalSize=res["total_size"],
                ingestedSize=res["ingested_size"],
                ingestedChunks=res["ingested_chunks"],
            ),
        )

        instance_crud.update_pipeline_step(
            db,
            data.instanceId,
            _first_step.id,
            InstancePipelineStepStatusUpdate(
                status=PipelineStepStatus.COMPLETED,
                endTime=util_func.get_iso_datetime(),
            ),
        )

        instance_crud.update_pipeline_step(
            db,
            data.instanceId,
            _second_step.id,
            InstancePipelineStepStatusUpdate(
                status=PipelineStepStatus.RUNNING,
                startTime=util_func.get_iso_datetime(),
            ),
        )

        #     es.update(
        #         index="application",
        #         id=data.applicationId,
        #         body=json.dumps({"doc": {"instances": instances}}, default=vars),
        #     )

        #     # Save the chunks_as_json.json on lakefs

        # pprint(chunks_as_json)
        print("Number of chunks " + str(len(chunks_as_json)))
        # payloads = json.load(chunks_as_json)
        await vectordb.recreate_collection(collection=project_name)
        await vectordb.insert_records(
            collection=project_name, payload_with_contents=chunks_as_json
        )

        res = r.json().get(data.instanceId)

        instance_crud.update_instance_chart_data(
            db,
            data.instanceId,
            InstanceChartData(
                totalItems=res["total_items"],
                ingestedItems=res["ingested_items"],
                avgSize=res["avg_size"],
                totalSize=res["total_size"],
                ingestedSize=res["ingested_size"],
                ingestedChunks=res["ingested_chunks"],
            ),
        )
        instance_crud.update_instance(
            db,
            data.applicationId,
            data.instanceId,
            InstanceUpdate(status=InstanceStatus.COMPLETED),
        )
        instance_crud.update_pipeline_step(
            db,
            data.instanceId,
            _second_step.id,
            InstancePipelineStepStatusUpdate(
                status=PipelineStepStatus.COMPLETED,
                endTime=util_func.get_iso_datetime(),
            ),
        )
        instance_crud.update_pipeline_step(
            db,
            data.instanceId,
            _final_step.id,
            InstancePipelineStepStatusUpdate(
                status=PipelineStepStatus.COMPLETED,
                endTime=util_func.get_iso_datetime(),
                startTime=util_func.get_iso_datetime(),
            ),
        )
    except Exception as e:
        print("Error")
        print(e)
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
