from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional, cast
import uuid
import json
from pydantic import BaseModel, Field, ConfigDict
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call_param import (
    ChatCompletionMessageToolCallParam,
)
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

    # Model configuration - simplified agent creation
    model: str = "gpt-4o-mini"
    temperature: float = 0.7

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

    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        enable_analytics: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Simplified execution method based on CommandAgent pattern.
        Pass model, model parameters and functions/tools/agents and presto!
        """
        from utils import client
        from .tools import tool_store

        # Skip Redis-dependent agent_store, use dynamic agent store if available
        agent_store = kwargs.get("dynamic_agent_store", {})

        # Analytics setup if enabled
        analytics_service = None
        db = None
        execution_id = None
        tools_called = []
        api_calls_count = 0

        if enable_analytics:
            try:
                from services.analytics_service import analytics_service as analytics
                from db.database import get_db

                analytics_service = analytics
                db = next(get_db())
            except ImportError:
                enable_analytics = False

        # Start analytics tracking if enabled
        execution_context = None
        if enable_analytics and analytics_service:
            execution_context = analytics_service.track_agent_execution(
                agent_id=str(self.agent_id),
                agent_name=self.name,
                query=query,
                session_id=session_id,
                user_id=user_id,
                db=db,
            )
            execution_id = execution_context.__enter__()

        try:
            tries = 0

            if self.routing_options:
                routing_options = "\n".join(
                    [f"{k}: {v}" for k, v in self.routing_options.items()]
                )
                system_prompt = (
                    self.system_prompt.prompt
                    + f"""
                Here are the routing options:
                {routing_options}

                Your response should be in the format:
                {{ "routing": "respond", "content": "The answer to the query."}}
                """
                )
            else:
                system_prompt = self.system_prompt.prompt

            # Build messages array
            messages: List[ChatCompletionMessageParam] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ]

            # Add chat history if provided
            if chat_history:
                # Convert chat history to proper OpenAI format
                converted_history = []
                for msg in chat_history:
                    if isinstance(msg, dict):
                        # Handle different possible formats
                        if "actor" in msg:
                            # Convert 'actor' format to 'role' format
                            role = (
                                "assistant" if msg["actor"] == "bot" else msg["actor"]
                            )
                            converted_history.append(
                                {"role": role, "content": msg.get("content", "")}
                            )
                        elif "role" in msg:
                            # Already in correct format
                            converted_history.append(msg)
                        else:
                            # Skip malformed messages
                            continue

                # Insert chat history before the current query
                messages: List[ChatCompletionMessageParam] = [
                    {"role": "system", "content": system_prompt}
                ]
                messages.extend(
                    cast(List[ChatCompletionMessageParam], converted_history)
                )
                messages.append({"role": "user", "content": query})

            # Main retry loop
            while tries < self.max_retries:

                if enable_analytics and analytics_service:
                    analytics_service.logger.info(
                        f"{self.name} attempt {tries + 1}/{self.max_retries}"
                    )

                try:
                    # Track API call
                    api_calls_count += 1

                    # Prepare API call parameters
                    api_params = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": self.temperature,
                    }

                    # Add tools if available
                    if self.functions:
                        api_params["tools"] = self.functions
                        api_params["tool_choice"] = "auto"

                    response = client.chat.completions.create(**api_params)

                    if enable_analytics and analytics_service:
                        analytics_service.logger.debug(
                            f"OpenAI API response received for execution {execution_id}"
                        )

                    # Handle tool calls
                    if (
                        response.choices[0].finish_reason == "tool_calls"
                        and response.choices[0].message.tool_calls is not None
                    ):
                        tool_calls = response.choices[0].message.tool_calls

                        _message: ChatCompletionAssistantMessageParam = {
                            "role": "assistant",
                            "tool_calls": cast(
                                List[ChatCompletionMessageToolCallParam], tool_calls
                            ),
                        }
                        messages.append(_message)

                        for tool in tool_calls:
                            if enable_analytics and analytics_service:
                                analytics_service.logger.info(
                                    f"Executing tool: {tool.function.name}"
                                )

                            tool_id = tool.id
                            arguments = json.loads(tool.function.arguments)
                            function_name = tool.function.name

                            # Track tool usage
                            usage_id = None
                            tool_context = None
                            if enable_analytics and analytics_service and execution_id:
                                external_api = None
                                if function_name in ["web_search", "weather_forecast"]:
                                    external_api = function_name

                                tool_context = analytics_service.track_tool_usage(
                                    tool_name=function_name,
                                    execution_id=execution_id,
                                    input_data=arguments,
                                    external_api_called=external_api,
                                    db=db,
                                )
                                usage_id = tool_context.__enter__()

                            try:
                                # Execute tool or agent
                                try:
                                    if function_name in agent_store:
                                        result = agent_store[function_name](**arguments)
                                    else:
                                        result = tool_store[function_name](**arguments)

                                except Exception as tool_error:
                                    # If tool execution fails, still provide a response to maintain conversation flow
                                    print(
                                        f"❌ Tool '{function_name}' failed: {str(tool_error)}"
                                    )
                                    result = f"Error executing tool {function_name}: {str(tool_error)}"
                                    if enable_analytics and analytics_service:
                                        analytics_service.logger.error(
                                            f"Tool execution failed for {function_name}: {str(tool_error)}"
                                        )

                                # Update tool metrics if analytics enabled
                                if enable_analytics and analytics_service and usage_id:
                                    analytics_service.update_tool_metrics(
                                        usage_id=usage_id,
                                        output_data={
                                            "result": str(result)[:1000]
                                        },  # Truncate for storage
                                        db=db,
                                    )

                                # Track tool call for execution metrics
                                tools_called.append(
                                    {
                                        "tool_name": function_name,
                                        "arguments": arguments,
                                        "usage_id": str(usage_id) if usage_id else None,
                                    }
                                )

                                # Always add tool response message to maintain conversation flow
                                messages.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": tool_id,
                                        "content": str(result),
                                    }
                                )

                            finally:
                                # Exit tool tracking context if it was entered
                                if tool_context:
                                    tool_context.__exit__(None, None, None)

                        # NOTE: This continues the while loop - no return here!

                    else:
                        if response.choices[0].message.content is None:
                            raise Exception("No content in response")

                        # Update execution metrics before returning
                        if enable_analytics and analytics_service and execution_id:
                            analytics_service.update_execution_metrics(
                                execution_id=execution_id,
                                response=response.choices[0].message.content,
                                tools_called=tools_called,
                                tool_count=len(tools_called),
                                retry_count=tries,
                                api_calls_count=api_calls_count,
                                db=db,
                            )

                        return response.choices[0].message.content

                except Exception as e:
                    if enable_analytics and analytics_service:
                        analytics_service.logger.error(
                            f"Error in {self.name} execution: {str(e)}"
                        )

                    print(f"❌ Error in agent execution: {e}")
                    tries += 1

                    if tries >= self.max_retries:
                        # Update execution metrics with final retry count
                        if enable_analytics and analytics_service and execution_id:
                            analytics_service.update_execution_metrics(
                                execution_id=execution_id,
                                tools_called=tools_called,
                                tool_count=len(tools_called),
                                retry_count=tries,
                                api_calls_count=api_calls_count,
                                db=db,
                            )
                        return self._get_fallback_response()

            return self._get_fallback_response()

        finally:
            # Exit analytics tracking context if it was entered
            if execution_context:
                execution_context.__exit__(None, None, None)

    def _get_fallback_response(self) -> str:
        """Get fallback response when all retries fail."""
        import json

        return json.dumps(
            {
                "routing": "failed",
                "content": "Couldn't process your query. Please try again with a different approach.",
            }
        )

    def initialize_redis_communication(self):
        try:
            redis_manager = get_redis_manager()

            if not self.stream_name:
                self.stream_name = f"agent:{self.name.lower()}"

            if not self.consumer_name:
                self.consumer_name = f"{self.name.lower()}_{str(self.agent_id)[:8]}"

            if not redis_manager.is_connected:
                return

            if redis_manager.create_stream(self.stream_name):
                redis_manager.create_consumer_group(
                    self.stream_name, self.consumer_group
                )
                self.register_message_handler(self._default_message_handler)

        except Exception:
            # Redis communication failed - continue without it
            pass

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
        except Exception:
            # Failed to register message handler - continue without it
            pass

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

            return None

        except Exception as e:
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
                return None
        except Exception:
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
                return None
        except Exception:
            return None
