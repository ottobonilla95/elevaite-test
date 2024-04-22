from typing import List, Sequence, Any
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ..services import applications as service
from .deps import get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
    application as application_schemas,
    pipeline as pipeline_schemas,
)
from rbac_api import validators
# from rbac_api.app.errors.api_error import ApiError
router = APIRouter(prefix="/application", tags=["applications"])


@router.get("", response_model=list[application_schemas.Application])
def getApplicationList(
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connectors_factory(models.Application, ("READ",))) # uncomment this to use validator
) -> Sequence[application_schemas.Application]:
    # uncomment lines below when using validator

    # db: Session = validation_info.get("db", None)
    # authorized_app_types: list[application_schemas.ApplicationType] = []
    # for app_type in application_schemas.ApplicationType:
    #     app_type_errors = validation_info.get(f'applicationType_{app_type.value}', None)
    #     if not app_type_errors:
    #         authorized_app_types.append(app_type)
    
    return service.getApplicationList(
        db,
        # authorized_app_types # uncomment this when using validator
    )


@router.get("/{application_id}", response_model=application_schemas.Application)
def getApplicationById(
    application_id: int,
    db: Session = Depends(get_db) # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connector_factory(models.Application, ("READ",))) # uncomment this to use validator
) -> application_schemas.Application:
    # un comment lines below when using validator

    # application = validation_info.get("Application", None)
    # return application

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
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connector_pipelines_factory(models.Application, ("READ",))), #uncomment this to use validator
    db: Session = Depends(get_db) # comment this when using validator
) -> Sequence[pipeline_schemas.Pipeline]:
    # db: Session = validation_info.get("db", None) #uncomment this when using validator
    return service.getApplicationPipelines(db, application_id)
