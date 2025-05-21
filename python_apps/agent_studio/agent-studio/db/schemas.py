import uuid
from datetime import datetime
from typing import Dict, List, Optional, Literal, Any

from pydantic import BaseModel


class PromptBase(BaseModel):
    prompt_label: str
    prompt: str
    unique_label: str
    app_name: str
    version: str
    ai_model_provider: str
    ai_model_name: str
    tags: Optional[List[str]] = None
    hyper_parameters: Optional[Dict[str, str]] = None
    variables: Optional[Dict[str, str]] = None


class PromptCreate(PromptBase):
    sha_hash: str


class PromptUpdate(BaseModel):
    prompt_label: Optional[str] = None
    prompt: Optional[str] = None
    unique_label: Optional[str] = None
    app_name: Optional[str] = None
    version: Optional[str] = None
    ai_model_provider: Optional[str] = None
    ai_model_name: Optional[str] = None
    is_deployed: Optional[bool] = None
    tags: Optional[List[str]] = None
    hyper_parameters: Optional[Dict[str, str]] = None
    variables: Optional[Dict[str, str]] = None


class PromptInDB(PromptBase):
    id: int
    pid: uuid.UUID
    sha_hash: str
    is_deployed: bool
    created_time: datetime
    deployed_time: Optional[datetime] = None
    last_deployed: Optional[datetime] = None

    class Config:
        from_attributes = True


class PromptResponse(PromptInDB):
    pass


# Base schemas for Agent
class AgentBase(BaseModel):
    name: str
    parent_agent_id: Optional[uuid.UUID] = None
    system_prompt_id: uuid.UUID
    persona: Optional[str] = None
    functions: List[Dict[str, Any]]
    routing_options: Dict[str, str]
    short_term_memory: bool = False
    long_term_memory: bool = False
    reasoning: bool = False
    input_type: List[Literal["text", "voice", "image"]] = ["text", "voice"]
    output_type: List[Literal["text", "voice", "image"]] = ["text", "voice"]
    response_type: Literal["json", "yaml", "markdown", "HTML", "None"] = "json"
    max_retries: int = 3
    timeout: Optional[int] = None
    deployed: bool = False
    status: Literal["active", "paused", "terminated"] = "active"
    priority: Optional[int] = None
    failure_strategies: Optional[List[str]] = None
    collaboration_mode: Literal["single", "team", "parallel", "sequential"] = "single"


class AgentCreate(AgentBase):
    pass


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    parent_agent_id: Optional[uuid.UUID] = None
    system_prompt_id: Optional[uuid.UUID] = None
    persona: Optional[str] = None
    functions: Optional[List[Dict[str, Any]]] = None
    routing_options: Optional[Dict[str, str]] = None
    short_term_memory: Optional[bool] = None
    long_term_memory: Optional[bool] = None
    reasoning: Optional[bool] = None
    input_type: Optional[List[Literal["text", "voice", "image"]]] = None
    output_type: Optional[List[Literal["text", "voice", "image"]]] = None
    response_type: Optional[Literal["json", "yaml", "markdown", "HTML", "None"]] = None
    max_retries: Optional[int] = None
    timeout: Optional[int] = None
    deployed: Optional[bool] = None
    status: Optional[Literal["active", "paused", "terminated"]] = None
    priority: Optional[int] = None
    failure_strategies: Optional[List[str]] = None
    collaboration_mode: Optional[Literal["single", "team", "parallel", "sequential"]] = None


class AgentInDB(AgentBase):
    id: int
    agent_id: uuid.UUID
    session_id: Optional[str] = None
    last_active: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentResponse(AgentInDB):
    system_prompt: PromptResponse


# Schemas for PromptVersion
class PromptVersionBase(BaseModel):
    prompt_id: uuid.UUID
    version_number: str
    prompt_content: str
    commit_message: Optional[str] = None
    hyper_parameters: Optional[Dict[str, str]] = None
    created_by: Optional[str] = None


class PromptVersionCreate(PromptVersionBase):
    pass


class PromptVersionInDB(PromptVersionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PromptVersionResponse(PromptVersionInDB):
    pass


# Schemas for PromptDeployment
class PromptDeploymentBase(BaseModel):
    prompt_id: uuid.UUID
    environment: str
    version_number: str
    deployed_by: Optional[str] = None


class PromptDeploymentCreate(PromptDeploymentBase):
    pass


class PromptDeploymentInDB(PromptDeploymentBase):
    id: int
    deployed_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class PromptDeploymentResponse(PromptDeploymentInDB):
    pass


# Request schemas
class PromptDeployRequest(BaseModel):
    pid: uuid.UUID
    app_name: str
    environment: str = "production"


class PromptReadRequest(BaseModel):
    app_name: str
    pid: uuid.UUID


class PromptReadListRequest(BaseModel):
    app_name: str
    prompt_label: str
