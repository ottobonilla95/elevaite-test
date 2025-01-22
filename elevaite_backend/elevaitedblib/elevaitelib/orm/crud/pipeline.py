from sqlalchemy.orm import Session

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
