from pydantic import BaseModel, Field, Extra
from typing import Literal 
from pydantic import BaseModel, Field, Extra
from uuid import UUID

class StatusUpdateAction(BaseModel):
    action: Literal["Grant", "Revoke"] = Field(..., description="Action to grant or revoke status")
    class Config:
        extra = Extra.forbid
        schema_extra = {
            "example": {
                "action": "Grant"
            }
        }
