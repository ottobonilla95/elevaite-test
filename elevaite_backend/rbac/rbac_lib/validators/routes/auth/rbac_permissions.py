from fastapi import Depends, Body, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import UUID
from pprint import pprint
from typing import Any, Optional
from rbac_api.app.errors.api_error import ApiError
from rbac_lib.auth.impl import AccessTokenAuthentication
from rbac_lib.utils.deps import get_db
from elevaitelib.orm.db import models
from elevaitelib.schemas import (
    auth as auth_schemas,
    api as api_schemas,
)
from ....audit import AuditorProvider

auditor = AuditorProvider.get_instance()


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_evaluate_rbac_permissions(
    request: Request,
    logged_in_user: models.User = Depends(AccessTokenAuthentication.authenticate),
    # params required for pydantic validation
    account_id: Optional[UUID] = Header(
        None,
        alias="X-elevAIte-AccountId",
        description="account id under which rbac permissions are evaluated",
    ),
    project_id: Optional[UUID] = Header(
        None,
        alias="X-elevAIte-ProjectId",
        description="project id under which rbac permissions are evaluated",
    ),
) -> dict[str, Any]:
    db: Session = request.state.db
    try:
        return {"authenticated_entity": logged_in_user}
    except HTTPException as e:
        db.rollback()
        pprint(
            f"API error in POST /auth/permissions - validate_evaluate_rbac_permissions middleware: {e}"
        )
        raise e
    except SQLAlchemyError as e:
        db.rollback()
        print(
            f"DB error in POST /auth/permissions - validate_evaluate_rbac_permissions middleware: {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        db.rollback()
        print(
            f"Unexpected error in POST /auth/permissions - validate_evaluate_rbac_permissions middleware: {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
