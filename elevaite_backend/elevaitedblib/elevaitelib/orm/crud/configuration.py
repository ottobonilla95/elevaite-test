import json
from sqlalchemy.orm import Session, Query
from typing import Type, Callable
from ..db import models
from ...schemas import configuration as schema
from ...util.func import to_dict


def get_configuration_by_id(db: Session, application_id: int, id: str):
    return (
        db.query(models.Configuration)
        .filter(models.Configuration.applicationId == application_id)
        .filter(models.Configuration.id == id)
        .first()
    )


def get_configurations_of_application(
    db: Session,
    application_id: int,
    # filter_function: Callable[[Query], Query], # uncomment this when using validator
):
    query = db.query(models.Configuration)

    # if filter_function is not None: # uncomment this when using validator
    # query = filter_function(query)

    return query.filter(models.Configuration.applicationId == application_id).all()


def create_configuration(
    db: Session,
    configurationCreate: schema.ConfigurationCreate,
):
    _configuration = models.Configuration(
        applicationId=configurationCreate.applicationId,
        name=configurationCreate.name,
        isTemplate=configurationCreate.isTemplate,
        raw=to_dict(configurationCreate.raw),
    )
    # app.applicationType = createApplicationDTO
    db.add(_configuration)
    db.commit()
    db.refresh(_configuration)
    return _configuration


def update_configuration(
    db: Session, application_id: int, conf_id: str, dto: schema.ConfigurationUpdate
):
    _conf = get_configuration_by_id(db, application_id, conf_id)
    if _conf is None:
        return None

    for var, value in vars(dto).items():
        if value:
            (
                setattr(_conf, var, value)
                if var != "raw"
                else setattr(_conf, var, to_dict(value))
            )
        else:
            None

    db.add(_conf)
    db.commit()
    db.refresh(_conf)
    return _conf
