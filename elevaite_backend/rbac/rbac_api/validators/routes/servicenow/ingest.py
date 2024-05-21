from fastapi import Depends, HTTPException, Header, Request, Path
from uuid import UUID
from rbac_api.auth.impl import (
   AccessTokenOrApikeyAuthentication
)
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pprint import pprint
from typing import Any, Type
from rbac_api.app.errors.api_error import ApiError
 
from elevaitedb.db import models
from ...main import RBACProvider
import inspect

def validate_servicenow_tickets_ingest_factory(target_model_class : Type[models.Base], target_model_action_sequence: tuple[str, ...]):
   async def validate_servicenow_tickets_ingest(
      request: Request,
      # The params below are required for pydantic validation even when unused
      project_id: UUID = Header(..., alias = "X-elevAIte-ProjectId", description="The ID of the project under which servicenow ingest is done"),
      authenticated_entity: models.User | models.Apikey = Depends(AccessTokenOrApikeyAuthentication.authenticate), 
   ) -> dict[str, Any]:
      db: Session = request.state.db
      try: 
         # Set the context flags in request.state
         current_frame = inspect.currentframe()
         if current_frame and current_frame.f_locals:   
            frame_locals = current_frame.f_locals
            request.state.account_context_exists = 'account_id' in frame_locals
            request.state.project_context_exists = 'project_id' in frame_locals
         else:
            request.state.account_context_exists = False
            request.state.project_context_exists = False

         return await RBACProvider.get_instance().validate_rbac_permissions(
            request=request,
            db=db,
            target_model_action_sequence=target_model_action_sequence,
            authenticated_entity=authenticated_entity,
            target_model_class=target_model_class
         )
      except HTTPException as e:
         db.rollback()
         pprint(f'API error in POST /servicenow/ingest - validate_servicenow_ingest middleware : {e}')
         raise e
      except SQLAlchemyError as e:
         db.rollback()
         pprint(f'DB error in POST /servicenow/ingest validate_servicenow_ingest middleware: {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
      except Exception as e:
         db.rollback()
         print(f'Unexpected error in POST /servicenow/ingest - validate_servicenow_ingest middleware : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   return validate_servicenow_tickets_ingest