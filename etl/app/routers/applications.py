from pprint import pprint
from typing import Annotated
from fastapi import APIRouter, Body, Form, WebSocket, WebSocketDisconnect

from app.util.models import (
    ApplicationFormDTO,
    ApplicationInstanceDTO,
    ApplicationPipelineDTO,
    IngestApplicationChartDataDTO,
    IngestApplicationDTO,
    S3IngestFormDataDTO,
)
from app.services import applications as service
from app.util.websockets import ConnectionManager

router = APIRouter(prefix="/application", tags=["applications"])
manager = ConnectionManager()


@router.get("")
def getApplicationList() -> list[IngestApplicationDTO]:
    res = service.getApplicationList()
    pprint(res)
    return res


@router.get("/{application_id}")
def getApplicationById(application_id: str) -> IngestApplicationDTO:
    return service.getApplicationById(application_id)


@router.get("/{application_id}/form")
def getApplicationForm(application_id: str) -> ApplicationFormDTO:
    return service.getApplicationForm(application_id)


@router.get("/{application_id}/instance")
def getApplicationInstances(application_id: str) -> list[ApplicationInstanceDTO]:
    return service.getApplicationInstances(application_id)


@router.get("/{application_id}/instance/{instance_id}")
def getApplicationInstanceById(
    application_id: str, instance_id: str
) -> ApplicationInstanceDTO:
    return service.getApplicationInstanceById(
        application_id=application_id, instance_id=instance_id
    )


@router.get("/{application_id}/instance/{instance_id}/chart")
def getApplicationInstanceChart(
    application_id: str, instance_id: str
) -> IngestApplicationChartDataDTO:
    return service.getApplicationInstanceChart(
        application_id=application_id, instance_id=instance_id
    )


@router.post("/{application_id}/instance/s3")
def createApplicationInstance(
    application_id: str,
    createApplicationInstanceDto: Annotated[S3IngestFormDataDTO, Body()],
) -> ApplicationInstanceDTO:
    return service.createApplicationInstance(
        application_id=application_id,
        createApplicationInstanceDto=createApplicationInstanceDto,
    )


@router.websocket("/{application_id}/instance/{instance_id}/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")


@router.get("/{application_id}/pipelines")
def getApplicationPipelines(application_id: str) -> list[ApplicationPipelineDTO]:
    return service.getApplicationPipelines(application_id)
