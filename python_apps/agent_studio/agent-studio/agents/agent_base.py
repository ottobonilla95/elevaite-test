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
    response_type: Optional[Literal["json", "yaml", "markdown", "HTML", "None"]] = "json"

    max_retries: int = 3
    timeout: Optional[int] = None
    deployed: bool = False
    status: Literal["active", "paused", "terminated"] = "active"
    priority: Optional[int] = None

    failure_strategies: Optional[List[str]]

    session_id: Optional[str] = None
    last_active: Optional[datetime] = None
    # logging_level: Optional[Literal["debug", "info", "warning", "error"]] = "info"  # Debug level

    collaboration_mode: Optional[Literal["single", "team", "parallel", "sequential"]] = "single"  # Multi-agent behavior

    stream_name: Optional[str] = None
    consumer_group: str = "agent_group"
    consumer_name: Optional[str] = None
    message_handlers: Dict[str, Callable] = Field(default_factory=dict)

    def execute(self, *args, **kwargs) -> Any:
        """Execution script for each component."""
        raise NotImplementedError("Component execution logic should be implemented in subclasses.")

    def _execute_with_llm(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        response_format: Optional[Dict[str, str]] = None,
        stream: bool = False,
        enable_analytics: bool = False,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Common execution pattern for LLM-based agents.

        Args:
            query: The user query
            chat_history: Optional chat history
            model: OpenAI model to use
            temperature: Temperature for response generation
            response_format: Optional response format specification
            stream: Whether to stream the response
            enable_analytics: Whether to enable analytics tracking
            session_id: Session ID for analytics
            user_id: User ID for analytics
            **kwargs: Additional parameters

        Returns:
            The agent's response
        """
        from utils import client
        import json
        from .tools import tool_store

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
                print("Analytics service not available, continuing without analytics")
                enable_analytics = False

        # Start analytics tracking if enabled
        if enable_analytics and analytics_service:
            execution_context = analytics_service.track_agent_execution(
                agent_id=self.agent_id,
                agent_name=self.name,
                query=query,
                session_id=session_id,
                user_id=user_id,
                db=db,
            )
            execution_id = execution_context.__enter__()

        try:
            tries = 0

            # Build routing options string
            routing_options = "\n".join([f"{k}: {v}" for k, v in self.routing_options.items()])

            # Construct system prompt
            system_prompt = (
                self.system_prompt.prompt
                + f"""
            Here are the routing options:
            {routing_options}

            Your response should be in the format:
            {{ "routing": "respond", "content": "The answer to the query."}}
            """
            )

            # Build messages array
            messages = []
            if chat_history:
                messages.extend(chat_history)

            messages.extend([{"role": "system", "content": system_prompt}, {"role": "user", "content": query}])

            # Main retry loop
            while tries < self.max_retries:
                if enable_analytics and analytics_service:
                    analytics_service.logger.info(f"{self.name} attempt {tries + 1}/{self.max_retries}")

                try:
                    # Track API call
                    if enable_analytics:
                        api_calls_count += 1

                    # Prepare API call parameters
                    api_params = {"model": model, "messages": messages, "temperature": temperature, "stream": stream}

                    # Add tools if available
                    if self.functions:
                        api_params["tools"] = self.functions
                        api_params["tool_choice"] = "auto"

                    # Add response format if specified
                    if response_format:
                        api_params["response_format"] = response_format

                    # Call OpenAI API
                    response = client.chat.completions.create(**api_params)

                    if enable_analytics and analytics_service:
                        analytics_service.logger.debug(f"OpenAI API response received for execution {execution_id}")

                    # Handle tool calls
                    if (
                        hasattr(response.choices[0], "finish_reason")
                        and response.choices[0].finish_reason == "tool_calls"
                        and response.choices[0].message.tool_calls is not None
                    ):
                        tool_calls = response.choices[0].message.tool_calls
                        messages.append({"role": "assistant", "tool_calls": tool_calls})

                        # Process each tool call
                        for tool in tool_calls:
                            tool_id = tool.id
                            function_name = tool.function.name
                            arguments = json.loads(tool.function.arguments)

                            if enable_analytics and analytics_service:
                                analytics_service.logger.info(f"Executing tool: {function_name}")

                            # Track tool usage if analytics enabled
                            usage_id = None
                            if enable_analytics and analytics_service:
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
                                # Execute tool
                                result = tool_store[function_name](**arguments)

                                # Update tool metrics if analytics enabled
                                if enable_analytics and analytics_service and usage_id:
                                    analytics_service.update_tool_metrics(
                                        usage_id=usage_id,
                                        output_data={"result": str(result)[:1000]},  # Truncate for storage
                                        db=db,
                                    )

                                # Track tool call for execution metrics
                                if enable_analytics:
                                    tools_called.append(
                                        {
                                            "tool_name": function_name,
                                            "arguments": arguments,
                                            "usage_id": str(usage_id) if usage_id else None,
                                        }
                                    )

                                # Add tool response to messages
                                messages.append({"role": "tool", "tool_call_id": tool_id, "content": str(result)})

                            finally:
                                # Exit tool tracking context if it was entered
                                if enable_analytics and analytics_service and usage_id:
                                    tool_context.__exit__(None, None, None)

                    else:
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

                        # Return final response
                        return response.choices[0].message.content

                except Exception as e:
                    if enable_analytics and analytics_service:
                        analytics_service.logger.error(f"Error in {self.name} execution: {str(e)}")

                    print(f"Error in agent execution: {e}")
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
            if enable_analytics and analytics_service and execution_id:
                execution_context.__exit__(None, None, None)

    def _get_fallback_response(self) -> str:
        """Get fallback response when all retries fail."""
        import json

        return json.dumps(
            {"routing": "failed", "content": "Couldn't process your query. Please try again with a different approach."}
        )

    def initialize_redis_communication(self):
        try:
            redis_manager = get_redis_manager()

            if not self.stream_name:
                self.stream_name = f"agent:{self.name.lower()}"

            if not self.consumer_name:
                self.consumer_name = f"{self.name.lower()}_{str(self.agent_id)[:8]}"

            if not redis_manager.is_connected:
                print(f"Warning: Redis not available for agent {self.name}. Agent communication will be limited.")
                return

            if redis_manager.create_stream(self.stream_name):
                redis_manager.create_consumer_group(self.stream_name, self.consumer_group)
                self.register_message_handler(self._default_message_handler)
                print(f"Redis communication initialized for agent {self.name}")
            else:
                print(f"Warning: Failed to create Redis stream for agent {self.name}")

        except Exception as e:
            print(f"Warning: Failed to initialize Redis communication for agent {self.name}: {e}")

    def register_message_handler(self, handler: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]):
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
            print(f"Warning: Failed to register message handler for agent {self.name}: {e}")

    def _default_message_handler(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

    def send_message(self, target_stream: str, message: Dict[str, Any], priority: int = 0) -> Optional[str]:
        try:
            redis_manager = get_redis_manager()
            if redis_manager.is_connected:
                return redis_manager.publish_message(target_stream, message, priority=priority)
            else:
                print(f"Warning: Cannot send message from agent {self.name} - Redis not available")
                return None
        except Exception as e:
            print(f"Warning: Failed to send message from agent {self.name}: {e}")
            return None

    def request_reply(self, target_stream: str, message: Dict[str, Any], timeout: int = 5) -> Optional[Dict[str, Any]]:
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
                print(f"Warning: Cannot send request from agent {self.name} - Redis not available")
                return None
        except Exception as e:
            print(f"Warning: Failed to send request from agent {self.name}: {e}")
            return None
