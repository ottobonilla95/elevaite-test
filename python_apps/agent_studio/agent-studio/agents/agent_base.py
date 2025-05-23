from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional
import uuid
from pydantic import BaseModel, Field
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from data_classes import PromptObject

# Import Redis utilities
from redis_utils import redis_manager


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
    response_type: Optional[Literal["json", "yaml", "markdown", "HTML", "None"]] = (
        "json"
    )

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

    collaboration_mode: Optional[
        Literal["single", "team", "parallel", "sequential"]
    ] = "single"  # Multi-agent behavior

    # Redis communication settings
    stream_name: Optional[str] = None
    consumer_group: str = "agent_group"
    consumer_name: Optional[str] = None
    message_handlers: Dict[str, Callable] = Field(default_factory=dict)

    # Add a function to import the right prompt for the agent.
    def execute(self, **kwargs) -> Any:
        """Execution script for each component."""
        raise NotImplementedError(
            "Component execution logic should be implemented in subclasses."
        )

    def initialize_redis_communication(self):
        """Initialize Redis communication for the agent."""
        # Set default stream name if not provided
        if not self.stream_name:
            self.stream_name = f"agent:{self.name.lower()}"

        # Set default consumer name if not provided
        if not self.consumer_name:
            self.consumer_name = f"{self.name.lower()}_{str(self.agent_id)[:8]}"

        # Create stream and consumer group
        redis_manager.create_stream(self.stream_name)
        redis_manager.create_consumer_group(self.stream_name, self.consumer_group)

        # Register default message handler
        self.register_message_handler(self._default_message_handler)

    def register_message_handler(
        self, handler: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]
    ):
        """Register a message handler function."""
        # Start consuming messages with the handler
        if self.stream_name is not None:
            redis_manager.consume_messages(
                self.stream_name,
                handler,
                group_name=self.consumer_group,
                consumer_name=self.consumer_name,
            )

    def _default_message_handler(
        self, message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Default message handler that processes incoming messages."""
        try:
            # Extract message data
            data = message.get("data", {})
            msg_type = data.get("type", "unknown")

            # Check if we have a specific handler for this message type
            if msg_type in self.message_handlers:
                return self.message_handlers[msg_type](data)

            # Default processing logic
            if "query" in data:
                # Process query using execute method
                result = self.execute(query=data["query"])
                return {"result": result}

            # Log unhandled message
            print(f"Agent {self.name} received unhandled message: {data}")
            return None

        except Exception as e:
            print(f"Error handling message in agent {self.name}: {e}")
            return {"error": str(e)}

    def send_message(
        self, target_stream: str, message: Dict[str, Any], priority: int = 0
    ) -> Optional[str]:
        """Send a message to another agent's stream."""
        return redis_manager.publish_message(target_stream, message, priority=priority)

    def request_reply(
        self, target_stream: str, message: Dict[str, Any], timeout: int = 5
    ) -> Optional[Dict[str, Any]]:
        """Send a request to another agent and wait for a reply."""
        return redis_manager.request_reply(
            target_stream, message, timeout=timeout, priority=message.get("priority", 0)
        )

    class Config:
        arbitrary_types_allowed = True
