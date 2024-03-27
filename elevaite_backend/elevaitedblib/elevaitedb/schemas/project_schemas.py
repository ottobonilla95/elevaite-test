from pydantic import BaseModel, Field, Extra, root_validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
from .dataset import Dataset

class ProjectType(str, Enum):
    My_Projects = "My_Projects"
    Shared_With_Me = "Shared_With_Me"
    All = "All"

class ProjectView(str, Enum):
    Hierarchical = "Hierarchical"
    Flat = "Flat"

class ProjectCreationRequestDTO(BaseModel):
    account_id: UUID = Field(...)
    name: str = Field(..., max_length=60)
    description: Optional[str] = Field(None, max_length=500)
    parent_project_id: Optional[UUID] = Field(None)
    
    class Config:
        extra = Extra.forbid
        schema_extra = {
            "example": {
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "My Project",
                "description": "Project description",
                "parent_project_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }

class ProjectPatchRequestDTO(BaseModel):
    name: Optional[str] = Field(None, max_length=60)
    description: Optional[str] = Field(None, max_length=500)
    
    class Config:
        extra = Extra.forbid
        schema_extra = {
            "example": {
                "name": "Updated Project Name",
                "description": "Updated Project Description"
            }
        }

    @root_validator(pre=True)
    @classmethod
    def check_not_all_none(cls, values):
        # Check if all values are None
        if all(value is None for value in values.values()):
            print(f"Inside PATCH /projects/project_id - ProjectPatchRequestDTO schema validation")
            raise ValueError("At least one field must be provided in payload")
        return values
    
# class UserToProjectDTO(BaseModel):
#     user_id: UUID = Field(..., description="The ID of the user to add to the project")
    
#     class Config:
#         extra = Extra.forbid
#         schema_extra = {
#             "example": {
#                 "user_id": "123e4567-e89b-12d3-a456-426614174000"
#             }
#         }

class ProjectResponseDTO(BaseModel):
    id: UUID = Field(...)
    account_id: UUID = Field(...)
    name: str = Field(..., max_length=60)
    description: Optional[str] = Field(None, max_length=500)
    project_owner_id: UUID = Field(...)
    parent_project_id: Optional[UUID] = Field(None)
    is_disabled: bool = Field(...)
    datasets: list[Dataset]
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)
    
    class Config:
        extra = Extra.forbid
        orm_mode = True
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "My Project",
                "description": "Project description",
                "project_owner_id": "123e4567-e89b-12d3-a456-426614174000",
                "parent_project_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_disabled": False,
                "datasets": [],
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z"
            }
        }
