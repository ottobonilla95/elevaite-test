from typing import Callable, Union

from elevaitelib.orm.crud import pipeline as pipeline_crud
from elevaitelib.schemas.pipeline import PipelineCreate, is_pipeline
from fastapi import HTTPException
from sqlalchemy.orm import Query, Session


def getPipelines(
    db: Session,
    filter_function: Union[Callable[[Query], Query], None],
    skip: int = 0,
    limit: int = 10,
):
    r = pipeline_crud.get_pipelines(db=db, skip=skip, limit=limit, filter_function=filter_function)
    return r


def getPipelinesOfProject(
    db: Session,
    filter_function: Union[Callable[[Query], Query], None],
    skip: int = 0,
    limit: int = 10,
):
    r = pipeline_crud.get_pipelines_of_project(
        db=db,
        skip=skip,
        limit=limit,
        filter_function=filter_function,
    )
    return r


def getPipelineById(
    db: Session,
    id: str,
    filter_function: Union[Callable[[Query], Query], None],
):
    pipeline = pipeline_crud.get_pipeline_by_id(db=db, pipeline_id=id, filter_function=filter_function)
    if not is_pipeline(pipeline):
        raise HTTPException(404, "Pipeline not found")


def createPipeline(db: Session, dto: PipelineCreate):
    return pipeline_crud.create_pipeline(db=db, pipeline_dto=dto)
