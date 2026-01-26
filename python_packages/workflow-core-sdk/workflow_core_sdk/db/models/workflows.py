"""
Workflow SQLModel definitions

This module contains all workflow-related database models using SQLModel.
"""

import uuid as uuid_module
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON, DateTime, func
from enum import Enum

from .base import get_utc_datetime


class WorkflowStatus(str, Enum):
    """Workflow status enumeration"""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ExecutionPattern(str, Enum):
    """Workflow execution pattern enumeration"""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class ExecutionBackend(str, Enum):
    """Workflow execution backend selection"""

    LOCAL = "local"
    DBOS = "dbos"


# Base workflow model with shared fields
class WorkflowBase(SQLModel):
    """Base workflow model with common fields"""

    name: str = Field(max_length=255, description="Workflow name")
    description: Optional[str] = Field(default=None, description="Workflow description")
    version: str = Field(default="1.0.0", max_length=50, description="Workflow version")

    execution_pattern: ExecutionPattern = Field(
        default=ExecutionPattern.SEQUENTIAL,
        description="How the workflow steps should be executed",
    )

    configuration: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Complete workflow configuration including steps",
    )

    global_config: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Global configuration applied to all steps",
    )

    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Tags for categorizing workflows",
    )

    timeout_seconds: Optional[int] = Field(default=None, description="Overall workflow timeout in seconds")

    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT, description="Current workflow status")

    created_by: Optional[str] = Field(default=None, max_length=255, description="User who created the workflow")


# Database table model
class Workflow(SQLModel, table=True):
    """Workflow database model"""

    # Primary key (single UUID)
    id: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        primary_key=True,
        description="Primary workflow identifier",
    )

    # Workflow fields from WorkflowBase
    name: str = Field(max_length=255, description="Workflow name")
    description: Optional[str] = Field(default=None, description="Workflow description")
    version: str = Field(default="1.0.0", max_length=50, description="Workflow version")

    execution_pattern: ExecutionPattern = Field(
        default=ExecutionPattern.SEQUENTIAL,
        description="How the workflow steps should be executed",
    )

    configuration: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Complete workflow configuration including steps",
    )

    global_config: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Global configuration applied to all steps",
    )

    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Tags for categorizing workflows",
    )

    timeout_seconds: Optional[int] = Field(default=None, description="Overall workflow timeout in seconds")

    status: WorkflowStatus = Field(default=WorkflowStatus.DRAFT, description="Current workflow status")

    created_by: Optional[str] = Field(default=None, max_length=255, description="User who created the workflow")

    # Timestamps
    created_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
        description="When the record was created",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now()),
        description="When the record was last updated",
    )

    # Relationships will be added later when we set up proper foreign keys


# API schemas
class WorkflowCreate(WorkflowBase):
    """Schema for creating a new workflow"""

    pass


class WorkflowRead(WorkflowBase):
    """Schema for reading workflow data"""

    id: uuid_module.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Optional execution summary
    total_executions: Optional[int] = Field(default=None, description="Total number of executions")
    successful_executions: Optional[int] = Field(default=None, description="Number of successful executions")
    last_executed: Optional[datetime] = Field(default=None, description="Last execution timestamp")


class WorkflowUpdate(SQLModel):
    """Schema for updating workflow data"""

    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    version: Optional[str] = Field(default=None, max_length=50)
    execution_pattern: Optional[ExecutionPattern] = Field(default=None)
    configuration: Optional[Dict[str, Any]] = Field(default=None)
    global_config: Optional[Dict[str, Any]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    timeout_seconds: Optional[int] = Field(default=None)
    status: Optional[WorkflowStatus] = Field(default=None)


class WorkflowSummary(SQLModel):
    """Lightweight workflow summary for listings"""

    id: uuid_module.UUID
    name: str
    description: Optional[str]
    version: str
    status: WorkflowStatus
    execution_pattern: ExecutionPattern
    created_at: str
    created_by: Optional[str]
    tags: List[str]

    # Execution statistics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    last_executed: Optional[str] = None
