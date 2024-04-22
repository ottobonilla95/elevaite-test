from fastapi import APIRouter,Query
from typing import Annotated, Any, Sequence
from fastapi import APIRouter, Body, Depends
import pika
from uuid import UUID
from sqlalchemy.orm import Session
from ..services import instances as instance_service
from .deps import get_rabbitmq_connection, get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
    instance as instance_schemas,
    configuration as configuration_schemas,
)
from rbac_api import validators

router = APIRouter(prefix="/application/{application_id}/instance", tags=["instances"])


@router.get("", response_model=list[instance_schemas.Instance])
def getApplicationInstances(
    application_id: int,
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connector_instances_factory(models.Instance, ("READ",))) # uncomment this when using validator
) -> Sequence[instance_schemas.Instance]:
    # db: Session = validation_info.get("db", None) # uncomment this when using validator
    # project = validation_info.get('Project', None) # uncomment this when using validator
    return instance_service.getApplicationInstances(
        db,
        application_id,
        # project.id # uncomment this when using validator
    )


@router.get("/{instance_id}", response_model=instance_schemas.Instance)
def getApplicationInstanceById(
    application_id: int,
    instance_id: str,
    db: Session = Depends(get_db), # comment this when using validator 
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connector_instance_factory(models.Instance, ("READ",))) # uncomment this to use validator
) -> instance_schemas.Instance:
    
    # instance = validation_info.get("Instance", None) # uncomment this when using validator
    # return instance # uncomment this when using validator
    
    # comment lines below when using validator
    return instance_service.getApplicationInstanceById(
        db, application_id=application_id, instance_id=instance_id
    )


@router.get(
    "/{instance_id}/chart",
    response_model=instance_schemas.InstanceChartData,
)
def getApplicationInstanceChart(
    application_id: int, instance_id: str,
    # _= Depends(validators.validate_get_connector_instance_chart_factory(models.Instance, ("READ",))) # uncomment this to use validator
) -> instance_schemas.InstanceChartData:
    return instance_service.getApplicationInstanceChart(
        application_id=application_id, instance_id=instance_id
    )


@router.get(
    "/{instance_id}/configuration",
    response_model=configuration_schemas.Configuration,
)
def getApplicationInstanceConfiguration(
    application_id: int,
    instance_id: str,
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connector_instance_configuration_factory(models.Instance, ("CONFIGURATION","READ")))
) -> instance_schemas.Configuration:
    # db: Session = validation_info.get("db", None) # uncomment this when using validator
    return instance_service.getApplicationInstanceConfiguration(
        db=db, application_id=application_id, instance_id=instance_id
    )


@router.get(
    "/{instance_id}/log",
    response_model=list[instance_schemas.InstanceLogs],
)
def getApplicationInstanceLogs(
    instance_id: str, skip: int = 0, limit: int = 100,
    # _= Depends(validators.validate_get_connector_instance_logs_factory(models.Instance, ("READ",))), # uncomment this to use validator
) -> list[instance_schemas.InstanceLogs]:
    return instance_service.getApplicationInstanceLogs(
        instance_id=instance_id, offset=skip, limit=limit
    )


@router.post("/", response_model=instance_schemas.Instance)
def createApplicationInstance(
    application_id: int,
    createInstanceDto: Annotated[
        instance_schemas.InstanceCreateDTO,
        Body(),
    ],
    rmq: pika.BlockingConnection = Depends(get_rabbitmq_connection),
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_create_connector_instance_factory(models.Instance, ("CREATE",))) # uncomment this to use validator
) -> instance_schemas.Instance:
    # db: Session = validation_info.get("db", None) # uncomment this when using validator
    return instance_service.createApplicationInstance(
        db=db,
        application_id=application_id,
        createInstanceDto=createInstanceDto,
        rmq=rmq,
    )
