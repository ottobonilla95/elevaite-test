from typing import Callable
from uuid import UUID
from elevaitelib.schemas.pipeline import PipelineCreate
from sqlalchemy.orm import Session, Query
from sqlalchemy import or_

from ..db import models


def get_pipelines(
    db: Session,
    filter_function: Callable[[Query], Query],
    skip: int = 0,
    limit: int = 0,
) -> list[models.Pipeline]:
    query = db.query(models.Pipeline)

    if filter_function is not None:  # uncomment this when using validator
        query = filter_function(query)
    return query.offset(skip).limit(limit).all()


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
        query.filter(
            or_(
                models.Pipeline.projectId == project_id,
                models.Pipeline.projectId == None,
            )
        )
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_pipeline_by_id(
    db: Session,
    pipeline_id: str,
    project_id: UUID,
    filter_function: Callable[[Query], Query] | None,
) -> models.Pipeline:
    query = db.query(models.Pipeline)

    if filter_function is not None:  # uncomment this when using validator
        query = filter_function(query)
    return query.filter(
        models.Pipeline.id == pipeline_id,
        or_(
            models.Pipeline.projectId == project_id,
            models.Pipeline.projectId == None,
        ),
    ).first()


def create_pipeline(db: Session, pipeline_dto: PipelineCreate) -> models.Pipeline:
    _pipeline = models.Pipeline(
        flyte_name=pipeline_dto.flyte_name,
        input=pipeline_dto.input,
        label=pipeline_dto.label,
    )
    db.add(_pipeline)
    db.commit()
    db.refresh(_pipeline)
    return _pipeline
