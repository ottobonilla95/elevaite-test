"""
Database Models for Workflow Engine

SQLAlchemy models for workflow configurations, execution contexts,
step registrations, and execution history using db-core patterns.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from db_core import Base
    DB_CORE_AVAILABLE = True
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()
    DB_CORE_AVAILABLE = False


class WorkflowConfig(Base):
    """
    Workflow configuration model.
    
    Stores workflow definitions including steps, execution patterns,
    and metadata.
    """
    __tablename__ = "workflow_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    execution_pattern = Column(String(50), default="sequential")  # sequential, parallel, conditional
    
    # JSON configuration for steps and settings
    steps_config = Column(JSON, nullable=False, default=list)
    workflow_config = Column(JSON, default=dict)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    executions = relationship("WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_configs_workflow_id', 'workflow_id'),
        Index('idx_workflow_configs_created_at', 'created_at'),
        Index('idx_workflow_configs_active', 'is_active'),
    )


class StepRegistration(Base):
    """
    Step registration model.
    
    Stores registered step types and their configurations.
    """
    __tablename__ = "step_registrations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step_type = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Function reference and execution details
    function_reference = Column(String(500), nullable=False)
    execution_type = Column(String(50), default="local")  # local, rpc, api
    
    # Configuration schemas and metadata
    parameters_schema = Column(JSON, default=dict)
    response_schema = Column(JSON, default=dict)
    step_metadata = Column(JSON, default=dict)
    
    # Registration metadata
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    registered_by = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_step_registrations_step_type', 'step_type'),
        Index('idx_step_registrations_active', 'is_active'),
    )


class WorkflowExecution(Base):
    """
    Workflow execution model.
    
    Stores execution contexts and tracks workflow runs.
    """
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Workflow reference
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflow_configs.id"), nullable=False)
    workflow = relationship("WorkflowConfig", back_populates="executions")
    
    # Execution status and timing
    status = Column(String(50), default="pending")  # pending, running, completed, failed, cancelled
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # User context
    user_id = Column(String(255), nullable=False)
    session_id = Column(String(255))
    
    # Execution data and results
    input_data = Column(JSON, default=dict)
    step_io_data = Column(JSON, default=dict)
    execution_metadata = Column(JSON, default=dict)
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Relationships
    step_executions = relationship("StepExecution", back_populates="workflow_execution", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_executions_execution_id', 'execution_id'),
        Index('idx_workflow_executions_workflow_id', 'workflow_id'),
        Index('idx_workflow_executions_user_id', 'user_id'),
        Index('idx_workflow_executions_status', 'status'),
        Index('idx_workflow_executions_started_at', 'started_at'),
    )


class StepExecution(Base):
    """
    Step execution model.
    
    Stores individual step execution results and metrics.
    """
    __tablename__ = "step_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    step_execution_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Workflow execution reference
    workflow_execution_id = Column(UUID(as_uuid=True), ForeignKey("workflow_executions.id"), nullable=False)
    workflow_execution = relationship("WorkflowExecution", back_populates="step_executions")
    
    # Step details
    step_id = Column(String(255), nullable=False)
    step_type = Column(String(255), nullable=False)
    step_name = Column(String(255))
    step_order = Column(Integer)
    
    # Execution status and timing
    status = Column(String(50), default="pending")  # pending, running, completed, failed, skipped
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    execution_time_seconds = Column(Integer)
    
    # Step data
    input_data = Column(JSON, default=dict)
    output_data = Column(JSON, default=dict)
    step_config = Column(JSON, default=dict)
    
    # Error handling
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # Performance metrics
    memory_usage_mb = Column(Integer)
    cpu_usage_percent = Column(Integer)
    
    # Indexes
    __table_args__ = (
        Index('idx_step_executions_step_execution_id', 'step_execution_id'),
        Index('idx_step_executions_workflow_execution_id', 'workflow_execution_id'),
        Index('idx_step_executions_step_id', 'step_id'),
        Index('idx_step_executions_step_type', 'step_type'),
        Index('idx_step_executions_status', 'status'),
        Index('idx_step_executions_started_at', 'started_at'),
    )


class AgentConfig(Base):
    """
    Agent configuration model.
    
    Stores agent definitions and configurations.
    """
    __tablename__ = "agent_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Agent configuration
    model = Column(String(255), nullable=False)
    provider_type = Column(String(100), default="openai_textgen")
    system_prompt = Column(Text, nullable=False)
    temperature = Column(Integer, default=10)  # Store as int (0.1 = 10)
    max_tokens = Column(Integer, default=1000)
    
    # Tools and capabilities
    tools = Column(JSON, default=list)
    capabilities = Column(JSON, default=list)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_agent_configs_agent_id', 'agent_id'),
        Index('idx_agent_configs_provider_type', 'provider_type'),
        Index('idx_agent_configs_active', 'is_active'),
    )


class ToolConfig(Base):
    """
    Tool configuration model.
    
    Stores tool definitions for agents and workflows.
    """
    __tablename__ = "tool_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tool_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Tool configuration
    tool_type = Column(String(100), nullable=False)  # function, api, database, etc.
    function_reference = Column(String(500))
    api_endpoint = Column(String(500))
    
    # Configuration and schemas
    tool_config = Column(JSON, default=dict)
    input_schema = Column(JSON, default=dict)
    output_schema = Column(JSON, default=dict)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(255))
    is_active = Column(Boolean, default=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_tool_configs_tool_id', 'tool_id'),
        Index('idx_tool_configs_tool_type', 'tool_type'),
        Index('idx_tool_configs_active', 'is_active'),
    )
