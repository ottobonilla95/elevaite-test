import json
from sqlalchemy.orm import Session, Query
from typing import Type, Callable
from ..db import models
from ...schemas import configuration as schema
from ...util.func import to_dict


def get_configuration_by_id(db: Session, id: str):
    return db.query(models.Configuration).filter(models.Configuration.id == id).first()


def get_configurations_of_pipeline(
    db: Session,
    pipeline_id: str,
    # filter_function: Callable[[Query], Query], # uncomment this when using validator
):
    query = db.query(models.Configuration)

    # if filter_function is not None: # uncomment this when using validator
    # query = filter_function(query)

    return query.filter(models.Configuration.pipelineId == pipeline_id).all()


def create_configuration(
    db: Session,
    configurationCreate: schema.ConfigurationCreate,
):
    _configuration = models.Configuration(
        pipelineId=configurationCreate.pipelineId,
        name=configurationCreate.name,
        isTemplate=configurationCreate.isTemplate,
        raw=to_dict(configurationCreate.raw),
    )
    db.add(_configuration)
    db.commit()
    db.refresh(_configuration)
    return _configuration


def update_configuration(db: Session, conf_id: str, dto: schema.ConfigurationUpdate):
    _conf = get_configuration_by_id(db, conf_id)
    if _conf is None:
        return None

    for var, value in vars(dto).items():
        if value:
            (
                setattr(_conf, var, value)
                if var != "raw"
                else setattr(_conf, var, to_dict(value))
            )

    db.add(_conf)
    db.commit()
    db.refresh(_conf)
    return _conf
