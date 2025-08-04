import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Float,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class AgentExecutionMetrics(Base):
    __tablename__ = "agent_execution_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False
    )
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
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

    agent = relationship("Agent")

    __table_args__ = (UniqueConstraint("execution_id", name="uix_execution_id"),)


class ToolUsageMetrics(Base):
    __tablename__ = "tool_usage_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    usage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_execution_metrics.execution_id"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    input_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_api_called: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    api_response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    api_status_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    execution = relationship("AgentExecutionMetrics")


class WorkflowMetrics(Base):
    __tablename__ = "workflow_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    workflow_type: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
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
    user_satisfaction_score: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # 1-5 scale
    task_completion_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # 0-1 scale


class WorkflowExecution(Base):
    """Complete workflow execution records with full tracing capability"""

    __tablename__ = "workflow_executions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )
    workflow_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.workflow_id"), nullable=True
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=True
    )
    execution_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'agent' or 'workflow'
    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'queued', 'running', 'completed', 'failed', 'cancelled'
    progress: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # 0.0 to 1.0
    current_step: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Input/Output data
    query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    input_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    result: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tools_called: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    estimated_completion: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )

    # User/Session info
    session_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Workflow tracing data
    current_step_index: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    execution_path: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True
    )  # List of agents executed in order
    branch_decisions: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # Decision points and outcomes

    # Relationships
    workflow = relationship("Workflow", foreign_keys=[workflow_id])
    agent = relationship("Agent", foreign_keys=[agent_id])
    steps = relationship(
        "WorkflowExecutionStep",
        back_populates="execution",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("execution_id", name="uix_workflow_execution_id"),
    )


class WorkflowExecutionStep(Base):
    """Individual steps within workflow executions with full input/output tracking"""

    __tablename__ = "workflow_execution_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    step_id: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Unique within execution
    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.execution_id"),
        nullable=False,
    )

    # Step identification
    step_type: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'agent_execution', 'tool_call', 'decision_point', 'data_processing'
    step_index: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Order within execution
    agent_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    agent_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tool_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Step status and timing
    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # 'pending', 'running', 'completed', 'failed', 'skipped'
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Input/Output data
    input_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    step_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Relationships
    execution = relationship("WorkflowExecution", back_populates="steps")

    __table_args__ = (
        UniqueConstraint("execution_id", "step_id", name="uix_execution_step"),
    )


class SessionMetrics(Base):
    __tablename__ = "session_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    start_time: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    total_queries: Mapped[int] = mapped_column(Integer, default=0)
    successful_queries: Mapped[int] = mapped_column(Integer, default=0)
    failed_queries: Mapped[int] = mapped_column(Integer, default=0)
    agents_used: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # List of agent names used
    unique_agents_count: Mapped[int] = mapped_column(Integer, default=0)
    average_response_time_ms: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )
    total_tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
