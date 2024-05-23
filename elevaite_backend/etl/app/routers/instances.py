from pprint import pprint
from fastapi import APIRouter, Request
from typing import Annotated, Any, Sequence, List, Dict, Callable, Type, Optional
from fastapi import APIRouter, Body, Depends, Header
import pika
from uuid import UUID
from sqlalchemy.orm import Session, Query
from ..services import instances as instance_service
from .deps import get_rabbitmq_connection, get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
    instance as instance_schemas,
    configuration as configuration_schemas,
    # api as api_schemas,
)
# from rbac_api import (
#    route_validator_map,
#    RBACValidatorProvider
# )

router = APIRouter(prefix="/application/{application_id}/instance", tags=["instances"])


@router.get("", response_model=list[instance_schemas.Instance])
def getApplicationInstances(
    # request: Request, #uncomment when using validator
    application_id: int,
    db: Session = Depends(get_db),  # comment this when using validator
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getApplicationInstances')]), # uncomment this when using validator
    # project_id: UUID = Header(..., alias = "X-elevAIte-ProjectId", description="project_id under which connector instances are queried"), # uncomment this when using validator
) -> Sequence[instance_schemas.Instance]:
    
    # db: Session = request.state.db # uncomment this when using validator
    # all_query_authorized_types_filter_function = RBACValidatorProvider.get_instance().get_post_validation_types_filter_function_for_all_query(models.Instance, validation_info) # uncomment this when using validator

    return instance_service.getApplicationInstances(
        db,
        application_id,
        # project_id, # uncomment this when using validator
        # filter_function= all_query_authorized_types_filter_function, # uncomment this when using validator
    )


@router.get("/{instance_id}", response_model=instance_schemas.Instance)
def getApplicationInstanceById(
    application_id: int,
    instance_id: str,
    db: Session = Depends(get_db),  # comment this when using validator
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getApplicationInstanceById')]), # uncomment this to use validator
) -> instance_schemas.Instance:

    # instance = validation_info.get("Instance", None) # uncomment this when using validator
    # return instance # uncomment this when using validator

    # comment lines below when using validator
    res = instance_service.getApplicationInstanceById(
        db, application_id=application_id, instance_id=instance_id
    )
    return res


@router.get(
    "/{instance_id}/chart",
    response_model=instance_schemas.InstanceChartData,
)
def getApplicationInstanceChart(
    application_id: int,
    instance_id: str,
    # _= Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getApplicationInstanceChart')]), # uncomment this to use validator
) -> instance_schemas.InstanceChartData:
    return instance_service.getApplicationInstanceChart(
        application_id=application_id, instance_id=instance_id
    )


@router.get(
    "/{instance_id}/configuration",
    response_model=configuration_schemas.Configuration,
)
def getApplicationInstanceConfiguration(
    # request: Request, # uncomment when using validator
    application_id: int,
    instance_id: str,
    db: Session = Depends(get_db),  # comment this when using validator
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getApplicationInstanceConfiguration')]), # uncomment to use validator
) -> instance_schemas.Configuration:
    # db: Session = request.state.db # uncomment this when using validator
    return instance_service.getApplicationInstanceConfiguration(
        db=db, application_id=application_id, instance_id=instance_id
    )


@router.get(
    "/{instance_id}/log",
    response_model=list[instance_schemas.InstanceLogs],
)
def getApplicationInstanceLogs(
    instance_id: str,
    skip: int = 0,
    limit: int = 100,
    # _= Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getApplicationInstanceLogs')]), # uncomment this to use validator
) -> list[instance_schemas.InstanceLogs]:
    return instance_service.getApplicationInstanceLogs(
        instance_id=instance_id, offset=skip, limit=limit
    )


@router.post("/", response_model=instance_schemas.Instance)
def createApplicationInstance(
    # request: Request, #uncomment when using validator
    application_id: int,
    createInstanceDto: Annotated[
        instance_schemas.InstanceCreateDTO,
        Body(),
    ],
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'createApplicationInstance')]), # uncomment this to use validator
    rmq: pika.BlockingConnection = Depends(get_rabbitmq_connection),
    db: Session = Depends(get_db),  # comment this when using validator
) -> instance_schemas.Instance:
    # db: Session = request.state.db # uncomment this when using validator
    return instance_service.createApplicationInstance(
        db=db,
        application_id=application_id,
        createInstanceDto=createInstanceDto,
        rmq=rmq,
    )
