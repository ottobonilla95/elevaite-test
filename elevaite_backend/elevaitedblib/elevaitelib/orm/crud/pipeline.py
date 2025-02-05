from typing import Callable
from uuid import UUID
from elevaitelib.schemas.pipeline import PipelineCreate, PipelineTaskCreate, PipelineTaskUpdate, PipelineVariableCreate
from sqlalchemy.orm import Session, Query

from ..db import models


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
    return query.filter(models.Pipeline.projects.any(id=project_id)).offset(skip).limit(limit).all()


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


def add_tasks_to_pipeline(db: Session, pipeline_id: str, task_id: str) -> models.Pipeline:
    _pipeline = db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).one()
    _task = db.query(models.PipelineTask).filter(models.PipelineTask.id == task_id).one()
    _pipeline.tasks.append(_task)
    db.commit()
    db.refresh(_pipeline)
    return _pipeline


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


def create_pipeline_tast(db: Session, dto: PipelineTaskCreate) -> models.PipelineTask:
    _task = models.PipelineTask(name=dto.name, task_type=dto.task_type, src=dto.src)

    db.add(_task)
    db.commit()
    db.refresh(_task)
    return _task


def update_pipeline_task(db: Session, id: str, dto: PipelineTaskUpdate) -> models.PipelineTask:
    _task = db.query(models.PipelineTask).filter(models.PipelineTask.id == id).one()
    if dto.dependencies:
        _task.dependencies = []
        for dep in dto.dependencies:
            __task = db.query(models.PipelineTask).filter(models.PipelineTask.id == dep.id).one()
            _task.dependencies.append(__task)

    if dto.input:
        _task.input = []
        for var in dto.input:
            _var = db.query(models.PipelineVariable).filter(models.PipelineVariable.name == var.name).one()
            _task.input.append(_var)

    if dto.output:
        _task.output = []
        for var in dto.output:
            _var = db.query(models.PipelineVariable).filter(models.PipelineVariable.name == var.name).one()
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


def add_dependency_to_task(db: Session, target_id: str, dep_id: str) -> models.PipelineTask:
    _target = db.query(models.PipelineTask).filter(models.PipelineTask.id == target_id).one()
    _dep = db.query(models.PipelineTask).filter(models.PipelineTask.id == dep_id).one()

    _target.dependencies.append(_dep)
    db.commit()
    db.refresh(_target)
    return _target


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


def create_pipeline_variable(db: Session, dto: PipelineVariableCreate) -> models.PipelineVariable:
    _var = models.PipelineVariable(name=dto.name, var_type=dto.var_type)

    db.add(_var)
    db.commit()
    db.refresh(_var)
    return _var
