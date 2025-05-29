# import datetime
import pydantic
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

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
    uniqueLabel:str
    appName:str
    version:str
    createdTime:datetime
    deployedTime:Optional[datetime]
    last_deployed:Optional[datetime]
    modelProvider: str
    modelName: str
    isDeployed:bool
    tags: Optional[List[str]]
    hyper_parameters: Optional[Dict[str, str]]
    variables: Optional[Dict[str, str]]

class Agent(BaseModel):
    name: str
    agent_id: uuid.UUID
    parent_agent: Optional[uuid.UUID] = None
    system_prompt: PromptObject
    persona: Optional[str]
    functions: List[Dict[str, Any]]
    routing_options: Dict[str, str]
    short_term_memory: bool = False
    long_term_memory: bool = False
    reasoning: bool = False
    streaming: bool = False
    input_type: Optional[Literal["text", "voice", "image"]] = "text"
    output_type: Optional[Literal["text", "voice", "image"]] = "text"
    # Make input output type a list of types
    response_type: Optional[Literal["json", "yaml", "markdown", "HTML", "None"]] = "json"
    # agent_type: Optional[Literal["agent", "workflow"]] = "agent"

    # Execution parameters
    max_retries: int = 3
    timeout: Optional[int] = None
    deployed: bool = False
    status: Literal["active", "paused", "terminated"] = "active"
    priority: Optional[int] = None
    active_agents: Optional[List[str]] = None  # List of active agents

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



class ChatRequest(BaseModel):
    qid: uuid.UUID = Field(default_factory=uuid.UUID)
    session_id: uuid.UUID = Field(default_factory=uuid.UUID)
    user_id: str
    request: Optional[str]
    request_timestamp: Optional[datetime]
    response: Optional[str]
    response_timestamp: Optional[datetime]
    vote: int = 0
    vote_timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now())  # timezone-naive
    feedback: str = ""
    feedback_timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now())  # timezone-naive
    agent_flow_id: uuid.UUID = Field(default_factory=uuid.UUID)
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())


class AgentFlow(BaseModel):
    agent_flow_id: uuid.UUID = Field(default_factory=uuid.UUID)
    session_id: uuid.UUID = Field(default_factory=uuid.UUID)
    qid: uuid.UUID = Field(default_factory=uuid.UUID)
    user_id: str
    request: str
    response: str
    tries: int = 0
    chat_history: Optional[str] = None
    tool_calls: Optional[str] = None
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())

class MessageObject(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.UUID)
    userName: str
    isBot: bool
    text: str
    date: datetime = Field(default_factory=lambda: datetime.now())
    vote: Optional[int] = 0
    feedback:Optional[str] = ""
    feedbackfiles: Optional[List[str]] = None
    files: Optional[List[str]] = None
    media: Optional[List[str]] = None
    isStreaming: bool = False
    agentStatus: Optional[str] = None
    sources: Optional[List[str]] = None

class SessionObject(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.UUID)
    label: str
    messages: List[MessageObject]
    creationDate: datetime = Field(default_factory=lambda: datetime.now())
    summary: Optional[str] = None


