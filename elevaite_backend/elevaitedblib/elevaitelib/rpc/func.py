import json
import os
from typing import Any
from dotenv import load_dotenv
from elevaitelib.schemas.dataset import DatasetVersionCreate
from ..util.logger import ESLogger
import redis
from sqlalchemy.orm import Session

from ..orm.db.database import SessionLocal
from ..orm.crud import (
    instance as instance_crud,
    project as project_crud,
    dataset as dataset_crud,
)
from ..schemas.instance import (
    InstancePipelineStepData,
    InstanceStatus,
    InstanceUpdate,
    InstanceChartData,
    PipelineStepStatus,
    InstancePipelineStepStatusUpdate,
    chart_data_from_redis,
)
from ..util import func as util_func
from elevaite_client.rpc.interfaces import (
    InstanceStatusInput,
    InstanceStepMetaInput,
    LogInfo,
    PipelineStepStatusInput,
    RepoNameInput,
    SetInstanceChartDataInput,
    SetRedisStatsInput,
    SetRedisValueInput,
    MaxDatasetVersionInput,
    CreateDatasetVersionInput,
)


def _get_redis() -> redis.Redis:
    load_dotenv()
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
    # if REDIS_USERNAME is None:
    #     raise Exception("REDIS_USERNAME is null")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    # if REDIS_PASSWORD is None:
    #     raise Exception("REDIS_PASSWORD is null")

    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
    )
    try:
        r.ping()
    except Exception as e:
        print("Could not connect to Redis")
    return r


def set_redis_stats(payload: Any, r: redis.Redis = _get_redis()):
    input = SetRedisStatsInput(**payload)
    _data = {
        "total_items": input.count,
        "ingested_items": 0,
        "ingested_size": 0,
        "ingested_chunks": 0,
        "avg_size": input.avg_size,
        "total_size": input.size,
    }

    r.json().set(input.instance_id, ".", _data)
    r.close()
    return ""


def set_redis_value(payload: Any, r: redis.Redis = _get_redis()):
    input = SetRedisValueInput.parse_obj(payload)
    r.json().set(name=input.name, path=input.path, obj=input.obj)
    return ""


def set_instance_running(payload: Any, db: Session = SessionLocal()):
    input = InstanceStatusInput(**payload)
    instance_crud.update_instance(
        db=db,
        application_id=input.application_id,
        instance_id=input.instance_id,
        updateInstanceDTO=InstanceUpdate(status=InstanceStatus.RUNNING),
    )
    db.close()
    return ""


def set_instance_completed(payload: Any, db: Session = SessionLocal()):
    input = InstanceStatusInput(**payload)
    instance_crud.update_instance(
        db=db,
        application_id=input.application_id,
        instance_id=input.instance_id,
        updateInstanceDTO=InstanceUpdate(
            status=InstanceStatus.COMPLETED, endTime=util_func.get_iso_datetime()
        ),
    )
    db.close()
    return ""


def set_pipeline_step_meta(payload: Any, db: Session = SessionLocal()):
    input = InstanceStepMetaInput(**payload)
    instance_crud.update_pipeline_step(
        db=db,
        instance_id=input.instance_id,
        step_id=input.step_id,
        dto=InstancePipelineStepStatusUpdate(
            meta=list(
                map(
                    lambda item: InstancePipelineStepData(
                        label=item.label, value=item.value
                    ),
                    input.meta,
                )
            )
        ),
    )
    db.close()
    return ""


def set_pipeline_step_completed(payload: Any, db: Session = SessionLocal()):
    input = PipelineStepStatusInput(**payload)
    instance_crud.update_pipeline_step(
        db=db,
        instance_id=input.instance_id,
        step_id=input.step_id,
        dto=InstancePipelineStepStatusUpdate(
            endTime=util_func.get_iso_datetime(),
            status=PipelineStepStatus.COMPLETED,
        ),
    )
    db.close()
    return ""


def set_pipeline_step_running(payload: Any, db: Session = SessionLocal()):
    input = PipelineStepStatusInput(**payload)
    instance_crud.update_pipeline_step(
        db=db,
        instance_id=input.instance_id,
        step_id=input.step_id,
        dto=InstancePipelineStepStatusUpdate(
            startTime=util_func.get_iso_datetime(),
            status=PipelineStepStatus.RUNNING,
        ),
    )
    db.close()
    return ""


def set_instance_chart_data(
    payload: Any, r: redis.Redis = _get_redis(), db: Session = SessionLocal()
):
    input = SetInstanceChartDataInput(**payload)
    _res = r.json().get(name=input.instance_id)

    res = json.loads(json.dumps(_res))

    instance_crud.update_instance_chart_data(
        db=db, instance_id=input.instance_id, updateChartData=chart_data_from_redis(res)
    )
    db.close()
    r.close()
    return ""


def get_repo_name(payload: Any, db: Session = SessionLocal()) -> str:
    input = RepoNameInput(**payload)
    _project_name = project_crud.get_project_name(db=db, project_id=input.project_id)
    dataset = dataset_crud.get_dataset_by_id(db=db, dataset_id=input.dataset_id)
    if dataset is None:
        raise Exception("Dataset not found")
    db.close()
    project_name = util_func.to_kebab_case(_project_name)
    dataset_name = util_func.to_kebab_case(dataset.name)
    repo_name = project_name + "-" + dataset_name
    return repo_name


def get_max_version_of_dataset(payload: Any, db: Session = SessionLocal()) -> str:
    input = MaxDatasetVersionInput(**payload)
    res = dataset_crud.get_max_version_of_dataset(db=db, datasetId=input.dataset_id)
    return str(res)


def create_dataset_version(payload: Any, db: Session = SessionLocal()) -> str:
    input = CreateDatasetVersionInput(**payload)
    res = dataset_crud.create_dataset_version(
        db=db,
        datasetId=input.dataset_id,
        dsvc=DatasetVersionCreate(commitId=input.ref_id, version=input.version),
    )
    return str(res)


def hello(payload: Any) -> Any:
    return json.dumps(payload)


def log_info(payload: Any):
    input = LogInfo.parse_obj(payload)
    logger = ESLogger(input.key)
    logger.info(input.msg)
    logger.destroy()
    return ""
