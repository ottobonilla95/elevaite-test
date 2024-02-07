import os
from pprint import pprint
from typing import Annotated
from dotenv import load_dotenv
from fastapi import APIRouter, Body, Depends, Form, WebSocket, WebSocketDisconnect
import pika

from app.util.models import (
    ApplicationFormDTO,
    ApplicationInstanceDTO,
    ApplicationPipelineDTO,
    IngestApplicationChartDataDTO,
    IngestApplicationDTO,
    PreProcessFormDTO,
    S3IngestFormDataDTO,
)
from app.services import applications as service
from app.util.websockets import ConnectionManager

router = APIRouter(prefix="/application", tags=["applications"])
manager = ConnectionManager()


def get_rabbitmq_connection():
    load_dotenv()
    RABBITMQ_USER = os.getenv("RABBITMQ_USER")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
    RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST")
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=5672,
            heartbeat=600,
            blocked_connection_timeout=300,
            credentials=credentials,
            virtual_host=RABBITMQ_VHOST,
        )
    )
    channel = connection.channel()
    channel.queue_declare("s3_ingest")
    channel.queue_declare("preprocess")

    try:
        yield connection
    finally:
        connection.close()


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
    rmq: pika.BlockingConnection = Depends(get_rabbitmq_connection),
) -> ApplicationInstanceDTO:
    return service.createApplicationInstance(
        application_id=application_id,
        createApplicationInstanceDto=createApplicationInstanceDto,
        rmq=rmq,
    )


@router.post("/{application_id}/instance/")
def createApplicationInstance(
    application_id: str,
    createApplicationInstanceDto: Annotated[
        S3IngestFormDataDTO | PreProcessFormDTO, Body()
    ],
    rmq: pika.BlockingConnection = Depends(get_rabbitmq_connection),
) -> ApplicationInstanceDTO:
    return service.createApplicationInstance(
        application_id=application_id,
        createApplicationInstanceDto=createApplicationInstanceDto,
        rmq=rmq,
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
