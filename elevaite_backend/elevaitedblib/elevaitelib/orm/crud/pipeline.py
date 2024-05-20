from sqlalchemy.orm import Session

from ..db import models


def get_pipelines(db: Session, skip: int = 0, limit: int = 0) -> list[models.Pipeline]:
    return db.query(models.Pipeline).offset(skip).limit(limit).all()


def get_pipelines_of_application(
    db: Session, application_id: int, skip: int = 0, limit: int = 100
) -> list[models.Pipeline]:
    return (
        db.query(models.Pipeline)
        .filter(models.Pipeline.applicationId == application_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_pipeline_by_id(db: Session, pipeline_id: str) -> models.Pipeline:
    return db.query(models.Pipeline).filter(models.Pipeline.id == pipeline_id).first()
