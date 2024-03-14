from sqlalchemy.orm import Session

from elevaitedb.schemas.configuration import (
    ConfigurationCreate,
    ConfigurationUpdate,
    is_configuration,
)
from elevaitedb.crud import (
    configuration as configuration_crud,
)


def getConfigurationsOfApplication(db: Session, application_id: int):
    _conf = configuration_crud.get_configurations_of_application(db, application_id)
    return _conf


def getConfigurationById(db: Session, application_id: int, conf_id: str):
    _conf = configuration_crud.get_configuration_by_id(db, application_id, conf_id)
    return _conf


def createConfiguration(db: Session, create_configuration: ConfigurationCreate):
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
