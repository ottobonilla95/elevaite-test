from typing import List
from sqlalchemy.orm import Session
from elevaitelib.orm.crud import (
    pipeline as pipeline_crud,
    application as application_crud,
)
from elevaitelib.orm.db import models


def getApplicationList(
    db: Session,
    # filter_function: Callable[[Query], Query] # uncomment this when using validator
) -> List[models.Application]:
    apps = application_crud.get_applications(
        db=db,
        # filter_function=filter_function # uncomment this when using validator
    )
    return apps


def getApplicationById(db: Session, application_id: int) -> models.Application:
    app = application_crud.get_application_by_id(db, application_id)
    return app


def getApplicationPipelines(db: Session, application_id: int) -> List[models.Pipeline]:
    pipelines = pipeline_crud.get_pipelines_of_application(db, application_id)
    return pipelines
