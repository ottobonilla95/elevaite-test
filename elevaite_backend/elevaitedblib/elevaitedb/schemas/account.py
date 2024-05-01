from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, root_validator, Extra
from uuid import UUID
from . import common as common_schemas

class AccountCreationRequestDTO(BaseModel):
   organization_id: UUID = Field(..., description="Id of the parent organization")
   name: str = Field(..., max_length = 60, description="Name of the Account")
   description: Optional[str] = Field(None, max_length = 500, description="Brief description of the Account")
   class Config:
      extra = Extra.forbid
      schema_extra = {
            "example": {
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Account name",
                "description": "Account description"
            }
        }
      
class AccountPatchRequestDTO(BaseModel):
   name: Optional[str] = Field(None, max_length = 60, description="Name of the Account")
   description: Optional[str] = Field(None, max_length = 500, description="Brief description of the Account")
   class Config:
      extra = Extra.forbid
      schema_extra = {
            "example": {
                "name": "Updated Account Name",
                "description": "Updated Account Description"
            }
        }
      
   @root_validator(pre=True)
   @classmethod
   def check_not_all_none(cls, values):
      # Check if all values are None
      if all(value is None for value in values.values()):
         print(f"Inside PATCH /accounts/account_id - AccountPatchRequestDTO schema validation")
         raise ValueError("At least one field must be provided in payload")
      return values
    
class AccountAdminStatusUpdateDTO(common_schemas.StatusUpdateAction):
   pass

class AccountResponseDTO(BaseModel):
   id: UUID = Field(..., examples=["123e4567-e89b-12d3-a456-426614174000"])
   organization_id: UUID = Field(..., description="Id of the parent organization")
   name: str = Field(..., max_length = 60, description="Name of the Account")
   description: Optional[str] = Field(max_length = 500, description="Brief description of the Account")
   created_at: datetime = Field(...)
   updated_at: datetime = Field(...)

   class Config:
      extra = Extra.forbid
      orm_mode = True
      schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "organization_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Example Account",
                "description": "This is an example of an account description.",
                "created_at": "2022-01-01T00:00:00Z",
                "updated_at": "2022-01-02T00:00:00Z"
            }
        }


