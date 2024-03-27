from pydantic import BaseModel, Field, Extra
from typing import Literal 

class ResourceStatusUpdateDTO(BaseModel):
   action: Literal["Disable", "Enable"] = Field(..., description="Action to disable/enable resource")
   class Config:
      extra = Extra.forbid
      schema_extra = {
            "example": {
                "action": "Disable"
            }
        }
