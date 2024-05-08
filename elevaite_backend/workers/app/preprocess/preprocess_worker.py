import asyncio
import json
import os
import threading
from elasticsearch import Elasticsearch
import redis

from elevaitedb.db.database import SessionLocal
from elevaitedb.crud import (
    instance as instance_crud,
    pipeline as pipeline_crud,
)
from elevaitedb.util import func as util_func
from elevaitedb.schemas.instance import (
    InstanceStatus,
    InstanceUpdate,
)
from elevaitedb.util.logger import ESLogger

from .steps.base_step import (
    STEP_REGISTRY,
    RESOURCE_REGISTRY,
    get_initialized_step,
    register_resource_registry,
)

from ..util.func import (
    set_instance_running,
    set_pipeline_step_completed,
    set_pipeline_step_running,
    set_instance_completed,
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
    global STEP_REGISTRY
    global RESOURCE_REGISTRY
    try:
        _instance_registry = register_resource_registry(instance_id=data.instanceId)

        db = SessionLocal()

        set_instance_running(
            db=db, application_id=data.applicationId, instance_id=data.instanceId
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

        entry_step_runner = get_initialized_step(
            data=data, db=db, logger=logger, r=r, step_id=_entry_step.id
        )
        await entry_step_runner.run()

        _step_runner_1 = get_initialized_step(
            data=data, db=db, logger=logger, r=r, step_id=_first_step.id
        )
        await _step_runner_1.run()

        _step_runner_2 = get_initialized_step(
            data=data, db=db, logger=logger, r=r, step_id=_second_step.id
        )

        await _step_runner_2.run()

        set_pipeline_step_running(
            db=db, instance_id=data.instanceId, step_id=str(_final_step.id)
        )

        set_pipeline_step_completed(
            db=db, instance_id=data.instanceId, step_id=str(_final_step.id)
        )

        set_instance_completed(
            db=db, application_id=data.applicationId, instance_id=data.instanceId
        )
        logger.info(message="Worker completed pre-process pipeline")
        db.close()
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
