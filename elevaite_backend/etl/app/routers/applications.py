from pprint import pprint
from typing import Annotated
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session
from app.services import applications as service
from app.routers.deps import get_db
from elevaitedb.schemas import (
    application as application_schemas,
    pipeline as pipeline_schemas,
)

router = APIRouter(prefix="/application", tags=["applications"])


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
