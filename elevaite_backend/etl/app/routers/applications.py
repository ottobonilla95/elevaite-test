from pprint import pprint
from typing import Annotated
from fastapi import APIRouter, Body, Depends
import pika
from sqlalchemy.orm import Session
from app.services import applications as service
from app.util.websockets import ConnectionManager
from app.routers.deps import get_rabbitmq_connection, get_db
from elevaitedb.schemas import (
    application as application_schemas,
    instance as instance_schemas,
    pipeline as pipeline_schemas,
    configuration as configuration_schemas,
)

router = APIRouter(prefix="/application", tags=["applications"])
manager = ConnectionManager()


@router.get("", response_model=list[application_schemas.Application])
def getApplicationList(
    db: Session = Depends(get_db),
) -> list[application_schemas.Application]:
    return service.getApplicationList(db)


@router.get("/{application_id}", response_model=application_schemas.Application)
def getApplicationById(
    application_id: int,
    db: Session = Depends(get_db),
) -> application_schemas.Application:
    return service.getApplicationById(db, application_id)


# @router.get("/{application_id}/form")
# def getApplicationForm(application_id: int) -> ApplicationFormDTO:
#     return service.getApplicationForm(application_id)


@router.get(
    "/{application_id}/instance", response_model=list[instance_schemas.Instance]
)
def getApplicationInstances(
    application_id: int,
    db: Session = Depends(get_db),
) -> list[instance_schemas.Instance]:
    return service.getApplicationInstances(db, application_id)


@router.get(
    "/{application_id}/instance/{instance_id}", response_model=instance_schemas.Instance
)
def getApplicationInstanceById(
    application_id: int,
    instance_id: str,
    db: Session = Depends(get_db),
) -> instance_schemas.Instance:
    return service.getApplicationInstanceById(
        db, application_id=application_id, instance_id=instance_id
    )


@router.get(
    "/{application_id}/instance/{instance_id}/chart",
    response_model=instance_schemas.InstanceChartData,
)
def getApplicationInstanceChart(
    application_id: int, instance_id: str
) -> instance_schemas.InstanceChartData:
    return service.getApplicationInstanceChart(
        application_id=application_id, instance_id=instance_id
    )


@router.get(
    "/{application_id}/instance/{instance_id}/configuration",
    response_model=configuration_schemas.Configuration,
)
def getApplicationInstanceConfiguration(
    application_id: int,
    instance_id: str,
    db: Session = Depends(get_db),
) -> instance_schemas.InstanceChartData:
    return service.getApplicationInstanceConfiguration(
        db=db, application_id=application_id, instance_id=instance_id
    )


@router.post(
    "/{application_id}/instance/{instance_id}/approve",
    response_model=instance_schemas.Instance,
)
def approveApplicationInstance(
    application_id: int,
    instance_id: str,
    db: Session = Depends(get_db),
) -> instance_schemas.Instance:
    return service.approveApplicationInstance(
        db, application_id=application_id, instance_id=instance_id
    )


@router.post("/{application_id}/instance/", response_model=instance_schemas.Instance)
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
    return service.createApplicationInstance(
        db=db,
        application_id=application_id,
        createInstanceDto=createApplicationInstanceDto,
        rmq=rmq,
    )


# @router.websocket("/{application_id}/instance/{instance_id}/ws/{client_id}")
# async def websocket_endpoint(websocket: WebSocket, client_id: int):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             await manager.send_personal_message(f"You wrote: {data}", websocket)
#             await manager.broadcast(f"Client #{client_id} says: {data}")
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)
#         await manager.broadcast(f"Client #{client_id} left the chat")


@router.get(
    "/{application_id}/pipelines", response_model=list[pipeline_schemas.Pipeline]
)
def getApplicationPipelines(
    application_id: int,
    db: Session = Depends(get_db),
) -> list[pipeline_schemas.Pipeline]:
    return service.getApplicationPipelines(db, application_id)
