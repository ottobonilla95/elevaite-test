
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Literal, Any
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

from pydantic import BaseModel, ConfigDict

from .prompts import PromptResponse

class AgentBase(BaseModel):
    name: str
    agent_type: Optional[
        Literal[
            "router",
            "web_search",
            "data",
            "troubleshooting",
            "api",
            "weather",
            "toshiba",
        ]
    ] = None
    description: Optional[str] = None
    parent_agent_id: Optional[uuid.UUID] = None
    system_prompt_id: uuid.UUID
    persona: Optional[str] = None
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
    available_for_deployment: bool = True
    deployment_code: Optional[str] = None

class AgentFunctionInner(BaseModel):
    name: str

class AgentFunction(BaseModel):
    function: AgentFunctionInner

class AgentCreate(AgentBase):
    functions: List[AgentFunction]

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    agent_type: Optional[
        Literal[
            "router",
            "web_search",
            "data",
            "troubleshooting",
            "api",
            "weather",
            "toshiba",
        ]
    ] = None
    description: Optional[str] = None
    parent_agent_id: Optional[uuid.UUID] = None
    system_prompt_id: Optional[uuid.UUID] = None
    persona: Optional[str] = None
    functions: Optional[List[AgentFunction]] = None
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
    available_for_deployment: Optional[bool] = None
    deployment_code: Optional[str] = None

class AgentInDB(AgentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: uuid.UUID
    session_id: Optional[str] = None
    last_active: Optional[datetime] = None
    functions: List[ChatCompletionToolParam]

class AgentResponse(AgentInDB):
    system_prompt: PromptResponse
    functions: List[ChatCompletionToolParam]
