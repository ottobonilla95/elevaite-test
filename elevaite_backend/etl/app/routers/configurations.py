from pprint import pprint
from typing import Annotated, Any, List, Dict, Type, Callable
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session, Query
from ..services import configurations as conf_service
from .deps import get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
    configuration as configuration_schemas,
)
from rbac_api import (
   validators,
   rbac_instance
)
router = APIRouter(
    prefix="/application/{application_id}/configuration", tags=["configurations"]
)


@router.get("", response_model=list[configuration_schemas.Configuration])
def getApplicationConfigurations(
    application_id: int,
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connector_configurations_factory(models.Configuration, ("READ",))), # uncomment this to use validator
    ):

    # db: Session = validation_info.get("db", None) # uncomment this when using validator

    # typenames = validation_info.get("target_entity_typename_combinations", tuple()) # uncomment this when using validator
    # typevalues = validation_info.get("target_entity_typevalue_combinations", tuple()) # uncomment this when using validator

    # filters_list: List[Dict[str, Any]] = rbac_instance.generate_post_validation_type_filters_for_all_query(models.Configuration, typenames, typevalues, validation_info) # uncomment this when using validator

    # Create a filter function closure
    # def filter_function(model_class : Type[models.Base], query: Query) -> Query:  # uncomment this when using validator
    #     return rbac_instance.apply_post_validation_type_filters_for_all_query(
    #         model_class, filters_list, query)
    
    return conf_service.getConfigurationsOfApplication(
        db=db,
        # filter_function=filter_function, # uncomment this when using validator
        application_id=application_id
    )


@router.get("/{configuration_id}", response_model=configuration_schemas.Configuration)
def getApplicationConfiguration(
    application_id: int,
    configuration_id: str,
    db: Session = Depends(get_db),
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connector_configuration_factory(models.Configuration, ("READ",))), #uncomment this to use validator
):
    # applicationConfiguration = validation_info.get("Configuration", None) # uncomment this when using validator
    # return applicationConfiguration # uncomment this when using validator

    return conf_service.getConfigurationById(
        db, application_id, conf_id=configuration_id
    ) # comment this when using validator


@router.post("/", response_model=configuration_schemas.Configuration)
def createConfiguration(
    application_id: int,
    createConfigurationDto: Annotated[
        configuration_schemas.ConfigurationCreate, Body()
    ],
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_create_connector_configuration_factory(models.Configuration, ("CREATE",))), # uncomment this to use validator
):
    # db: Session = validation_info.get("db", None) #comment this when using validator
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
