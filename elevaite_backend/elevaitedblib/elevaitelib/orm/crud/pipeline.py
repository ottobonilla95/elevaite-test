from typing import Callable
from uuid import UUID

import boto3
from elevaitelib.schemas.pipeline import (
    PipelineCreate,
    PipelineScheduleCreate,
    PipelineTaskCreate,
    PipelineTaskUpdate,
    PipelineUpdate,
    PipelineVariableCreate,
    PipelineVariableUpdate,
)
from sqlalchemy.orm import Session, Query

from pipelines.utils import json2sagemaker

from ..db import models

# --- Pipeline Endpoints ---


def get_pipelines(db: Session, skip: int = 0, limit: int = 0) -> list[models.Pipeline]:
    return db.query(models.Pipeline).offset(skip).limit(limit).all()


def get_pipelines_of_project(
    db: Session,
    filter_function: Callable[[Query], Query],
    project_id: UUID,
    skip: int = 0,
    limit: int = 0,
) -> list[models.Pipeline]:
    query = db.query(models.Pipeline)

    if filter_function is not None:  # uncomment this when using validator
        query = filter_function(query)
    return (
        query.filter(models.Pipeline.projects.any(id=project_id))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_pipeline_by_id(
    db: Session,
    pipeline_id: UUID,
    filter_function: Callable[[Query], Query] | None = None,
) -> models.Pipeline:
    query = db.query(models.Pipeline)

    if filter_function is not None:  # uncomment this when using validator
        query = filter_function(query)
    return query.filter(models.Pipeline.id == pipeline_id).first()


def create_pipeline(db: Session, pipeline_dto: PipelineCreate) -> models.Pipeline:
    _pipeline = models.Pipeline(
        name=pipeline_dto.name,
        description=pipeline_dto.description,
        entrypoint=pipeline_dto.entrypoint,
    )
    db.add(_pipeline)
    db.commit()
    db.refresh(_pipeline)
    return _pipeline


def update_pipeline(
    db: Session, pipeline_id: UUID, dto: PipelineUpdate
) -> models.Pipeline:
    _pipeline = (
        db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).one()
    )
    if dto.name is not None:
        _pipeline.name = dto.name
    if dto.description is not None:
        _pipeline.description = dto.description
    if dto.entrypoint is not None:
        _pipeline.entrypoint = dto.entrypoint
    db.commit()
    db.refresh(_pipeline)
    return _pipeline


def delete_pipeline(db: Session, pipeline_id: UUID) -> models.Pipeline:
    _pipeline = (
        db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).one()
    )
    db.delete(_pipeline)
    db.commit()
    return _pipeline


def add_tasks_to_pipeline(
    db: Session, pipeline_id: str, task_id: str
) -> models.Pipeline:
    _pipeline = (
        db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).one()
    )
    _task = (
        db.query(models.PipelineTask).filter(models.PipelineTask.id == task_id).one()
    )
    _pipeline.tasks.append(_task)
    db.commit()
    db.refresh(_pipeline)
    return _pipeline


# --- Pipeline Schedule Endpoints ---


def create_pipeline_schedule(
    db: Session, pipeline_id: UUID, dto: PipelineScheduleCreate
) -> models.PipelineSchedule:
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).one()
    schedule = models.PipelineSchedule(**dto.dict())
    pipeline.schedule = schedule
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def get_pipeline_schedule(db: Session, pipeline_id: UUID) -> models.PipelineSchedule:
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).one()
    return pipeline.schedule


def update_pipeline_schedule(
    db: Session, pipeline_id: UUID, dto: PipelineScheduleCreate
) -> models.PipelineSchedule:
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).one()
    schedule = pipeline.schedule
    if schedule is None:
        schedule = models.PipelineSchedule(**dto.dict())
        pipeline.schedule = schedule
        db.add(schedule)
    else:
        schedule.frequency = dto.frequency
        schedule.time = dto.time
    db.commit()
    db.refresh(schedule)
    return schedule


def delete_pipeline_schedule(db: Session, pipeline_id: UUID) -> models.PipelineSchedule:
    pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).one()
    schedule = pipeline.schedule
    if schedule:
        db.delete(schedule)
        db.commit()
    return schedule


# --- Pipeline Task Endpoints ---


def get_pipeline_tasks(
    db: Session,
    filter_function: Callable[[Query], Query],
    skip: int = 0,
    limit: int = 0,
) -> list[models.PipelineTask]:
    query = db.query(models.PipelineTask)

    if filter_function is not None:  # uncomment this when using validator
        query = filter_function(query)
    return query.offset(skip).limit(limit).all()


def create_pipeline_task(db: Session, dto: PipelineTaskCreate) -> models.PipelineTask:
    _task = models.PipelineTask(name=dto.name, task_type=dto.task_type, src=dto.src)

    db.add(_task)
    db.commit()
    db.refresh(_task)
    return _task


def update_pipeline_task(
    db: Session, id: str, dto: PipelineTaskUpdate
) -> models.PipelineTask:
    _task = db.query(models.PipelineTask).filter(models.PipelineTask.id == id).one()
    if dto.dependencies:
        _task.dependencies = []
        for dep in dto.dependencies:
            __task = (
                db.query(models.PipelineTask)
                .filter(models.PipelineTask.id == dep.id)
                .one()
            )
            _task.dependencies.append(__task)

    if dto.input:
        _task.input = []
        for var in dto.input:
            _var = (
                db.query(models.PipelineVariable)
                .filter(models.PipelineVariable.name == var.name)
                .one()
            )
            _task.input.append(_var)

    if dto.output:
        _task.output = []
        for var in dto.output:
            _var = (
                db.query(models.PipelineVariable)
                .filter(models.PipelineVariable.name == var.name)
                .one()
            )
            _task.output.append(_var)

    if dto.name:
        _task.name = dto.name

    if dto.task_type:
        _task.task_type = dto.task_type

    if dto.src:
        _task.src = dto.src

    db.commit()
    db.refresh(_task)
    return _task


def delete_pipeline_task(db: Session, task_id: str) -> models.PipelineTask:
    _task = (
        db.query(models.PipelineTask).filter(models.PipelineTask.id == task_id).one()
    )
    db.delete(_task)
    db.commit()
    return _task


def add_dependency_to_task(
    db: Session, target_id: str, dep_id: str
) -> models.PipelineTask:
    _target = (
        db.query(models.PipelineTask).filter(models.PipelineTask.id == target_id).one()
    )
    _dep = db.query(models.PipelineTask).filter(models.PipelineTask.id == dep_id).one()

    _target.dependencies.append(_dep)
    db.commit()
    db.refresh(_target)
    return _target


def remove_dependency_from_task(
    db: Session, target_id: str, dep_id: str
) -> models.PipelineTask:
    _target = (
        db.query(models.PipelineTask).filter(models.PipelineTask.id == target_id).one()
    )
    _dep = db.query(models.PipelineTask).filter(models.PipelineTask.id == dep_id).one()
    if _dep in _target.dependencies:
        _target.dependencies.remove(_dep)
        db.commit()
        db.refresh(_target)
    return _target


# --- Pipeline Variable Endpoints ---


def get_pipeline_variables(
    db: Session,
    filter_function: Callable[[Query], Query],
    skip: int = 0,
    limit: int = 0,
):
    query = db.query(models.PipelineVariable)

    if filter_function is not None:  # uncomment this when using validator
        query = filter_function(query)
    return query.offset(skip).limit(limit).all()


def create_pipeline_variable(
    db: Session, dto: PipelineVariableCreate
) -> models.PipelineVariable:
    _var = models.PipelineVariable(name=dto.name, var_type=dto.var_type)

    db.add(_var)
    db.commit()
    db.refresh(_var)
    return _var


def update_pipeline_variable(
    db: Session, variable_id: UUID, dto: PipelineVariableUpdate
) -> models.PipelineVariable:
    _var = (
        db.query(models.PipelineVariable)
        .filter(models.PipelineVariable.id == variable_id)
        .one()
    )
    if dto.name is not None:
        _var.name = dto.name
    if dto.var_type is not None:
        _var.var_type = dto.var_type
    db.commit()
    db.refresh(_var)
    return _var


def delete_pipeline_variable(db: Session, variable_id: UUID) -> models.PipelineVariable:
    _var = (
        db.query(models.PipelineVariable)
        .filter(models.PipelineVariable.id == variable_id)
        .one()
    )
    db.delete(_var)
    db.commit()
    return _var


# --- SageMaker Pipeline Endpoints ---


def create_sagemaker_pipelines(
    request_count: int,
    json_files: list[str],
    persist_job_name: bool = False,
) -> list[dict]:
    results = []
    if request_count != len(json_files):
        raise ValueError(
            "The number of json_files provided does not match the request_count."
        )

    for json_file in json_files:
        try:
            pipeline_def = json2sagemaker.load_pipeline_definition(json_file)
            pipeline = json2sagemaker.create_pipeline(
                pipeline_def, persist_job_name_flag=persist_job_name
            )
            upsert_response = json2sagemaker.upsert_pipeline(pipeline)
            execution = json2sagemaker.start_pipeline(pipeline)
            results.append(
                {
                    "json_file": json_file,
                    "pipeline_execution_arn": execution.arn,
                    "upsert_response": upsert_response,
                }
            )
        except Exception as e:
            results.append(
                {
                    "json_file": json_file,
                    "error": str(e),
                }
            )
    return results


def get_sagemaker_pipeline_status(execution_arn: str) -> dict:
    client = boto3.client("sagemaker")
    return client.describe_pipeline_execution(PipelineExecutionArn=execution_arn)


def update_sagemaker_pipeline(
    json_file: str,
    persist_job_name: bool = False,
) -> dict:
    pipeline_def = json2sagemaker.load_pipeline_definition(json_file)
    pipeline = json2sagemaker.create_pipeline(
        pipeline_def, persist_job_name_flag=persist_job_name
    )
    upsert_response = json2sagemaker.upsert_pipeline(pipeline)
    execution = json2sagemaker.start_pipeline(pipeline)
    return {
        "json_file": json_file,
        "pipeline_execution_arn": execution.arn,
        "upsert_response": upsert_response,
    }


def delete_sagemaker_pipeline() -> dict:
    json2sagemaker.shutdown_processors()
    return {"message": "Cached processors have been shut down."}
