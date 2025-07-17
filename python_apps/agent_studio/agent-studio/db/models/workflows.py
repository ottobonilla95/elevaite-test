import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, get_utc_datetime


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    version: Mapped[str] = mapped_column(String, default="1.0.0")

    configuration: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )  # Stores the complete workflow config

    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=get_utc_datetime, onupdate=get_utc_datetime
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_deployed: Mapped[bool] = mapped_column(Boolean, default=False)
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True)

    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    workflow_agents = relationship(
        "WorkflowAgent", back_populates="workflow", cascade="all, delete-orphan"
    )
    workflow_connections = relationship(
        "WorkflowConnection", back_populates="workflow", cascade="all, delete-orphan"
    )
    workflow_deployments = relationship(
        "WorkflowDeployment", back_populates="workflow", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("name", "version", name="uix_workflow_name_version"),
    )


class WorkflowAgent(Base):
    __tablename__ = "workflow_agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.workflow_id"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False
    )

    position_x: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    position_y: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    node_id: Mapped[str] = mapped_column(
        String, nullable=False
    )  # Frontend node identifier

    agent_config: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # Override agent settings for this workflow

    added_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)

    workflow = relationship("Workflow", back_populates="workflow_agents")
    agent = relationship("Agent")

    __table_args__ = (
        UniqueConstraint("workflow_id", "agent_id", name="uix_workflow_agent"),
        UniqueConstraint("workflow_id", "node_id", name="uix_workflow_node_id"),
    )


class WorkflowConnection(Base):
    __tablename__ = "workflow_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.workflow_id"), nullable=False
    )
    source_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False
    )
    target_agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agents.agent_id"), nullable=False
    )

    connection_type: Mapped[str] = mapped_column(
        String, default="default"
    )  # e.g., "default", "conditional", "parallel"
    conditions: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # Conditions for conditional connections
    priority: Mapped[int] = mapped_column(
        Integer, default=0
    )  # Order of execution for multiple connections

    source_handle: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    target_handle: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)

    workflow = relationship("Workflow", back_populates="workflow_connections")
    source_agent = relationship("Agent", foreign_keys=[source_agent_id])
    target_agent = relationship("Agent", foreign_keys=[target_agent_id])

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    deployment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.workflow_id"), nullable=False
    )

    environment: Mapped[str] = mapped_column(
        String, default="production"
    )  # e.g., "development", "staging", "production"
    deployment_name: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[str] = mapped_column(
        String, default="active"
    )  # "active", "inactive", "failed"
    deployed_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    runtime_config: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )  # Runtime-specific overrides

    last_executed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    execution_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    workflow = relationship("Workflow", back_populates="workflow_deployments")

    __table_args__ = (
        UniqueConstraint(
            "deployment_name", "environment", name="uix_deployment_name_env"
        ),
    )
