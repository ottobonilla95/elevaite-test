from fastapi import APIRouter
from typing import Annotated
from fastapi import APIRouter, Body, Depends
import pika
from sqlalchemy.orm import Session
from app.services import applications as app_service, instances as instance_service
from app.routers.deps import get_rabbitmq_connection, get_db
from elevaitedb.schemas import (
    instance as instance_schemas,
    configuration as configuration_schemas,
)


router = APIRouter(prefix="/application/{application_id}/instance", tags=["instances"])


@router.get("", response_model=list[instance_schemas.Instance])
def getApplicationInstances(
    application_id: int,
    db: Session = Depends(get_db),
) -> list[instance_schemas.Instance]:
    return instance_service.getApplicationInstances(db, application_id)


@router.get("/{instance_id}", response_model=instance_schemas.Instance)
def getApplicationInstanceById(
    application_id: int,
    instance_id: str,
    db: Session = Depends(get_db),
) -> instance_schemas.Instance:
    return instance_service.getApplicationInstanceById(
        db, application_id=application_id, instance_id=instance_id
    )


@router.get(
    "/{instance_id}/chart",
    response_model=instance_schemas.InstanceChartData,
)
def getApplicationInstanceChart(
    application_id: int, instance_id: str
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
    db: Session = Depends(get_db),
) -> instance_schemas.InstanceChartData:
    return instance_service.getApplicationInstanceConfiguration(
        db=db, application_id=application_id, instance_id=instance_id
    )


# @router.post(
#     "/{instance_id}/approve",
#     response_model=instance_schemas.Instance,
# )
# def approveApplicationInstance(
#     application_id: int,
#     instance_id: str,
#     db: Session = Depends(get_db),
# ) -> instance_schemas.Instance:
#     return service.approveApplicationInstance(
#         db, application_id=application_id, instance_id=instance_id
#     )


@router.post("/", response_model=instance_schemas.Instance)
def createApplicationInstance(
    application_id: int,
    createApplicationInstanceDto: Annotated[
        configuration_schemas.S3IngestFormDataDTO
        | configuration_schemas.PreProcessFormDTO,
        Body(),
    ],
    rmq: pika.BlockingConnection = Depends(get_rabbitmq_connection),
    db: Session = Depends(get_db),
) -> instance_schemas.Instance:
    return instance_service.createApplicationInstance(
        db=db,
        application_id=application_id,
        createInstanceDto=createApplicationInstanceDto,
        rmq=rmq,
    )
