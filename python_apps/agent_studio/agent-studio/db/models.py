import uuid
from datetime import UTC, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
    Float,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship, remote, foreign

from .database import Base


def get_utc_datetime() -> datetime:
    return datetime.now(UTC)


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
    created_time: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime, onupdate=get_utc_datetime)

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
    added_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)

    # Relationships
    workflow = relationship("Workflow", back_populates="workflow_connections")
    source_agent = relationship("Agent", foreign_keys=[source_agent_id])
    target_agent = relationship("Agent", foreign_keys=[target_agent_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "workflow_id",
            "source_agent_id",
            "target_agent_id",
            name="uix_workflow_connection",
        ),
    )


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
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
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
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    deployed_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version_number: Mapped[str] = mapped_column(String, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    prompt = relationship("Prompt")

    # Constraints
    __table_args__ = (UniqueConstraint("prompt_id", "environment", name="uix_prompt_environment"),)


class AgentExecutionMetrics(Base):
    __tablename__ = "agent_execution_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    agent_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tools_called: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tool_count: Mapped[int] = mapped_column(Integer, default=0)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    api_calls_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    agent = relationship("Agent")

    # Constraints
    __table_args__ = (UniqueConstraint("execution_id", name="uix_execution_id"),)


class ToolUsageMetrics(Base):
    __tablename__ = "tool_usage_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usage_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_execution_metrics.execution_id"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    input_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_api_called: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    api_response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    api_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    execution = relationship("AgentExecutionMetrics")


class WorkflowMetrics(Base):
    __tablename__ = "workflow_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    workflow_type: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    agents_involved: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    agent_count: Mapped[int] = mapped_column(Integer, default=1)
    total_tool_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_api_calls: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_satisfaction_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 1-5 scale
    task_completion_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0-1 scale


class SessionMetrics(Base):
    __tablename__ = "session_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_queries: Mapped[int] = mapped_column(Integer, default=0)
    successful_queries: Mapped[int] = mapped_column(Integer, default=0)
    failed_queries: Mapped[int] = mapped_column(Integer, default=0)
    agents_used: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # List of agent names used
    unique_agents_count: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
