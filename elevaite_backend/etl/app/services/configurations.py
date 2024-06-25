from typing import List, Any, Callable, Type
from elevaitelib.orm.db import models
from sqlalchemy.orm import Session, Query

from elevaitelib.schemas.configuration import (
    ConfigurationCreate,
    ConfigurationUpdate,
    is_configuration,
)
from elevaitelib.orm.crud import (
    configuration as configuration_crud,
)


def getConfigurationsOfPipeline(
    db: Session,
    filter_function: Callable[[Query], Query],  # uncomment this when using validator
    pipeline_id: str,
) -> List[models.Configuration]:
    _conf = configuration_crud.get_configurations_of_pipeline(
        db,
        pipeline_id,
        filter_function=filter_function,  # uncomment this when using validator
    )
    return _conf


def getConfigurationById(db: Session, conf_id: str) -> models.Configuration:
    _conf = configuration_crud.get_configuration_by_id(db, conf_id)
    return _conf


def createConfiguration(
    db: Session, create_configuration: ConfigurationCreate
) -> models.Configuration:
    _conf = configuration_crud.create_configuration(db, create_configuration)
    return _conf


def updateConfiguration(
    db: Session,
    conf_id: str,
    updateConfiguration: ConfigurationUpdate,
):
    _conf = configuration_crud.update_configuration(
        db=db, conf_id=conf_id, dto=updateConfiguration
    )
    return _conf
