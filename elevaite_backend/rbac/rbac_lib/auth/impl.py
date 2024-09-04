from fastapi import Header, Depends, Request
from pprint import pprint
from typing import Optional
from rbac_lib.utils.api_error import ApiError
from sqlalchemy.orm import Session
from .idp.interface import IDPInterface
from .idp.factory import IDPFactory
from rbac_lib.utils.RedisSingleton import RedisSingleton
from elevaitelib.schemas import (
    auth as auth_schemas,
    api as api_schemas,
)
from elevaitelib.orm.db.models import User, Apikey
from datetime import datetime, UTC
from rbac_lib.utils.funcs import (
    make_naive_datetime_utc,
)
from rbac_lib.utils.deps import get_db
from .interface import AuthenticationInterface
from ..audit import AuditorProvider

auditor = AuditorProvider.get_instance()


class AccessTokenOrApikeyAuthentication(AuthenticationInterface):

    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    @staticmethod
    async def authenticate(
        request: Request,
        access_token_header: Optional[str] = Header(
            None,
            alias="X-elevAIte-idp-auth",
            description="iDP access token with email and profile scope",
        ),
        idp_type: Optional[auth_schemas.iDPType] = Header(
            None,
            alias="idp",
            description="choice of iDP for access token. Defaults to google when not provided",
        ),
        api_key_header: Optional[str] = Header(
            None, alias="X-elevAIte-apikey", description="API key for auth"
        ),
        db: Session = Depends(get_db),
    ) -> User | Apikey:

        request.state.db = db

        # Ensure only one method of authentication is provided
        if (access_token_header and api_key_header) or (
            not access_token_header and not api_key_header
        ):
            raise ApiError.validationerror(
                "either an iDP access token or an API key must be provided, but not both."
            )

        if access_token_header:  # access token authentication
            request.state.access_method = auth_schemas.AuthType.ACCESS_TOKEN.value
            request.state.idp = (
                idp_type if idp_type else auth_schemas.iDPType.GOOGLE.value
            )
            if not access_token_header.startswith("Bearer "):
                print(
                    f"in authenticate middleware : Request auth header must contain bearer iDP access_token for authentication"
                )
                raise ApiError.unauthorized(
                    "Request auth header must contain bearer iDP access_token for authentication"
                )

            # Get user info from google's public endpoint using token
            token = access_token_header.split(" ")[1]
            cached_email = RedisSingleton(decode_responses=True).connection.get(token)

            if cached_email is None:
                idp: IDPInterface = IDPFactory.get_idp(
                    idp_type=idp_type if idp_type else auth_schemas.iDPType.GOOGLE
                )
                email = idp.get_user_email(access_token=token)
                pprint(f"user email obtained from token successfully")
                RedisSingleton().connection.setex(token, 60 * 60, email)
            else:
                email = cached_email

            request.state.user_email = email

            logged_in_user = db.query(User).filter(User.email == email).first()
            if not logged_in_user:
                raise ApiError.unauthorized("User is unauthenticated")

            request.state.logged_in_entity_id = logged_in_user.id

            return logged_in_user

        else:  # API key authentication
            request.state.access_method = auth_schemas.AuthType.API_KEY.value
            api_key: Apikey = (
                db.query(Apikey).filter(Apikey.key == api_key_header).first()
            )
            # Check if the API key does not exist or has expired (if applicable)
            if not api_key or (
                api_key.expires_at != "NEVER"
                and make_naive_datetime_utc(api_key.expires_at) <= datetime.now(UTC)
            ):
                raise ApiError.unauthorized("invalid or expired API key")
            request.state.logged_in_entity_id = api_key.id
            return api_key


class AccessTokenAuthentication(AuthenticationInterface):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    @staticmethod
    async def authenticate(
        request: Request,
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
        db: Session = Depends(get_db),
    ) -> User:

        request.state.db = db
        request.state.access_method = auth_schemas.AuthType.ACCESS_TOKEN.value
        request.state.idp = idp_type if idp_type else auth_schemas.iDPType.GOOGLE.value

        if not access_token_header.startswith("Bearer "):  # access token authentication
            print(
                f"in authenticate middleware : Request auth header must contain bearer iDP access_token for authentication"
            )
            raise ApiError.unauthorized(
                "Request auth header must contain bearer iDP access_token for authentication"
            )

        # Get user info from google's public endpoint using token
        token = access_token_header.split(" ")[1]
        cached_email = RedisSingleton(decode_responses=True).connection.get(token)

        if cached_email is None:
            idp: IDPInterface = IDPFactory.get_idp(
                idp_type=idp_type if idp_type else auth_schemas.iDPType.GOOGLE
            )
            email = idp.get_user_email(access_token=token)
            RedisSingleton().connection.setex(token, 60 * 60, email)
        else:
            email = cached_email

        request.state.user_email = email

        logged_in_user = db.query(User).filter(User.email == email).first()
        if not logged_in_user:
            raise ApiError.unauthorized("user is unauthenticated")

        request.state.logged_in_entity_id = logged_in_user.id

        return logged_in_user


class ApikeyAuthentication(AuthenticationInterface):
    @auditor.audit(api_namespace=api_schemas.APINamespace.RBAC_API)
    @staticmethod
    async def authenticate(
        request: Request,
        api_key_header: str = Header(
            ..., alias="X-elevAIte-apikey", description="API key for auth"
        ),
        db: Session = Depends(get_db),
    ) -> Apikey:

        request.state.db = db
        request.state.access_method = auth_schemas.AuthType.API_KEY.value

        api_key: Apikey = db.query(Apikey).filter(Apikey.key == api_key_header).first()
        # Check if the API key does not exist or has expired (if applicable)
        if not api_key or (
            api_key.expires_at != "NEVER"
            and make_naive_datetime_utc(api_key.expires_at) <= datetime.now(UTC)
        ):
            raise ApiError.unauthorized("invalid or expired API key")

        request.state.logged_in_entity_id = api_key.id

        return api_key
