import asyncio
import uuid
from typing import List, Tuple, Optional, Callable, Type
from elevaitelib.orm.db import models
from elevaitelib.schemas.pipeline import PipelineCreate, is_pipeline
from elevaitelib.util.func import to_kebab_case
from fastapi import HTTPException
from qdrant_client import AsyncQdrantClient
from qdrant_client.conversions import common_types as types
from qdrant_client.http.models import Distance, VectorParams
from sqlalchemy.orm import Session, Query
from elevaitelib.schemas.collection import Collection, CollectionCreate
from elevaitelib.orm.crud import pipeline as pipeline_crud
from elevaitelib.util import func as util_func


def getPipelines(
    db: Session,
    filter_function: Callable[[Query], Query],  # uncomment this when using validator
    skip: int = 0,
    limit: int = 10,
):
    r = pipeline_crud.get_pipelines(
        db=db, skip=skip, limit=limit, filter_function=filter_function
    )
    return r


def getPipelinesOfProject(
    db: Session,
    filter_function: Callable[[Query], Query],
    project_id: uuid.UUID,
    skip: int = 0,
    limit: int = 10,
):
    r = pipeline_crud.get_pipelines_of_project(
        db=db,
        skip=skip,
        limit=limit,
        filter_function=filter_function,
        project_id=project_id,
    )
    return r


def getPipelineById(
    db: Session,
    id: str,
    project_id: uuid.UUID,
    filter_function: Callable[[Query], Query],
):
    pipeline = pipeline_crud.get_pipeline_by_id(
        db=db, pipeline_id=id, filter_function=filter_function, project_id=project_id
    )
    if not is_pipeline(pipeline):
        raise HTTPException(404, "Pipeline not found")


def createPipeline(db: Session, dto: PipelineCreate):
    return pipeline_crud.create_pipeline(db=db, pipeline_dto=dto)
