from enum import Enum
from pydantic import BaseModel, Field, validator, Extra, Field
from typing import Optional, Union, Literal
from datetime import datetime, timezone
import uuid
from ..util.func import (
    get_utc_datetime,
    make_naive_datetime_utc,
)
from .permission import (
    ApikeyScopedRBACPermission,
)


class ApikeyPermissionsType(str, Enum):
    CLONED = "cloned"
    CUSTOM = "custom"


class ApikeyCreate(BaseModel):
    name: str = Field(..., max_length=20, description="api key name")
    permissions_type: ApikeyPermissionsType
    permissions: ApikeyScopedRBACPermission = Field(default=dict())
    expires_at: Union[datetime, Literal["NEVER"]] = Field(
        description='Expiration date or "NEVER" for no expiration.'
    )

    @validator("expires_at")
    @classmethod
    def check_expires_at(
        cls, v: Union[datetime, Literal["NEVER"]]
    ) -> Union[datetime, Literal["NEVER"]]:
        if v != "NEVER":
            v = make_naive_datetime_utc(v)
            if v <= get_utc_datetime():
                raise ValueError("expires_at must be a future date.")
        return v

    class Config:
        extra = Extra.forbid


class ApikeyBaseResponse(
    BaseModel
):  # key field, cloned_user_id and cloned_apikey_id fields excluded
    id: uuid.UUID
    name: str
    creator_id: uuid.UUID
    project_id: uuid.UUID
    permissions: ApikeyScopedRBACPermission
    permissions_type: ApikeyPermissionsType
    created_at: datetime
    expires_at: datetime

    class Config:
        orm_mode = True


class ApikeyGetResponseDTO(ApikeyBaseResponse):
    pass


class ApikeyCreateResponseDTO(ApikeyBaseResponse):
    key: str
