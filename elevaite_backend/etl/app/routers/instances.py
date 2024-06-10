from pprint import pprint
from fastapi import APIRouter, Request
from typing import Annotated, Any, Sequence, List, Dict, Callable, Type, Optional
from fastapi import APIRouter, Body, Depends, Header
import pika
from flytekit.remote import FlyteRemote
from uuid import UUID
from sqlalchemy.orm import Session, Query
from ..services import instances as instance_service
from .deps import get_flyte_remote, get_rabbitmq_connection, get_db
from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    instance as instance_schemas,
    configuration as configuration_schemas,
    # api as api_schemas,
)

# from rbac_api import (
#    route_validator_map,
#    RBACValidatorProvider
# )
# rbacValidator = RBACValidatorProvider.get_instance()

router = APIRouter(prefix="/instance", tags=["instances"])


@router.get("/{instance_id}", response_model=instance_schemas.Instance)
def getApplicationInstanceById(
    instance_id: str,
    db: Session = Depends(get_db),  # comment this when using validator
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getApplicationInstanceById')]), # uncomment this to use validator
) -> instance_schemas.Instance:

    instance = validation_info.get(
        "Instance", None
    )  # uncomment this when using validator
    return instance  # uncomment this when using validator

    # comment lines below when using validator
    # res = instance_service.getInstanceById(db, instance_id=instance_id)
    # return res


@router.get(
    "/{instance_id}/chart",
    response_model=instance_schemas.InstanceChartData,
)
def getApplicationInstanceChart(
    instance_id: str,
    # _= Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'getApplicationInstanceChart')]), # uncomment this to use validator
) -> instance_schemas.InstanceChartData:
    return instance_service.getInstanceChart(instance_id=instance_id)


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
    db: Session = request.state.db  # uncomment this when using validator
    return instance_service.getInstanceConfiguration(
        db=db, pipeline_id=pipeline_id, instance_id=instance_id
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
    return instance_service.getInstanceLogs(
        instance_id=instance_id, offset=skip, limit=limit
    )


@router.post("/", response_model=instance_schemas.Instance)
def createApplicationInstance(
    request: Request,  # uncomment when using validator
    createInstanceDto: Annotated[
        instance_schemas.InstanceCreateDTO,
        Body(),
    ],
    # validation_info:dict[str, Any] = Depends(route_validator_map[(api_schemas.APINamespace.ETL_API, 'createApplicationInstance')]), # uncomment this to use validator
    rmq: pika.BlockingConnection = Depends(get_rabbitmq_connection),
    # db: Session = Depends(get_db),  # comment this when using validator
    remote: FlyteRemote = Depends(get_flyte_remote),
    validation_info: dict[str, Any] = Depends(
        routes_to_middleware_imple_map["createApplicationInstance"]
    ),  # uncomment this to use validator
) -> instance_schemas.Instance:
    db: Session = request.state.db  # uncomment this when using validator
    return instance_service.createInstance(
        db=db, createInstanceDto=createInstanceDto, rmq=rmq, remote=remote
    )
