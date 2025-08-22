"""
Workflow execution SQLModel definitions

This module contains all execution-related database models using SQLModel.
Uses the simplified approach: single table model + response models that extend it.
"""

import uuid as uuid_module
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum

from .base import get_utc_datetime


class ExecutionStatus(str, Enum):
    """Execution status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class StepStatus(str, Enum):
    """Step execution status enumeration"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


# Base class with common fields (no table=True)
class WorkflowExecutionBase(SQLModel):
    """Base workflow execution model with common fields"""

    # Foreign key to workflow
    workflow_id: uuid_module.UUID = Field(
        description="ID of the workflow being executed"
    )

    # User context
    user_id: Optional[str] = Field(
        default=None, max_length=255, description="User who triggered the execution"
    )
    session_id: Optional[str] = Field(
        default=None, max_length=255, description="Session ID for tracking"
    )
    organization_id: Optional[str] = Field(
        default=None, max_length=255, description="Organization ID"
    )

    # Execution state
    status: ExecutionStatus = Field(
        default=ExecutionStatus.PENDING, description="Current execution status"
    )

    # Data fields (as regular Dict for base class)
    input_data: Dict[str, Any] = Field(
        default_factory=dict, description="Initial input data for the workflow"
    )
    output_data: Dict[str, Any] = Field(
        default_factory=dict, description="Final output data from the workflow"
    )
    step_io_data: Dict[str, Any] = Field(
        default_factory=dict, description="Input/output data for all steps"
    )
    execution_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Execution metadata and analytics"
    )

    # Error handling
    error_message: Optional[str] = Field(
        default=None, description="Error message if execution failed"
    )

    # Timing
    started_at: Optional[datetime] = Field(
        default=None, description="When execution started"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When execution completed"
    )
    execution_time_seconds: Optional[float] = Field(
        default=None, description="Total execution time in seconds"
    )


# Database table model (inherits base + adds table-specific fields)
class WorkflowExecution(WorkflowExecutionBase, table=True):
    """Workflow execution database model"""

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # UUID fields
    uuid: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        sa_column=Column(UUID(as_uuid=True), unique=True, nullable=False),
        description="Internal unique identifier",
    )
    execution_id: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        sa_column=Column(UUID(as_uuid=True), unique=True, nullable=False),
        description="External execution identifier",
    )

    # Override data fields with SQLAlchemy columns for database storage
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Initial input data for the workflow",
    )
    output_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Final output data from the workflow",
    )
    step_io_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Input/output data for all steps",
    )
    execution_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Execution metadata and analytics",
    )

    # Override error_message with Text column for longer messages
    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Error message if execution failed",
    )

    # Foreign key to workflow
    workflow_id: uuid_module.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), nullable=False),
        description="ID of the workflow being executed",
    )

    # User context
    user_id: Optional[str] = Field(
        default=None, max_length=255, description="User who triggered the execution"
    )
    session_id: Optional[str] = Field(
        default=None, max_length=255, description="Session ID for tracking"
    )
    organization_id: Optional[str] = Field(
        default=None, max_length=255, description="Organization ID"
    )

    # Execution state
    status: ExecutionStatus = Field(
        default=ExecutionStatus.PENDING, description="Current execution status"
    )

    # Data fields
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Initial input data for the workflow",
    )
    output_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Final output data from the workflow",
    )
    step_io_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Input/output data for all steps",
    )
    execution_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Execution metadata and analytics",
    )

    # Error handling
    error_message: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Error message if execution failed",
    )

    # Timing
    started_at: Optional[datetime] = Field(
        default=None, description="When execution started"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When execution completed"
    )
    execution_time_seconds: Optional[float] = Field(
        default=None, description="Total execution time in seconds"
    )

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


# Step base class (moved here before table model)
class StepExecutionBase(SQLModel):
    """Base step execution model with common fields"""

    # Foreign key to workflow execution
    workflow_execution_id: uuid_module.UUID = Field(
        description="ID of the workflow execution"
    )

    # Step identification
    step_id: str = Field(
        max_length=255, description="ID of the step from workflow configuration"
    )
    step_name: str = Field(max_length=255, description="Name of the step")
    step_type: str = Field(max_length=100, description="Type of step being executed")

    # Execution state
    status: StepStatus = Field(
        default=StepStatus.PENDING, description="Current step status"
    )

    # Data fields
    input_data: Dict[str, Any] = Field(
        default_factory=dict, description="Input data for the step"
    )
    output_data: Dict[str, Any] = Field(
        default_factory=dict, description="Output data from the step"
    )
    step_config: Dict[str, Any] = Field(
        default_factory=dict, description="Step configuration used for execution"
    )

    # Error handling
    error_message: Optional[str] = Field(
        default=None, description="Error message if step failed"
    )

    # Timing and execution details
    started_at: Optional[datetime] = Field(
        default=None, description="When step execution started"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When step execution completed"
    )
    execution_time_seconds: Optional[float] = Field(
        default=None, description="Step execution time in seconds"
    )
    retry_count: int = Field(
        default=0, description="Number of times this step was retried"
    )
    step_order: Optional[int] = Field(
        default=None, description="Order of execution within the workflow"
    )


# Step execution table model (inherits base + adds table-specific fields)
class StepExecution(StepExecutionBase, table=True):
    """Step execution database model"""

    # Primary key
    id: Optional[int] = Field(default=None, primary_key=True)

    # UUID field
    uuid: uuid_module.UUID = Field(
        default_factory=uuid_module.uuid4,
        sa_column=Column(UUID(as_uuid=True), unique=True, nullable=False),
        description="Internal unique identifier",
    )

    # Foreign key to workflow execution
    workflow_execution_id: uuid_module.UUID = Field(
        sa_column=Column(UUID(as_uuid=True), nullable=False),
        description="ID of the workflow execution",
    )

    # Step identification
    step_id: str = Field(
        max_length=255, description="ID of the step from workflow configuration"
    )
    step_name: str = Field(max_length=255, description="Name of the step")
    step_type: str = Field(max_length=100, description="Type of step being executed")

    # Execution state
    status: StepStatus = Field(
        default=StepStatus.PENDING, description="Current step status"
    )

    # Data fields
    input_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Input data for the step",
    )
    output_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Output data from the step",
    )
    step_config: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Step configuration used for execution",
    )

    # Error handling
    error_message: Optional[str] = Field(
        default=None, sa_column=Column(Text), description="Error message if step failed"
    )

    # Timing and execution details
    started_at: Optional[datetime] = Field(
        default=None, description="When step execution started"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="When step execution completed"
    )
    execution_time_seconds: Optional[float] = Field(
        default=None, description="Step execution time in seconds"
    )
    retry_count: int = Field(
        default=0, description="Number of times this step was retried"
    )
    step_order: Optional[int] = Field(
        default=None, description="Order of execution within the workflow"
    )

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


# API Response models that extend the base models (not table models)
class WorkflowExecutionRead(WorkflowExecutionBase):
    """Schema for reading workflow execution data"""

    # Add the ID fields that are in the table model
    id: int
    uuid: uuid_module.UUID
    execution_id: uuid_module.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Optional step summary (computed fields)
    total_steps: Optional[int] = Field(
        default=None, description="Total number of steps"
    )
    completed_steps: Optional[int] = Field(
        default=None, description="Number of completed steps"
    )
    failed_steps: Optional[int] = Field(
        default=None, description="Number of failed steps"
    )


class StepExecutionRead(StepExecutionBase):
    """Schema for reading step execution data"""

    # Add the ID fields that are in the table model
    id: int
    uuid: uuid_module.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


# API Update models (only include fields that can be updated)
class WorkflowExecutionUpdate(SQLModel):
    """Schema for updating workflow execution data"""

    status: Optional[ExecutionStatus] = Field(default=None)
    output_data: Optional[Dict[str, Any]] = Field(default=None)
    step_io_data: Optional[Dict[str, Any]] = Field(default=None)
    execution_metadata: Optional[Dict[str, Any]] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    execution_time_seconds: Optional[float] = Field(default=None)


class StepExecutionUpdate(SQLModel):
    """Schema for updating step execution data"""

    status: Optional[StepStatus] = Field(default=None)
    output_data: Optional[Dict[str, Any]] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    execution_time_seconds: Optional[float] = Field(default=None)
    retry_count: Optional[int] = Field(default=None)
