from typing import Annotated
from elevaitelib.schemas import (
    pipeline as pipeline_schemas,
)
from fastapi import APIRouter, Body, Depends
from rbac_api import RBACValidatorProvider

from ..services import pipeline_tasks as task_service
from .deps import get_db

rbacValidator = RBACValidatorProvider.get_instance()

router = APIRouter(prefix="/pipeline/task", tags=["pipeline tasks"])


@router.get("", response_model=list[pipeline_schemas.PipelineTask])
def getPipelines(
    skip: int = 0,
    limit: int = 10,
    db=Depends(get_db),
):
    return task_service.getPipelineTasks(db=db, skip=skip, limit=limit, filter_function=None)


@router.get("{task_id}", response_model=pipeline_schemas.PipelineTask)
def getPipelineTaskById(task_id: str, db=Depends(get_db)):
    return task_service.getTaskById(db=db, filter_function=None, id=task_id)


@router.post("", response_model=pipeline_schemas.PipelineTask)
def createPipelinetask(dto: Annotated[pipeline_schemas.PipelineTaskCreate, Body()], db=Depends(get_db)):
    return task_service.createTask(db=db, dto=dto, filter_function=None)


@router.put("{task_id}", response_model=pipeline_schemas.PipelineTask)
def updatePipelineTask(task_id: str, dto: Annotated[pipeline_schemas.PipelineTaskUpdate, Body()], db=Depends(get_db)):
    return task_service.updateTask(db=db, dto=dto, filter_function=None, id=task_id)


@router.post("{task_id}/dependencies", response_model=pipeline_schemas.PipelineTask)
def addDependencyToTask(task_id: str, dto: Annotated[pipeline_schemas.PipelineTaskDependency, Body()], db=Depends(get_db)):
    return task_service.addDependencyToTask(db=db, task_id=task_id, dep_id=dto.task_id)


@router.delete("{task_id}", response_model=pipeline_schemas.PipelineTask)
def deleteTask(task_id: str, db=Depends(get_db)):
    return task_service.deleteTask(db=db, task_id=task_id, filter_function=None)
