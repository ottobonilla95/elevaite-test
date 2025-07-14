import uuid
from datetime import datetime
from typing import Dict, List, Optional, Literal, Any
from enum import Enum

from pydantic import BaseModel, ConfigDict

from .agents import AgentResponse


class ConnectionType(str, Enum):
    DEFAULT = "default"
    CONDITIONAL = "conditional"
    NOTIFICATION = "notification"
    DELAY = "delay"
    ACTION = "action"


class WorkflowBase(BaseModel):
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    configuration: Dict[str, Any]
    created_by: Optional[str] = None
    is_active: bool = True
    is_editable: bool = True
    tags: Optional[List[str]] = None


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_editable: Optional[bool] = None
    tags: Optional[List[str]] = None


class WorkflowInDB(WorkflowBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_deployed: bool
    deployed_at: Optional[datetime] = None


class WorkflowResponse(WorkflowInDB):
    workflow_agents: List["WorkflowAgentResponse"] = []
    workflow_connections: List["WorkflowConnectionResponse"] = []
    workflow_deployments: List["WorkflowDeploymentResponse"] = []


class WorkflowAgentBase(BaseModel):
    workflow_id: uuid.UUID
    agent_id: uuid.UUID
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    node_id: str
    agent_config: Optional[Dict[str, Any]] = None


class WorkflowAgentCreate(WorkflowAgentBase):
    pass


class WorkflowAgentUpdate(BaseModel):
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    node_id: Optional[str] = None
    agent_config: Optional[Dict[str, Any]] = None


class WorkflowAgentInDB(WorkflowAgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    added_at: datetime


class WorkflowAgentResponse(WorkflowAgentInDB):
    agent: AgentResponse


class WorkflowConnectionBase(BaseModel):
    workflow_id: uuid.UUID
    source_agent_id: uuid.UUID
    target_agent_id: uuid.UUID
    connection_type: ConnectionType = ConnectionType.DEFAULT
    conditions: Optional[Dict[str, Any]] = None
    priority: int = 0
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None


class WorkflowConnectionCreate(WorkflowConnectionBase):
    pass


class WorkflowConnectionUpdate(BaseModel):
    connection_type: Optional[ConnectionType] = None
    conditions: Optional[Dict[str, Any]] = None
    priority: Optional[int] = None
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None


class WorkflowConnectionInDB(WorkflowConnectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class WorkflowConnectionResponse(WorkflowConnectionInDB):
    source_agent: AgentResponse
    target_agent: AgentResponse


class WorkflowDeploymentBase(BaseModel):
    workflow_id: uuid.UUID
    environment: str = "production"
    deployment_name: str
    deployed_by: Optional[str] = None
    runtime_config: Optional[Dict[str, Any]] = None


class WorkflowDeploymentCreate(WorkflowDeploymentBase):
    pass


class WorkflowDeploymentRequest(BaseModel):
    environment: str = "production"
    deployment_name: str
    deployed_by: Optional[str] = None
    runtime_config: Optional[Dict[str, Any]] = None


class WorkflowDeploymentUpdate(BaseModel):
    status: Optional[Literal["active", "inactive", "failed"]] = None
    runtime_config: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None


class WorkflowDeploymentInDB(WorkflowDeploymentBase):
    id: int
    deployment_id: uuid.UUID
    status: Literal["active", "inactive", "failed"] = "active"
    deployed_at: datetime
    stopped_at: Optional[datetime] = None
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class WorkflowDeploymentResponse(WorkflowDeploymentInDB):
    workflow: WorkflowInDB


class WorkflowExecutionRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, str]]] = None
    runtime_overrides: Optional[Dict[str, Any]] = None


class WorkflowStreamExecutionRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, str]]] = None
    runtime_overrides: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(BaseModel):
    status: str
    response: Optional[str] = None
    execution_id: Optional[str] = None
    workflow_id: Optional[str] = None
    deployment_id: Optional[str] = None
    timestamp: Optional[str] = None
