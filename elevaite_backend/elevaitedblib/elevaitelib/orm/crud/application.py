from sqlalchemy.orm import Session, Query
from typing import Callable, Type
from ..db import models
from ...schemas import application


def get_applications(
    db: Session,
    # filter_function: Callable[[Query], Query], # uncomment this when using validator
    skip: int = 0,
    limit: int = 100,
):
    query = db.query(models.Application)

    # if filter_function is not None: # uncomment this when using validator
    # query = filter_function(query)

    return query.offset(skip).limit(limit).all()


def get_application_by_id(db: Session, id: int):
    return db.query(models.Application).filter(models.Application.id == id).first()


def create_application(
    db: Session, createApplicationDTO: application.ApplicationCreate
):
    _app = models.Application(
        title=createApplicationDTO.title,
        icon=createApplicationDTO.icon,
        applicationType=createApplicationDTO.applicationType,
        creator=createApplicationDTO.creator,
        description=createApplicationDTO.description,
        version=createApplicationDTO.version,
    )
    # app.applicationType = createApplicationDTO
    db.add(_app)
    db.commit()
    db.refresh(_app)
    return _app
