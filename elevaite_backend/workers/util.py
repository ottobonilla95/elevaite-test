import redis
from sqlalchemy.orm import Session

from elevaitedb.crud import (
    instance as instance_crud,
    project as project_crud,
    dataset as dataset_crud,
)
from elevaitedb.schemas.instance import (
    InstanceStatus,
    InstanceUpdate,
    InstanceChartData,
    PipelineStepStatus,
    InstancePipelineStepStatusUpdate,
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


def set_instance_running(db: Session, application_id: str, instance_id: str):
    instance_crud.update_instance(
        db=db,
        application_id=application_id,
        instance_id=instance_id,
        updateInstanceDTO=InstanceUpdate(status=InstanceStatus.RUNNING),
    )


def set_instance_completed(db: Session, application_id: str, instance_id: str):
    instance_crud.update_instance(
        db=db,
        application_id=application_id,
        instance_id=instance_id,
        updateInstanceDTO=InstanceUpdate(
            status=InstanceStatus.COMPLETED, endTime=util_func.get_iso_datetime()
        ),
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
            endTime=util_func.get_iso_datetime(),
            status=PipelineStepStatus.RUNNING,
        ),
    )


def set_instance_chart_data(r: redis.Redis, db: Session, instance_id: str):
    res = r.json().get(name=instance_id)

    instance_crud.update_instance_chart_data(
        db=db,
        instance_id=instance_id,
        updateChartData=InstanceChartData(
            totalItems=res["total_items"],
            ingestedItems=res["ingested_items"],
            avgSize=res["avg_size"],
            totalSize=res["total_size"],
            ingestedSize=res["ingested_size"],
            ingestedChunks=res["ingested_chunks"],
        ),
    )


def get_repo_name(db: Session, project_id: str, dataset_id: str) -> str:
    _project_name = project_crud.get_project_name(db=db, project_id=project_id)
    project_name = util_func.to_kebab_case(_project_name)
    dataset = dataset_crud.get_dataset_by_id(db=db, dataset_id=dataset_id)
    if dataset is None:
        raise Exception("Dataset not found")
    dataset_name = util_func.to_kebab_case(dataset.name)
    repo_name = project_name + "-" + dataset_name
    return repo_name
