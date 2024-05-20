from typing import List, Sequence, Any, Dict, Type, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session, Query
from ..services import applications as service
from .deps import get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
    application as application_schemas,
    pipeline as pipeline_schemas,
)

# from rbac_api import (
#    routes_to_middleware_imple_map,
#    rbac_instance
# )
 
router = APIRouter(prefix="/application", tags=["applications"])


@router.get("", response_model=list[application_schemas.Application])
def getApplicationList(
    # request: Request,  # uncomment this when using validator
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(routes_to_middleware_imple_map['getApplicationList']), # uncomment this to use validator
) -> Sequence[application_schemas.Application]:

    # db: Session = request.state.db # uncomment this when using validator
    # all_query_authorized_types_filter_function = rbac_instance.get_post_validation_types_filter_function_for_all_query(models.Application, validation_info) # uncomment this when using validator
    
    return service.getApplicationList(
        db,
        # filter_function=all_query_authorized_types_filter_function # uncomment this when using validator
    )


@router.get("/{application_id}", response_model=application_schemas.Application)
def getApplicationById(
    application_id: int,
    db: Session = Depends(get_db) # comment this when using validator
    # validation_info:dict[str, Any] = Depends(routes_to_middleware_imple_map['getApplicationById']), # uncomment this to use validator,
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
    # request: Request, # uncomment this when using validator
    application_id: int,
    db: Session = Depends(get_db), # comment this when using validator
    # validation_info:dict[str, Any] = Depends(routes_to_middleware_imple_map['getApplicationPipelines']), # uncomment this to use validator
) -> Sequence[pipeline_schemas.Pipeline]:
    # db: Session = request.state.db #uncomment this when using validator
    return service.getApplicationPipelines(db, application_id)
