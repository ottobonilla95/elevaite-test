import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, get_utc_datetime


class ToolCategory(Base):
    __tablename__ = "tool_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime, onupdate=get_utc_datetime)

    tools = relationship("Tool", back_populates="category")


class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    server_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    host: Mapped[str] = mapped_column(String, nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    protocol: Mapped[str] = mapped_column(String, default="http")  # http, https, ws, wss
    endpoint: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # API endpoint path

    auth_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # none, bearer, basic, api_key
    auth_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Auth configuration

    status: Mapped[str] = mapped_column(String, default="active")  # active, inactive, error, maintenance
    last_health_check: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    health_check_interval: Mapped[int] = mapped_column(Integer, default=300)  # seconds
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    capabilities: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    registered_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime, onupdate=get_utc_datetime)

    tools = relationship("Tool", back_populates="mcp_server")

    __table_args__ = (UniqueConstraint("name", name="uix_mcp_server_name"),)


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, default="1.0.0")

    tool_type: Mapped[str] = mapped_column(String, nullable=False)  # local, remote, mcp
    execution_type: Mapped[str] = mapped_column(String, default="function")  # function, api, command

    parameters_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)  # OpenAI function schema
    return_schema: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # Expected return format

    module_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Python module path
    function_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Function name

    mcp_server_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("mcp_servers.server_id"), nullable=True
    )
    remote_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Name on the remote server

    api_endpoint: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    http_method: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # GET, POST, PUT, DELETE
    headers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    auth_required: Mapped[bool] = mapped_column(Boolean, default=False)

    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tool_categories.category_id"), nullable=True
    )
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)  # Runtime availability
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    average_execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    documentation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    examples: Mapped[Optional[List[dict]]] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=get_utc_datetime, onupdate=get_utc_datetime)

    category = relationship("ToolCategory", back_populates="tools")
    mcp_server = relationship("MCPServer", back_populates="tools")

    __table_args__ = (UniqueConstraint("name", name="uix_tool_name"),)
