from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from data_classes import PromptObject


# Lazy import to avoid Redis connection at import time
def get_redis_manager():
    from redis_utils import redis_manager

    return redis_manager


class Agent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

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

    max_retries: int = 3
    timeout: Optional[int] = None
    deployed: bool = False
    status: Literal["active", "paused", "terminated"] = "active"
    priority: Optional[int] = None

    failure_strategies: Optional[List[str]]

    session_id: Optional[str] = None
    last_active: Optional[datetime] = None
    # logging_level: Optional[Literal["debug", "info", "warning", "error"]] = "info"  # Debug level

    collaboration_mode: Optional[
        Literal["single", "team", "parallel", "sequential"]
    ] = "single"  # Multi-agent behavior

    stream_name: Optional[str] = None
    consumer_group: str = "agent_group"
    consumer_name: Optional[str] = None
    message_handlers: Dict[str, Callable] = Field(default_factory=dict)

    def execute(self, *args, **kwargs) -> Any:
        """Execution script for each component."""
        raise NotImplementedError(
            "Component execution logic should be implemented in subclasses."
        )

    def initialize_redis_communication(self):
        try:
            redis_manager = get_redis_manager()

            if not self.stream_name:
                self.stream_name = f"agent:{self.name.lower()}"

            if not self.consumer_name:
                self.consumer_name = f"{self.name.lower()}_{str(self.agent_id)[:8]}"

            if not redis_manager.is_connected:
                print(
                    f"Warning: Redis not available for agent {self.name}. Agent communication will be limited."
                )
                return

            if redis_manager.create_stream(self.stream_name):
                redis_manager.create_consumer_group(
                    self.stream_name, self.consumer_group
                )
                self.register_message_handler(self._default_message_handler)
                print(f"Redis communication initialized for agent {self.name}")
            else:
                print(f"Warning: Failed to create Redis stream for agent {self.name}")

        except Exception as e:
            print(
                f"Warning: Failed to initialize Redis communication for agent {self.name}: {e}"
            )

    def register_message_handler(
        self, handler: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]
    ):
        try:
            redis_manager = get_redis_manager()
            if self.stream_name is not None and redis_manager.is_connected:
                redis_manager.consume_messages(
                    self.stream_name,
                    handler,
                    group_name=self.consumer_group,
                    consumer_name=self.consumer_name,
                )
        except Exception as e:
            print(
                f"Warning: Failed to register message handler for agent {self.name}: {e}"
            )

    def _default_message_handler(
        self, message: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        try:
            data = message.get("data", {})
            msg_type = data.get("type", "unknown")

            if msg_type in self.message_handlers:
                return self.message_handlers[msg_type](data)

            if "query" in data:
                result = self.execute(query=data["query"])
                return {"result": result}

            print(f"Agent {self.name} received unhandled message: {data}")
            return None

        except Exception as e:
            print(f"Error handling message in agent {self.name}: {e}")
            return {"error": str(e)}

    def send_message(
        self, target_stream: str, message: Dict[str, Any], priority: int = 0
    ) -> Optional[str]:
        try:
            redis_manager = get_redis_manager()
            if redis_manager.is_connected:
                return redis_manager.publish_message(
                    target_stream, message, priority=priority
                )
            else:
                print(
                    f"Warning: Cannot send message from agent {self.name} - Redis not available"
                )
                return None
        except Exception as e:
            print(f"Warning: Failed to send message from agent {self.name}: {e}")
            return None

    def request_reply(
        self, target_stream: str, message: Dict[str, Any], timeout: int = 5
    ) -> Optional[Dict[str, Any]]:
        try:
            redis_manager = get_redis_manager()
            if redis_manager.is_connected:
                return redis_manager.request_reply(
                    target_stream,
                    message,
                    timeout=timeout,
                    priority=message.get("priority", 0),
                )
            else:
                print(
                    f"Warning: Cannot send request from agent {self.name} - Redis not available"
                )
                return None
        except Exception as e:
            print(f"Warning: Failed to send request from agent {self.name}: {e}")
            return None
