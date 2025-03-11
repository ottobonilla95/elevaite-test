from typing import Callable, Union

from elevaitelib.orm.crud import pipeline as pipeline_crud
from elevaitelib.orm.db import models
from elevaitelib.schemas.pipeline import PipelineTaskCreate, PipelineTaskUpdate
from sqlalchemy.orm import Query, Session


def getPipelineTasks(
    db: Session,
    filter_function: Union[Callable[[Query], Query], None],
    skip: int = 0,
    limit: int = 10,
) -> list[models.PipelineTask]:
    return pipeline_crud.get_pipeline_tasks(db=db, filter_function=filter_function, skip=skip, limit=limit)


def getTaskById(db: Session, filter_function: Union[Callable[[Query], Query], None], id: str) -> models.PipelineTask:
    return pipeline_crud.get_pipeline_task_by_id(db=db, filter_function=filter_function, id=id)


def createTask(
    db: Session, filter_function: Union[Callable[[Query], Query], None], dto: PipelineTaskCreate
) -> models.PipelineTask:
    return pipeline_crud.create_pipeline_task(db=db, dto=dto)


def updateTask(
    db: Session, filter_function: Union[Callable[[Query], Query], None], id: str, dto: PipelineTaskUpdate
) -> models.PipelineTask:
    return pipeline_crud.update_pipeline_task(db=db, id=id, dto=dto)


def addDependencyToTask(db: Session, task_id: str, dep_id: str) -> models.PipelineTask:
    return pipeline_crud.add_dependency_to_task(db=db, target_id=task_id, dep_id=dep_id)


def deleteTask(db: Session, filter_function: Union[Callable[[Query], Query], None], task_id: str) -> models.PipelineTask:
    return pipeline_crud.delete_pipeline_task(db=db, task_id=task_id)
