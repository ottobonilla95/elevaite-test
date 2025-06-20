
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Literal, Any

from pydantic import BaseModel, ConfigDict

class ToolCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

class ToolCategoryCreate(ToolCategoryBase):
    pass

class ToolCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

class ToolCategoryInDB(ToolCategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class ToolCategoryResponse(ToolCategoryInDB):
    pass

class MCPServerBase(BaseModel):
    name: str
    description: Optional[str] = None
    host: str
    port: int
    protocol: str = "http"
    endpoint: Optional[str] = None
    auth_type: Optional[Literal["none", "bearer", "basic", "api_key"]] = None
    auth_config: Optional[Dict[str, Any]] = None
    health_check_interval: int = 300
    version: Optional[str] = None
    capabilities: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class MCPServerCreate(MCPServerBase):
    pass

class MCPServerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    endpoint: Optional[str] = None
    auth_type: Optional[Literal["none", "bearer", "basic", "api_key"]] = None
    auth_config: Optional[Dict[str, Any]] = None
    status: Optional[Literal["active", "inactive", "error", "maintenance"]] = None
    health_check_interval: Optional[int] = None
    version: Optional[str] = None
    capabilities: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class MCPServerInDB(MCPServerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    server_id: uuid.UUID
    status: Literal["active", "inactive", "error", "maintenance"] = "active"
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    registered_at: datetime
    last_seen: Optional[datetime] = None
    updated_at: datetime

class MCPServerResponse(MCPServerInDB):
    pass

class MCPServerRegistration(BaseModel):
    name: str
    description: Optional[str] = None
    host: str
    port: int
    protocol: str = "http"
    endpoint: Optional[str] = None
    version: Optional[str] = None
    capabilities: Optional[List[str]] = None
    tools: Optional[List[Dict[str, Any]]] = None

class ToolExecutionRequest(BaseModel):
    parameters: Dict[str, Any]

class ToolExecutionResponse(BaseModel):
    status: Literal["success", "error", "timeout"]
    result: Dict[str, Any]
    execution_time_ms: int
    tool_id: uuid.UUID
    timestamp: datetime
    error_message: Optional[str] = None

class ToolBase(BaseModel):
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
    mcp_server_id: Optional[uuid.UUID] = None
    remote_name: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[Literal["GET", "POST", "PUT", "DELETE"]] = None
    headers: Optional[Dict[str, str]] = None
    auth_required: bool = False
    category_id: Optional[uuid.UUID] = None
    tags: Optional[List[str]] = None
    documentation: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None

class ToolCreate(ToolBase):
    pass

class ToolUpdate(BaseModel):
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
    mcp_server_id: Optional[uuid.UUID] = None
    remote_name: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[Literal["GET", "POST", "PUT", "DELETE"]] = None
    headers: Optional[Dict[str, str]] = None
    auth_required: Optional[bool] = None
    category_id: Optional[uuid.UUID] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_available: Optional[bool] = None
    documentation: Optional[str] = None
    examples: Optional[List[Dict[str, Any]]] = None

class ToolInDB(ToolBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tool_id: uuid.UUID
    is_active: bool = True
    is_available: bool = True
    last_used: Optional[datetime] = None
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime

class ToolResponse(ToolInDB):
    category: Optional[ToolCategoryResponse] = None
    mcp_server: Optional[MCPServerResponse] = None
