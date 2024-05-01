from typing import List, Sequence, Any, Dict
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ..services import applications as service
from .deps import get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
    application as application_schemas,
    pipeline as pipeline_schemas,
)

from rbac_api import (
   validators,
   rbac_instance
)

router = APIRouter(prefix="/application", tags=["applications"])


@router.get("", response_model=list[application_schemas.Application])
def getApplicationList(
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connectors_factory(models.Application, ("READ",))) # uncomment this to use validator
) -> Sequence[application_schemas.Application]:

    # db: Session = validation_info.get("db", None) # uncomment this when using validator
    
    # typenames = validation_info.get("target_entity_typename_combinations", tuple()) # uncomment this when using validator
    # typevalues = validation_info.get("target_entity_typevalue_combinations", tuple()) # uncomment this when using validator

    # filters_list: List[Dict[str, Any]] = rbac_instance.generate_post_validation_type_filters_for_all_query(models.Application, typenames, typevalues, validation_info) # uncomment this when using validator
    
    return service.getApplicationList(
        db,
        # filters_list=filters_list # uncomment this when using validator
    )


@router.get("/{application_id}", response_model=application_schemas.Application)
def getApplicationById(
    application_id: int,
    db: Session = Depends(get_db) # comment this when using validator
    # validation_info:dict[str, Any] = Depends(validators.validate_get_connector_factory(models.Application, ("READ",))) # uncomment this to use validator
) -> application_schemas.Application:

    # application = validation_info.get("Application", None) # uncomment this when using validator
    # return application # uncomment this when using validator

    return service.getApplicationById(db, application_id) # comment this when using validator


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
