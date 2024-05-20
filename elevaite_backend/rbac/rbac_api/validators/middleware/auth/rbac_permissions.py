from fastapi import Depends, Body, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from pprint import pprint
from typing import Any, Optional
from rbac_api.app.errors.api_error import ApiError
from ..auth.authenticate.impl import AccessTokenAuthentication
from rbac_api.utils.deps import get_db
from elevaitedb.db import models
from elevaitedb.schemas import (
   auth as auth_schemas
)

async def validate_evaluate_rbac_permissions(
   request: Request,
   logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate), 
   # params required for pydantic validation
   account_id: Optional[UUID] = Header(None, alias='X-elevAIte-AccountId', description="account id under which rbac permissions are evaluated"),
   project_id: Optional[UUID] = Header(None, alias='X-elevAIte-ProjectId', description="project id under which rbac permissions are evaluated"),
) -> dict[str, Any]:
   db: Session = request.state.db
   try:
      return {"authenticated_entity": logged_in_user}
   except HTTPException as e:
      db.rollback()
      pprint(f'API error in POST /auth/permissions - validate_evaluate_rbac_permissions middleware: {e}')
      raise e
   except SQLAlchemyError as e:
      db.rollback()
      print(f'DB error in POST /auth/permissions - validate_evaluate_rbac_permissions middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
   except Exception as e:
      db.rollback()
      print(f'Unexpected error in POST /auth/permissions - validate_evaluate_rbac_permissions middleware: {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
