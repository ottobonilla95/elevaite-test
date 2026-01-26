from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, root_validator, Extra
from uuid import UUID

class OrganizationBase(BaseModel):
    name: Optional[str] = Field(None, max_length=60, description="Name of the organization")
    description: Optional[str] = Field(None, max_length=500, description="A brief description of the organization")
    
    class Config:
        extra = Extra.forbid
        schema_extra = {
            "example": {
                "name": "Organization 1",
                "description": "Description about organization"
            }
        }

class OrganizationCreationRequestDTO(OrganizationBase):
    name: str = Field(..., max_length=60, description="Name of the organization")  # Override to make it required for creation
    
    class Config:
        extra = Extra.forbid
        schema_extra = {
            "example": {
                "name": "Organization 1",
                "description": "Description about organization"
            }
        }

class OrganizationPatchRequestDTO(OrganizationBase):
    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            print("Inside PATCH /organization - OrganizationPatchRequestDTO schema validation")
            raise ValueError("At least one field must be provided in payload")
        return values
    
    class Config:
        extra = Extra.forbid
        schema_extra = {
            "example": {
                "name": "Updated Organization Name",
                "description": "Updated organization description"
            }
        }

class OrganizationResponseDTO(BaseModel):
    id: UUID = Field(...)
    name: str = Field(...)
    description: Optional[str] = Field(None)
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    class Config:
        extra = Extra.forbid
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Elevate Organization",
                "description": "An organization focusing on elevating data insights.",
                "created_at": "2022-01-01T00:00:00Z",
                "updated_at": "2022-01-02T00:00:00Z"
            }
        }
