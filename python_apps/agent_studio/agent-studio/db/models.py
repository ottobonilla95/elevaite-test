import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship, remote, foreign

from .database import Base


class Prompt(Base):
    __tablename__ = "prompts"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    # Basic prompt information
    prompt_label: Mapped[str] = mapped_column(String, nullable=False)
    prompt: Mapped[str] = mapped_column(String, nullable=False)
    sha_hash: Mapped[str] = mapped_column(String, nullable=False)
    unique_label: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    app_name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)

    # Model information
    ai_model_provider: Mapped[str] = mapped_column(String, nullable=False)
    ai_model_name: Mapped[str] = mapped_column(String, nullable=False)

    # Status and timestamps
    is_deployed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_time: Mapped[datetime] = mapped_column(DateTime, default=func.now)
    deployed_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_deployed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Additional metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    hyper_parameters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    variables: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    agents = relationship("Agent", back_populates="system_prompt")

    # Constraints
    __table_args__ = (UniqueConstraint("app_name", "prompt_label", "version", name="uix_prompt_app_label_version"),)


class Agent(Base):
    __tablename__ = "agents"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    # Basic agent information
    name: Mapped[str] = mapped_column(String, nullable=False)
    agent_type: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # router, web_search, data, troubleshooting, api, etc.
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Description of what the agent does
    parent_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=True
    )
    system_prompt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompts.pid"), nullable=False)
    persona: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Agent capabilities
    functions: Mapped[List[dict]] = mapped_column(JSONB, nullable=False)
    routing_options: Mapped[dict] = mapped_column(JSONB, nullable=False)
    short_term_memory: Mapped[bool] = mapped_column(Boolean, default=False)
    long_term_memory: Mapped[bool] = mapped_column(Boolean, default=False)
    reasoning: Mapped[bool] = mapped_column(Boolean, default=False)

    # Input/Output configuration
    input_type: Mapped[List[str]] = mapped_column(JSONB, default=["text", "voice"])
    output_type: Mapped[List[str]] = mapped_column(JSONB, default=["text", "voice"])
    response_type: Mapped[str] = mapped_column(String, default="json")

    # Execution parameters
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    timeout: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deployed: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String, default="active")
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Deployment configuration
    available_for_deployment: Mapped[bool] = mapped_column(Boolean, default=True)
    deployment_code: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Short code for deployment (e.g., "w", "h")

    # Failure handling
    failure_strategies: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    # Monitoring
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    last_active: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    collaboration_mode: Mapped[str] = mapped_column(String, default="single")

    # Relationships
    system_prompt = relationship("Prompt", back_populates="agents")

    # Self-referential relationship
    child_agents = relationship(
        "Agent",
        backref="parent",
        primaryjoin=remote(parent_agent_id) == foreign(agent_id),
    )

    # Constraints
    __table_args__ = (UniqueConstraint("name", "system_prompt_id", name="uix_agent_name_prompt"),)


class Workflow(Base):
    __tablename__ = "workflows"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    # Basic workflow information
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version: Mapped[str] = mapped_column(String, default="1.0.0")

    # Workflow configuration
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False)  # Stores the complete workflow config

    # Metadata
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now, onupdate=func.now)

    # Status and deployment
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deployed: Mapped[bool] = mapped_column(Boolean, default=False)
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Tags for categorization
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    workflow_agents = relationship("WorkflowAgent", back_populates="workflow", cascade="all, delete-orphan")
    workflow_connections = relationship("WorkflowConnection", back_populates="workflow", cascade="all, delete-orphan")
    workflow_deployments = relationship("WorkflowDeployment", back_populates="workflow")

    # Constraints
    __table_args__ = (UniqueConstraint("name", "version", name="uix_workflow_name_version"),)


class WorkflowAgent(Base):
    __tablename__ = "workflow_agents"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.workflow_id"), nullable=False)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)

    # Position and configuration in workflow
    position_x: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    position_y: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    node_id: Mapped[str] = mapped_column(String, nullable=False)  # Frontend node identifier

    # Agent-specific configuration for this workflow
    agent_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Override agent settings for this workflow

    # Metadata
    added_at: Mapped[datetime] = mapped_column(DateTime, default=func.now)

    # Relationships
    workflow = relationship("Workflow", back_populates="workflow_agents")
    agent = relationship("Agent")

    # Constraints
    __table_args__ = (
        UniqueConstraint("workflow_id", "agent_id", name="uix_workflow_agent"),
        UniqueConstraint("workflow_id", "node_id", name="uix_workflow_node_id"),
    )


class WorkflowConnection(Base):
    __tablename__ = "workflow_connections"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.workflow_id"), nullable=False)
    source_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)
    target_agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)

    # Connection configuration
    connection_type: Mapped[str] = mapped_column(String, default="default")  # e.g., "default", "conditional", "parallel"
    conditions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Conditions for conditional connections
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Order of execution for multiple connections

    # Frontend identifiers
    source_handle: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_handle: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now)

    # Relationships
    workflow = relationship("Workflow", back_populates="workflow_connections")
    source_agent = relationship("Agent", foreign_keys=[source_agent_id])
    target_agent = relationship("Agent", foreign_keys=[target_agent_id])

    # Constraints
    __table_args__ = (UniqueConstraint("workflow_id", "source_agent_id", "target_agent_id", name="uix_workflow_connection"),)


class WorkflowDeployment(Base):
    __tablename__ = "workflow_deployments"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deployment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    # Foreign keys
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("workflows.workflow_id"), nullable=False)

    # Deployment information
    environment: Mapped[str] = mapped_column(String, default="production")  # e.g., "development", "staging", "production"
    deployment_name: Mapped[str] = mapped_column(String, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(String, default="active")  # "active", "inactive", "failed"
    deployed_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Runtime configuration
    runtime_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Runtime-specific overrides

    # Monitoring
    last_executed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    workflow = relationship("Workflow", back_populates="workflow_deployments")

    # Constraints
    __table_args__ = (UniqueConstraint("deployment_name", "environment", name="uix_deployment_name_env"),)


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Version information
    prompt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompts.pid"), nullable=False)
    version_number: Mapped[str] = mapped_column(String, nullable=False)
    prompt_content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now)
    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Additional metadata
    commit_message: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    hyper_parameters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    prompt = relationship("Prompt")

    # Constraints
    __table_args__ = (UniqueConstraint("prompt_id", "version_number", name="uix_prompt_version"),)


class PromptDeployment(Base):
    __tablename__ = "prompt_deployments"

    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Deployment information
    prompt_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("prompts.pid"), nullable=False)
    environment: Mapped[str] = mapped_column(String, nullable=False)
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now)
    deployed_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version_number: Mapped[str] = mapped_column(String, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    prompt = relationship("Prompt")

    # Constraints
    __table_args__ = (UniqueConstraint("prompt_id", "environment", name="uix_prompt_environment"),)
