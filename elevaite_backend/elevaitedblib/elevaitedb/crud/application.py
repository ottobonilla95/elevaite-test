from sqlalchemy.orm import Session
from typing import Optional
from ..db import models
from ..schemas import application


def get_applications(
        db: Session,
        # authorized_app_types: list[application.ApplicationType], # uncomment this when using validator
        skip: int = 0,
        limit: int = 100
    ):
    query = db.query(models.Application)
    # query = query.filter(models.Application.applicationType.in_(authorized_app_types)) # uncomment this when using validator
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
