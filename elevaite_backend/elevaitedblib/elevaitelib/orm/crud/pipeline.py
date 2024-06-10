from elevaitelib.schemas.pipeline import PipelineCreate
from sqlalchemy.orm import Session

from ..db import models


def get_pipelines(db: Session, skip: int = 0, limit: int = 0) -> list[models.Pipeline]:
    return db.query(models.Pipeline).offset(skip).limit(limit).all()


def get_pipeline_by_id(db: Session, pipeline_id: str) -> models.Pipeline:
    return db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()


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
