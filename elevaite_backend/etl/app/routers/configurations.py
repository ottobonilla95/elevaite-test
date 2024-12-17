from typing import Annotated
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from ..services import configurations as conf_service
from .deps import get_db
from elevaitelib.schemas import (
    configuration as configuration_schemas,
    # api as api_schemas,
)

# from rbac_api import (
#    route_validator_map,
#    RBACValidatorProvider
# )
# rbacValidator = RBACValidatorProvider.get_instance()
router = APIRouter(prefix="/application/{application_id}/configuration", tags=["configurations"])


@router.get("", response_model=list[configuration_schemas.Configuration])
def getApplicationConfigurations(
    # request: Request, #uncomment when using validator
    application_id: int,
    db: Session = Depends(get_db),  # comment this when using validator
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getApplicationConfigurations')]), # uncomment this to use validator
):
    # db: Session = request.state.db # uncomment this when using validator
    # all_query_authorized_types_filter_function = rbacValidator.get_post_validation_types_filter_function_for_all_query(models.Configuration, validation_info) # uncomment this when using validator

    return conf_service.getConfigurationsOfApplication(
        db=db,
        # filter_function=all_query_authorized_types_filter_function, # uncomment this when using validator
        application_id=application_id,
    )


@router.get("/{configuration_id}", response_model=configuration_schemas.Configuration)
def getApplicationConfiguration(
    application_id: int,
    configuration_id: str,
    db: Session = Depends(get_db),
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getApplicationConfiguration')]), #uncomment this to use validator
):
    # applicationConfiguration = validation_info.get("Configuration", None) # uncomment this when using validator
    # return applicationConfiguration # uncomment this when using validator

    return conf_service.getConfigurationById(db, application_id, conf_id=configuration_id)  # comment this when using validator


@router.post("/", response_model=configuration_schemas.Configuration)
def createConfiguration(
    # request: Request, #uncomment when using validator
    application_id: int,
    createConfigurationDto: Annotated[configuration_schemas.ConfigurationCreate, Body()],
    db: Session = Depends(get_db),  # comment this when using validator
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'createConfiguration')]), # uncomment this to use validator
):
    # db: Session = request.state.db #comment this when using validator
    return conf_service.createConfiguration(db, create_configuration=createConfigurationDto)


@router.put("/{configuration_id}", response_model=configuration_schemas.Configuration)
def updateConfiguration(
    # request: Request, #uncomment when using validator
    application_id: int,
    configuration_id: str,
    updateConfigurationDto: Annotated[configuration_schemas.ConfigurationUpdate, Body()],
    db: Session = Depends(get_db),  # comment this when using validator
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'updateConfiguration')]), # uncomment this to use validator
):
    # db: Session = request.state.db # uncomment this when using validator
    return conf_service.updateConfiguration(
        db=db,
        application_id=application_id,
        conf_id=configuration_id,
        updateConfiguration=updateConfigurationDto,
    )
