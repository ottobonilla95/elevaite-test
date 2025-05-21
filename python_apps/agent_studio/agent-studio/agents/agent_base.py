from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
import uuid
from pydantic import BaseModel
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from data_classes import PromptObject


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
    input_type: Optional[List[Literal["text", "voice", "image"]]] = ["text", "voice"]
    output_type: Optional[List[Literal["text", "voice", "image"]]] = ["text", "voice"]
    response_type: Optional[Literal["json", "yaml", "markdown", "HTML", "None"]] = "json"

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
    def execute(self, *args, **kwargs) -> Any:
        """Execution script for each component."""
        raise NotImplementedError("Component execution logic should be implemented in subclasses.")
