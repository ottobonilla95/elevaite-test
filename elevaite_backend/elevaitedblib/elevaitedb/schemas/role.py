from pydantic import BaseModel, Field, Extra, root_validator, validator, PrivateAttr
from typing import Optional, Literal, List, Dict, Any
from uuid import UUID
from datetime import datetime
from .permission import (
   AccountScopedRBACPermission,
)


# RoleCreationRequestDTO: Defines the structure for creating a new role with detailed permissions
class RoleCreationRequestDTO(BaseModel):
   name: str = Field(...)
   permissions: AccountScopedRBACPermission = Field(...)

   class Config:
      extra = Extra.forbid
   
# RoleUpdateRequestDTO: Defines the structure for updating an existing role's permissions
class RoleUpdateRequestDTO(BaseModel):
   name: Optional[str] = Field(None)
   permissions: Optional[AccountScopedRBACPermission] = Field(None)

   @root_validator(pre=True)
   @classmethod
   def check_not_all_none(cls, values):
      # Check if all values are None
      if all(value is None for value in values.values()):
         print(f"Inside PATCH /roles/role_id - RoleUpdateRequestDTO schema validation")
         raise ValueError("At least one field must be provided in payload")
      return values
   
   class Config:
      extra = Extra.forbid

   

class RoleResponseDTO(BaseModel):
   id: UUID = Field(...)
   name: str = Field(...)
   permissions: AccountScopedRBACPermission = Field(...)
   created_at: datetime = Field(...)
   updated_at: datetime = Field(...)
   
   class Config:
      extra = Extra.forbid
      orm_mode = True
    

class RoleListDTO(BaseModel):
   role_ids: List[UUID] = Field(..., description="The IDs of the roles in a list to be assigned to a user")
   action: Literal["Add", "Remove"] = Field(..., description = "The action to be performed with the roles")

   @validator('role_ids')
   @classmethod
   def validate_role_ids(cls, v : List[UUID]) -> List[UUID]:
      # Ensure uniqueness
      if len(v) != len(set(v)):
         print(f"Inside PATCH /users/user_id/accounts/account_id/roles - RoleListDTO schema validation")
         raise ValueError('Duplicate role IDs are not allowed')
      # Check length constraint
      if len(v) < 1 or len(v) > 10:
         print(f"Inside PATCH /users/user_id/accounts/account_id/roles - RoleListDTO schema validation")
         raise ValueError('The list of role IDs must have length between 1 and 10 (inclusive)')
      return v
   
   class Config:
      extra = Extra.forbid
      schema_extra = {
            "example": {
                "role_ids": [
                    "11111111-1111-1111-1111-111111111111",
                    "22222222-2222-2222-2222-222222222222",
                    "33333333-3333-3333-3333-333333333333"
                ],
                "action": "Add"
            }
        }
class RoleSummaryDTO(BaseModel):
   id: UUID = Field(..., description="ID of role")
   name: str = Field(..., description = "The name of the role")
   
   class Config:
      extra = Extra.forbid
      orm_mode = True
      schema_extra = {
            "example": {
                "id": "11111111-1111-1111-1111-111111111111",
                "name": "Data Scientist"
            }
        }