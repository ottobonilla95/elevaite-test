from pprint import pprint
from typing import Annotated, Any
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from ..services import configurations as conf_service
from .deps import get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
    configuration as configuration_schemas,
)
from rbac_api import validators
router = APIRouter(
    prefix="/application/{application_id}/configuration", tags=["configurations"]
)


@router.get("", response_model=list[configuration_schemas.Configuration])
def getApplicationConfigurations(
    application_id: int,
    db: Session = Depends(get_db),
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connector_configurations_factory(models.Configuration, ("READ",))),
    ):
    # db: Session = validation_info.get("db", None)
    return conf_service.getConfigurationsOfApplication(db, application_id)


@router.get("/{configuration_id}", response_model=configuration_schemas.Configuration)
def getApplicationConfiguration(
    application_id: int,
    configuration_id: str,
    db: Session = Depends(get_db),
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connector_configuration_factory(models.Configuration, ("READ",))),
):
    # applicationConfiguration = validation_info.get("Configuration", None)
    # return applicationConfiguration
    return conf_service.getConfigurationById(
        db, application_id, conf_id=configuration_id
    )


@router.post("/", response_model=configuration_schemas.Configuration)
def createConfiguration(
    application_id: int,
    createConfigurationDto: Annotated[
        configuration_schemas.ConfigurationCreate, Body()
    ],
    db: Session = Depends(get_db),
    # validation_info:dict[str, Any] = Depends(validators.validate_create_connector_configuration_factory(models.Configuration, ("CREATE",))),
):
    # db: Session = validation_info.get("db", None)
    return conf_service.createConfiguration(
        db, create_configuration=createConfigurationDto
    )


@router.put("/{configuration_id}", response_model=configuration_schemas.Configuration)
def updateConfiguration(
    application_id: int,
    configuration_id: str,
    updateConfigurationDto: Annotated[
        configuration_schemas.ConfigurationUpdate, Body()
    ],
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_update_connector_configuration_factory(models.Configuration, ("UPDATE",))), # uncomment this to use validator
):
    # db: Session = validation_info.get("db", None) # uncomment this when using validator
    return conf_service.updateConfiguration(
        db=db,
        application_id=application_id,
        conf_id=configuration_id,
        updateConfiguration=updateConfigurationDto,
    )
