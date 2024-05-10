from pydantic import BaseModel,EmailStr, Field, Extra, root_validator, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from enum import Enum

from . import (
   common as common_schemas,
   user as user_schemas,
   dataset as dataset_schemas,
   role as role_schemas
)
class ProjectType(str, Enum):
    My_Projects = "My_Projects"
    Shared_With_Me = "Shared_With_Me"
    All = "All"

class ProjectView(str, Enum):
    Hierarchical = "Hierarchical"
    Flat = "Flat"

class ProjectCreationRequestDTO(BaseModel):
    name: str = Field(..., max_length=60)
    description: Optional[str] = Field(None, max_length=500)
    
    class Config:
        extra = Extra.forbid
        schema_extra = {
            "example": {
                "name": "My Project",
                "description": "Project description",
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
    
class ProjectAdminStatusUpdateDTO(common_schemas.StatusUpdateAction):
   pass

class ProjectResponseDTO(BaseModel):
    id: UUID = Field(...)
    account_id: UUID = Field(...)
    name: str = Field(..., max_length=60)
    description: Optional[str] = Field(None, max_length=500)
    creator: EmailStr = Field(...)
    parent_project_id: Optional[UUID] = Field(None)
    datasets: list[dataset_schemas.Dataset]
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
                "creator": "example@gmail.com",
                "parent_project_id": "123e4567-e89b-12d3-a456-426614174000",
                "datasets": [],
                "created_at": "2023-01-01T12:00:00Z",
                "updated_at": "2023-01-01T12:00:00Z"
            }
        }

class ProjectAssigneeDTO(BaseModel):
    user_id: UUID = Field(..., description="The ID of the user to be assigned to a project")
    permission_overrides: role_schemas.ProjectScopedPermission = Field(description='Optional Project-scoped permission overrides', default_factory=role_schemas.ProjectScopedPermission)

    class Config:
        extra = Extra.forbid

class ProjectAssigneeListDTO(BaseModel):
    assignees: List[ProjectAssigneeDTO] = Field(..., description="List of project assignees")

    @validator('assignees')
    @classmethod
    def validate_assignees(cls, v : List[ProjectAssigneeDTO]) -> List[ProjectAssigneeDTO]:
        # Ensure uniqueness of user_id's
        user_ids_seen = set()
        for assignee in v:
            if assignee.user_id in user_ids_seen:
                raise ValueError('Duplicate project assignee IDs are not allowed')
            user_ids_seen.add(assignee.user_id)
        # Check length constraint
        if len(v) < 1 or len(v) > 50:
            print(f"Inside ProjectAssigneeListDTO schema validation")
            raise ValueError('The list of project assignee IDs must have length between 1 and 50 (inclusive)')
        return v

    class Config:
        extra = Extra.forbid