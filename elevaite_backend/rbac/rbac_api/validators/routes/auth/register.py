from fastapi import Depends, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pprint import pprint
from typing import Optional
from rbac_api.app.errors.api_error import ApiError
from rbac_api.auth.impl import AccessTokenAuthentication
from rbac_api.utils.deps import get_db
from elevaitelib.schemas import (
    auth as auth_schemas,
    api as api_schemas,
)
from ....audit import AuditorProvider

auditor = AuditorProvider.get_instance()


@auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
async def validate_register_user(
    request: Request,
    db: Session = Depends(get_db),
    access_token_header: str = Header(
        ...,
        alias="Authorization",
        description="iDP access token with email and profile scope",
    ),
    idp_type: Optional[auth_schemas.iDPType] = Header(
        None,
        alias="idp",
        description="choice of iDP for access token. Defaults to google when not provided",
    ),
) -> None:
    """
    For now, every user is allowed to register themselves. Include whitelist validation here later.
    Returns the user_email for use in service method
    """
    try:
        try:
            await AccessTokenAuthentication.authenticate(
                request=request,
                access_token_header=access_token_header,
                idp_type=idp_type,
                db=db,
            )
        except HTTPException as e:
            if not e.detail == "User is unauthenticated":
                raise e
    except HTTPException as e:
        pprint(
            f"API error in POST /auth/register - validate_register_user middleware: {e}"
        )
        raise e
    except SQLAlchemyError as e:
        pprint(
            f"DB error in POST /auth/register - validate_register_user middleware: {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
    except Exception as e:
        print(
            f"Unexpected error in POST /auth/register - validate_register_user middleware: {e}"
        )
        request.state.source_error_msg = str(e)
        raise ApiError.serviceunavailable(
            "The server is currently unavailable, please try again later."
        )
