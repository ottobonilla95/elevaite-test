from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Any
from elevaitedb.schemas.application import Application, is_application, ApplicationType
from elevaitedb.schemas.pipeline import Pipeline, is_pipeline
from elevaitedb.crud import (
    pipeline as pipeline_crud,
    application as application_crud,
)
from elevaitedb.db import models


def getApplicationList(
    db: Session,
    # filters_list: List[dict[str, Any]] = [], # uncomment this when using validator
) -> List[models.Application]:
    apps = application_crud.get_applications(
        db=db, 
        # filters_list=filters_list # uncomment this when using validator
        )
    return apps


def getApplicationById(db: Session, application_id: int) -> models.Application:
    app = application_crud.get_application_by_id(db, application_id)
    return app


def getApplicationPipelines(db: Session, application_id: int) -> List[models.Pipeline]:
    pipelines = pipeline_crud.get_pipelines_of_application(db, application_id)
    return pipelines
