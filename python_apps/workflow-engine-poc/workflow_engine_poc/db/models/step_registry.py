"""
Step registry SQLModel definitions

This module contains all step type registration database models using SQLModel.
"""

import uuid as uuid_module
from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON, Text
from enum import Enum

from .base import BaseModel


class ExecutionType(str, Enum):
    """Step execution type enumeration"""

    LOCAL = "local"
    RPC = "rpc"
    API = "api"
    WEBHOOK = "webhook"


class StepCategory(str, Enum):
    """Step category enumeration"""

    DATA_PROCESSING = "data_processing"
    AI_LLM = "ai_llm"
    FILE_OPERATIONS = "file_operations"
    FLOW_CONTROL = "flow_control"
    INTEGRATION = "integration"
    UTILITY = "utility"


# Base step type model
class StepTypeBase(SQLModel):
    """Base step type model with common fields"""

    step_type: str = Field(
        max_length=100, unique=True, description="Unique identifier for the step type"
    )
    name: str = Field(
        max_length=255, description="Human-readable name for the step type"
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Detailed description of what this step does",
    )

    category: StepCategory = Field(
        default=StepCategory.UTILITY, description="Category this step belongs to"
    )

    execution_type: ExecutionType = Field(
        default=ExecutionType.LOCAL, description="How this step is executed"
    )

    function_reference: str = Field(
        max_length=500, description="Python function path or endpoint reference"
    )

    parameters_schema: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="JSON schema for step parameters validation",
    )

    response_schema: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="JSON schema for step response validation",
    )

    endpoint_config: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Configuration for RPC/API/webhook endpoints",
    )

    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Tags for categorizing and searching steps",
    )

    is_active: bool = Field(
        default=True, description="Whether this step type is active and available"
    )

    version: str = Field(
        default="1.0.0", max_length=50, description="Version of the step implementation"
    )

    author: Optional[str] = Field(
        default=None, max_length=255, description="Author or creator of the step type"
    )

    documentation_url: Optional[str] = Field(
        default=None, max_length=500, description="URL to detailed documentation"
    )

    example_config: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Example configuration for this step type",
    )

    # Performance and reliability metrics
    average_execution_time: Optional[float] = Field(
        default=None, description="Average execution time in seconds"
    )
    success_rate: Optional[float] = Field(
        default=None, description="Success rate as a percentage (0-100)"
    )
    total_executions: int = Field(
        default=0, description="Total number of times this step has been executed"
    )


# Database table model
class StepType(StepTypeBase, BaseModel, table=True):
    """Step type database model"""

    # External step type identifier
    step_type_id: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        unique=True,
        description="External step type identifier",
    )

    # Registration metadata
    registered_by: Optional[str] = Field(
        default=None, max_length=255, description="User who registered this step type"
    )

    last_used: Optional[str] = Field(
        default=None, description="When this step type was last used"
    )


# API schemas
class StepTypeCreate(StepTypeBase):
    """Schema for creating a new step type"""

    pass


class StepTypeRead(StepTypeBase):
    """Schema for reading step type data"""

    id: int
    uuid: uuid_module.UUID
    step_type_id: uuid_module.UUID
    created_at: str
    updated_at: Optional[str] = None
    registered_by: Optional[str] = None
    last_used: Optional[str] = None


class StepTypeUpdate(SQLModel):
    """Schema for updating step type data"""

    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = Field(default=None)
    category: Optional[StepCategory] = Field(default=None)
    execution_type: Optional[ExecutionType] = Field(default=None)
    function_reference: Optional[str] = Field(default=None, max_length=500)
    parameters_schema: Optional[Dict[str, Any]] = Field(default=None)
    response_schema: Optional[Dict[str, Any]] = Field(default=None)
    endpoint_config: Optional[Dict[str, Any]] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)
    version: Optional[str] = Field(default=None, max_length=50)
    author: Optional[str] = Field(default=None, max_length=255)
    documentation_url: Optional[str] = Field(default=None, max_length=500)
    example_config: Optional[Dict[str, Any]] = Field(default=None)


class StepTypeSummary(SQLModel):
    """Lightweight step type summary for listings"""

    id: int
    uuid: uuid_module.UUID
    step_type_id: uuid_module.UUID
    step_type: str
    name: str
    description: Optional[str]
    category: StepCategory
    execution_type: ExecutionType
    tags: List[str]
    is_active: bool
    version: str
    created_at: str

    # Usage statistics
    total_executions: int = 0
    success_rate: Optional[float] = None
    average_execution_time: Optional[float] = None
    last_used: Optional[str] = None
