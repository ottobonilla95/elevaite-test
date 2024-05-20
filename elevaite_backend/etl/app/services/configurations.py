from typing import List, Any, Callable, Type
from elevaitedb.db import models
from sqlalchemy.orm import Session, Query

from elevaitedb.schemas.configuration import (
    ConfigurationCreate,
    ConfigurationUpdate,
    is_configuration,
)
from elevaitedb.crud import (
    configuration as configuration_crud,
)


def getConfigurationsOfApplication(
    db: Session, 
    # filter_function: Callable[[Query], Query], # uncomment this when using validator
    application_id: int
) -> List[models.Configuration]:
    _conf = configuration_crud.get_configurations_of_application(
        db,
        application_id,
        # filter_function=filter_function, # uncomment this when using validator  
    )
    return _conf


def getConfigurationById(
    db: Session, application_id: int, conf_id: str
) -> models.Configuration:
    _conf = configuration_crud.get_configuration_by_id(db, application_id, conf_id)
    return _conf


def createConfiguration(
    db: Session, create_configuration: ConfigurationCreate
) -> models.Configuration:
    _conf = configuration_crud.create_configuration(db, create_configuration)
    return _conf


def updateConfiguration(
    db: Session,
    application_id: int,
    conf_id: str,
    updateConfiguration: ConfigurationUpdate,
):
    _conf = configuration_crud.update_configuration(
        db=db, application_id=application_id, conf_id=conf_id, dto=updateConfiguration
    )
    return _conf
