from typing import Optional, Dict, List, Any, Literal
import uuid
import pydantic
from pydantic import BaseModel
from datetime import datetime
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam


class PromptReadListRequest(pydantic.BaseModel):
    app_name: str
    prompt_label: str


class PromptReadDeployedRequest(pydantic.BaseModel):
    app_name: str
    prompt_label: str


class PromptReadRequest(pydantic.BaseModel):
    app_name: str
    pid: uuid.UUID


class PromptObjectRequest(pydantic.BaseModel):
    """
    pid: randomUUID(),
    app_name: appName,
    vendor: selectedVendor,
    model_name: selectedModelName,
    prompt_label: selectedPromptLabel,
    prompt: selectedPrompt,
    hash: hash,
    temperature: temperature,
    max_tokens: maxTokens,
    version: version,
    is_deployed: false,
    deployed_time: new Date().toISOString(),
    """

    pid: uuid.UUID
    is_system_prompt: Optional[bool]
    app_name: str
    vendor: str
    model_name: str
    prompt_label: str
    prompt: str
    hash: str
    temperature: str
    max_tokens: str
    version: Optional[str]
    tags: Optional[List[str]]
    is_deployed: Optional[bool]
    hyper_parameters: Optional[Dict[str, str]]
    variables: Optional[List[str]]
    deployed_time: Optional[datetime]


class PromptDeployRequest(pydantic.BaseModel):
    """
    pid: randomUUID(),
    app_name: appName,
    """

    pid: uuid.UUID
    app_name: str


class PromptObject(pydantic.BaseModel):
    pid: uuid.UUID
    prompt_label: str
    prompt: str
    sha_hash: str
    uniqueLabel: str
    appName: str
    version: str
    createdTime: datetime
    deployedTime: Optional[datetime]
    last_deployed: Optional[datetime]
    modelProvider: str
    modelName: str
    isDeployed: bool
    tags: Optional[List[str]]
    hyper_parameters: Optional[Dict[str, str]]
    variables: Optional[Dict[str, str]]


class Agent(BaseModel):
    name: str
    agent_id: uuid.UUID
    parent_agent: Optional[uuid.UUID] = None
    system_prompt: PromptObject
    persona: Optional[str]
    functions: List[ChatCompletionToolParam]
    routing_options: Dict[str, str]
    short_term_memory: bool = False
    long_term_memory: bool = False
    reasoning: bool = False
    # input_type: Optional[Literal["text", "voice", "image"]] = "text"
    # output_type: Optional[Literal["text", "voice", "image"]] = "text"
    # Make input output type a list of types
    input_type: Optional[List[Literal["text", "voice", "image"]]] = ["text", "voice"]
    output_type: Optional[List[Literal["text", "voice", "image"]]] = ["text", "voice"]
    response_type: Optional[Literal["json", "yaml", "markdown", "HTML", "None"]] = "json"
    # agent_type: Optional[Literal["agent", "workflow"]] = "agent"

    # Execution parameters
    max_retries: int = 3
    timeout: Optional[int] = None
    deployed: bool = False
    status: Literal["active", "paused", "terminated"] = "active"
    priority: Optional[int] = None

    # Agent, Human or Parent Agent
    failure_strategies: Optional[List[str]]

    # Logging and monitoring
    session_id: Optional[str] = None
    last_active: Optional[datetime] = None
    # logging_level: Optional[Literal["debug", "info", "warning", "error"]] = "info"  # Debug level

    collaboration_mode: Optional[Literal["single", "team", "parallel", "sequential"]] = "single"  # Multi-agent behavior

    # Add a function to import the right prompt for the agent.
    def execute(self, **kwargs) -> Any:
        """Execution script for each component."""
        raise NotImplementedError("Component execution logic should be implemented in subclasses.")
