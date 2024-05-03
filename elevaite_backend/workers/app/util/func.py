import json
import ntpath
from typing import List
import redis
from sqlalchemy.orm import Session

from elevaitedb.crud import (
    instance as instance_crud,
    project as project_crud,
    dataset as dataset_crud,
)
from elevaitedb.schemas.instance import (
    InstancePipelineStepData,
    InstanceStatus,
    InstanceUpdate,
    InstanceChartData,
    PipelineStepStatus,
    InstancePipelineStepStatusUpdate,
    chart_data_from_redis,
)
from elevaitedb.util import func as util_func


def set_redis_stats(r: redis.Redis, instance_id: str, count, avg_size, size):
    _data = {
        "total_items": count,
        "ingested_items": 0,
        "ingested_size": 0,
        "ingested_chunks": 0,
        "avg_size": avg_size,
        "total_size": size,
    }

    r.json().set(instance_id, ".", _data)


def set_instance_running(db: Session, application_id: int, instance_id: str):
    instance_crud.update_instance(
        db=db,
        application_id=application_id,
        instance_id=instance_id,
        updateInstanceDTO=InstanceUpdate(status=InstanceStatus.RUNNING),
    )


def set_instance_completed(db: Session, application_id: int, instance_id: str):
    instance_crud.update_instance(
        db=db,
        application_id=application_id,
        instance_id=instance_id,
        updateInstanceDTO=InstanceUpdate(
            status=InstanceStatus.COMPLETED, endTime=util_func.get_iso_datetime()
        ),
    )


def set_pipeline_step_meta(
    db: Session, instance_id: str, step_id: str, meta: List[InstancePipelineStepData]
):
    instance_crud.update_pipeline_step(
        db=db,
        instance_id=instance_id,
        step_id=step_id,
        dto=InstancePipelineStepStatusUpdate(meta=meta),
    )


def set_pipeline_step_completed(db: Session, instance_id: str, step_id: str):
    instance_crud.update_pipeline_step(
        db=db,
        instance_id=instance_id,
        step_id=step_id,
        dto=InstancePipelineStepStatusUpdate(
            endTime=util_func.get_iso_datetime(),
            status=PipelineStepStatus.COMPLETED,
        ),
    )


def set_pipeline_step_running(db: Session, instance_id: str, step_id: str):
    instance_crud.update_pipeline_step(
        db=db,
        instance_id=instance_id,
        step_id=step_id,
        dto=InstancePipelineStepStatusUpdate(
            startTime=util_func.get_iso_datetime(),
            status=PipelineStepStatus.RUNNING,
        ),
    )


def set_instance_chart_data(r: redis.Redis, db: Session, instance_id: str):
    _res = r.json().get(name=instance_id)

    res = json.loads(json.dumps(_res))

    instance_crud.update_instance_chart_data(
        db=db, instance_id=instance_id, updateChartData=chart_data_from_redis(res)
    )


def get_repo_name(db: Session, project_id: str, dataset_id: str) -> str:
    _project_name = project_crud.get_project_name(db=db, project_id=project_id)
    dataset = dataset_crud.get_dataset_by_id(db=db, dataset_id=dataset_id)
    if dataset is None:
        raise Exception("Dataset not found")
    project_name = util_func.to_kebab_case(_project_name)
    dataset_name = util_func.to_kebab_case(dataset.name)
    repo_name = project_name + "-" + dataset_name
    return repo_name


def path_leaf(path: str) -> str:
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)
