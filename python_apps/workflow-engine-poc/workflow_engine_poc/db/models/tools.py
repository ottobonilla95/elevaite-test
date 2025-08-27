"""
Tool, ToolCategory, and MCPServer SQLModel definitions (DB and API schemas)
"""

from typing import Optional, List, Dict, Any, Literal
import uuid as uuid_module
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON, DateTime, func

from .base import get_utc_datetime


# ---------- Tool Categories ----------
class ToolCategoryBase(SQLModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    tags: List[str] = []


class ToolCategoryCreate(ToolCategoryBase):
    pass


class ToolCategoryUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None


class ToolCategoryRead(ToolCategoryBase):
    id: uuid_module.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None


class ToolCategory(SQLModel, table=True):
    id: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, primary_key=True)
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    created_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now()))


# ---------- MCP Servers ----------
class MCPServerBase(SQLModel):
    name: str
    description: Optional[str] = None
    host: str
    port: int
    protocol: str = "http"  # http|https|ws|wss
    endpoint: Optional[str] = None
    auth_type: Optional[Literal["none", "bearer", "basic", "api_key"]] = None
    auth_config: Optional[Dict[str, Any]] = None
    health_check_interval: int = 300
    version: Optional[str] = None
    capabilities: Optional[List[str]] = None
    tags: Optional[List[str]] = None


class MCPServerCreate(MCPServerBase):
    pass


class MCPServerUpdate(SQLModel):
    description: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    endpoint: Optional[str] = None
    auth_type: Optional[Literal["none", "bearer", "basic", "api_key"]] = None
    auth_config: Optional[Dict[str, Any]] = None
    health_check_interval: Optional[int] = None
    version: Optional[str] = None
    capabilities: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    status: Optional[Literal["active", "inactive", "error", "maintenance"]] = None


class MCPServerRead(MCPServerBase):
    id: uuid_module.UUID
    status: Literal["active", "inactive", "error", "maintenance"] = "active"
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    registered_at: datetime
    last_seen: Optional[datetime] = None
    updated_at: datetime


class MCPServer(SQLModel, table=True):
    id: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, primary_key=True)
    name: str
    description: Optional[str] = None

    host: str
    port: int
    protocol: str = "http"
    endpoint: Optional[str] = None

    auth_type: Optional[str] = None
    auth_config: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    health_check_interval: int = 300

    version: Optional[str] = None
    capabilities: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))

    status: str = Field(default="active")
    last_health_check: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    consecutive_failures: int = 0

    registered_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    last_seen: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    updated_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )


# ---------- Tools ----------
class ToolBase(SQLModel):
    name: str
    display_name: Optional[str] = None
    description: str
    version: str = "1.0.0"
    tool_type: Literal["local", "remote", "mcp", "api"]
    execution_type: Literal["function", "api", "command"] = "function"
    parameters_schema: Dict[str, Any]
    return_schema: Optional[Dict[str, Any]] = None
    module_path: Optional[str] = None
    function_name: Optional[str] = None
    mcp_server_id: Optional[uuid_module.UUID] = None
    remote_name: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[Literal["GET", "POST", "PUT", "DELETE"]] = None
    headers: Optional[Dict[str, str]] = None
    auth_required: bool = False
    category_id: Optional[uuid_module.UUID] = None
    tags: Optional[List[str]] = None
    documentation: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None


class ToolCreate(ToolBase):
    pass


class ToolUpdate(SQLModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    tool_type: Optional[Literal["local", "remote", "mcp", "api"]] = None
    execution_type: Optional[Literal["function", "api", "command"]] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    return_schema: Optional[Dict[str, Any]] = None
    module_path: Optional[str] = None
    function_name: Optional[str] = None
    mcp_server_id: Optional[uuid_module.UUID] = None
    remote_name: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[Literal["GET", "POST", "PUT", "DELETE"]] = None
    headers: Optional[Dict[str, str]] = None
    auth_required: Optional[bool] = None
    category_id: Optional[uuid_module.UUID] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_available: Optional[bool] = None
    documentation: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None


class ToolRead(ToolBase):
    id: uuid_module.UUID
    is_active: bool = True
    is_available: bool = True
    last_used: Optional[datetime] = None
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime


class Tool(SQLModel, table=True):
    id: uuid_module.UUID = Field(default_factory=uuid_module.uuid4, primary_key=True)
    name: str
    display_name: Optional[str] = None
    description: str
    version: str = "1.0.0"
    tool_type: str
    execution_type: str = "function"
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    return_schema: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    module_path: Optional[str] = None
    function_name: Optional[str] = None
    mcp_server_id: Optional[uuid_module.UUID] = None
    remote_name: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    headers: Optional[Dict[str, str]] = Field(default=None, sa_column=Column(JSON))
    auth_required: bool = False
    category_id: Optional[uuid_module.UUID] = None
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))
    documentation: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))

    is_active: bool = True
    is_available: bool = True
    last_used: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    usage_count: int = 0

    created_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        default_factory=get_utc_datetime,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
