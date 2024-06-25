from pprint import pprint
from typing import Annotated, Any, List, Dict, Type, Callable, Optional
from fastapi import APIRouter, Body, Depends, Request, Header
from sqlalchemy.orm import Session, Query
from ..services import configurations as conf_service
from .deps import get_db
from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    configuration as configuration_schemas,
    api as api_schemas,
)

from rbac_api import route_validator_map, RBACValidatorProvider

rbacValidator = RBACValidatorProvider.get_instance()
router = APIRouter(prefix="/configuration", tags=["configurations"])


@router.get("/{configuration_id}", response_model=configuration_schemas.Configuration)
def getConfigurationById(
    configuration_id: str,
    db: Session = Depends(get_db),
    validation_info: dict[str, Any] = Depends(
        route_validator_map[(api_schemas.APINamespace.ETL_API, "getConfigurationById")]
    ),  # uncomment this to use validator
):
    applicationConfiguration = validation_info.get(
        "Configuration", None
    )  # uncomment this when using validator
    return applicationConfiguration  # uncomment this when using validator

    # return conf_service.getConfigurationById(
    #     db, conf_id=configuration_id
    # )  # comment this when using validator


@router.post("/", response_model=configuration_schemas.Configuration)
def createConfiguration(
    request: Request,  # uncomment when using validator
    createConfigurationDto: Annotated[
        configuration_schemas.ConfigurationCreate, Body()
    ],
    # db: Session = Depends(get_db),  # comment this when using validator
    validation_info: dict[str, Any] = Depends(
        route_validator_map[(api_schemas.APINamespace.ETL_API, "createConfiguration")]
    ),  # uncomment this to use validator
):
    db: Session = request.state.db  # comment this when using validator
    return conf_service.createConfiguration(
        db, create_configuration=createConfigurationDto
    )


@router.put("/{configuration_id}", response_model=configuration_schemas.Configuration)
def updateConfiguration(
    request: Request,  # uncomment when using validator
    configuration_id: str,
    updateConfigurationDto: Annotated[
        configuration_schemas.ConfigurationUpdate, Body()
    ],
    # db: Session = Depends(get_db),  # comment this when using validator
    validation_info: dict[str, Any] = Depends(
        route_validator_map[(api_schemas.APINamespace.ETL_API, "updateConfiguration")]
    ),  # uncomment this to use validator
):
    db: Session = request.state.db  # uncomment this when using validator
    return conf_service.updateConfiguration(
        db=db,
        conf_id=configuration_id,
        updateConfiguration=updateConfigurationDto,
    )
