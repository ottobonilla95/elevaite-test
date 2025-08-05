from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional, cast, Generator
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
from services.shared_state import update_status


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

    def _process_chat_history(
        self,
        chat_history: Optional[List[Dict[str, Any]]],
        system_prompt: str,
        query: str,
    ) -> List[ChatCompletionMessageParam]:
        """
        Process chat history and build messages array for both execution methods.
        """
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
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
                        role = "assistant" if msg["actor"] == "bot" else msg["actor"]
                        converted_history.append(
                            {"role": role, "content": msg.get("content", "")}
                        )
                    elif "role" in msg:
                        # Already in correct format
                        converted_history.append(msg)
                    else:
                        # Skip malformed messages
                        continue

            # Add converted history to messages
            messages.extend(cast(List[ChatCompletionMessageParam], converted_history))

        # Add current query
        messages.append({"role": "user", "content": query})
        return messages

    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        enable_analytics: bool = False,
        max_tool_calls: int = 10,  # Higher limit for non-streaming to maintain compatibility
        execution_id: Optional[
            str
        ] = None,  # Allow custom execution_id to override UUID generation
        **kwargs: Any,
    ) -> str:
        """
        Simplified execution method based on CommandAgent pattern.
        Pass model, model parameters and functions/tools/agents and presto!
        """
        from utils import client
        from .tools import tool_store

        # update_status("superuser@iopex.com", "Thinking...")

        # Skip Redis-dependent agent_store, use dynamic agent store if available
        agent_store = kwargs.get("dynamic_agent_store", {})

        # Analytics setup if enabled
        analytics_service = None
        db = None
        # execution_id = None
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
        original_execution_id = execution_id  # Store original for workflow context
        if enable_analytics and analytics_service:
            if execution_id:
                # If execution_id is provided (workflow context), create agent execution record
                # for this execution_id so tool usage can reference it
                execution_context = analytics_service.track_agent_execution(
                    agent_id=str(self.agent_id),
                    agent_name=self.name,
                    query=query,
                    session_id=session_id,
                    user_id=user_id,
                    db=db,
                    execution_id=execution_id,  # Use the provided workflow execution_id
                )
                agent_execution_id = execution_context.__enter__()
                # Ensure we use the same execution_id (should be the same as provided)
                execution_id = agent_execution_id
            else:
                # Only create new agent execution tracking for standalone agent calls
                execution_context = analytics_service.track_agent_execution(
                    agent_id=str(self.agent_id),
                    agent_name=self.name,
                    query=query,
                    session_id=session_id,
                    user_id=user_id,
                    db=db,
                    execution_id=None,  # Let it create a new execution_id
                )
                agent_execution_id = execution_context.__enter__()
                execution_id = agent_execution_id

        try:
            tries = 0
            tool_call_count = 0

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

            # Build messages array using shared chat history processing
            messages = self._process_chat_history(chat_history, system_prompt, query)

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
                    update_status("superuser@iopex.com", "Thinking...")

                    if enable_analytics and analytics_service:
                        analytics_service.logger.debug(
                            f"OpenAI API response received for execution {execution_id}"
                        )

                    # Handle tool calls
                    if (
                        response.choices[0].finish_reason == "tool_calls"
                        and response.choices[0].message.tool_calls is not None
                    ):
                        # Check if we've exceeded max tool calls
                        if tool_call_count >= max_tool_calls:
                            if enable_analytics and analytics_service and execution_id:
                                analytics_service.update_execution_metrics(
                                    execution_id=execution_id,
                                    response=f"Maximum tool calls ({max_tool_calls}) reached.",
                                    tools_called=tools_called,
                                    tool_count=len(tools_called),
                                    retry_count=tries,
                                    api_calls_count=api_calls_count,
                                )
                            return f"Maximum tool calls ({max_tool_calls}) reached. Ending conversation."

                        tool_call_count += 1
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
                            update_status("superuser@iopex.com", function_name)

                            # Track tool usage
                            usage_id = None
                            tool_context = None
                            if enable_analytics and analytics_service and execution_id:
                                tool_context = analytics_service.track_tool_usage(
                                    tool_name=function_name,
                                    execution_id=execution_id,
                                    input_data=arguments,
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
                                    )

                                # Track tool call for execution metrics
                                tools_called.append(
                                    {
                                        "tool_name": function_name,
                                        "arguments": arguments,
                                        "usage_id": str(usage_id) if usage_id else None,
                                    }
                                )
                                update_status("superuser@iopex.com", "Thinking...")

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
                            )
                        return self._get_fallback_response()

            return self._get_fallback_response()

        finally:
            # Exit analytics tracking context if it was entered
            if execution_context:
                execution_context.__exit__(None, None, None)

    def execute_stream(
        self,
        query: str,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        enable_analytics: bool = False,
        max_tool_calls: int = 5,
        execution_id: Optional[str] = None,  # Allow custom execution_id
        **kwargs: Any,
    ) -> Generator[str, None, None]:
        """
        Streaming execution method that yields incremental responses.
        """
        from utils import client
        from .tools import tool_store

        # Skip Redis-dependent agent_store, use dynamic agent store if available
        agent_store = kwargs.get("dynamic_agent_store", {})

        # Analytics setup if enabled
        analytics_service = None
        db = None
        # execution_id is now passed as parameter or will be generated
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
        original_execution_id = execution_id  # Store original for workflow context
        if enable_analytics and analytics_service:
            if execution_id:
                # If execution_id is provided (workflow context), create agent execution record
                # for this execution_id so tool usage can reference it
                execution_context = analytics_service.track_agent_execution(
                    agent_id=str(self.agent_id),
                    agent_name=self.name,
                    query=query,
                    session_id=session_id,
                    user_id=user_id,
                    db=db,
                    execution_id=execution_id,  # Use the provided workflow execution_id
                )
                agent_execution_id = execution_context.__enter__()
                # Ensure we use the same execution_id (should be the same as provided)
                execution_id = agent_execution_id
            else:
                # Only create new agent execution tracking for standalone agent calls
                execution_context = analytics_service.track_agent_execution(
                    agent_id=str(self.agent_id),
                    agent_name=self.name,
                    query=query,
                    session_id=session_id,
                    user_id=user_id,
                    db=db,
                    execution_id=None,  # Let it create a new execution_id
                )
                agent_execution_id = execution_context.__enter__()
                execution_id = agent_execution_id

        try:
            tries = 0
            tool_call_count = 0

            # Build system prompt with routing options
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

            # Build messages array using shared chat history processing
            messages = self._process_chat_history(chat_history, system_prompt, query)

            # Main retry loop
            while tries < self.max_retries:
                if enable_analytics and analytics_service:
                    analytics_service.logger.info(
                        f"{self.name} streaming attempt {tries + 1}/{self.max_retries}"
                    )

                try:
                    # Track API call
                    api_calls_count += 1

                    # Prepare API call parameters
                    api_params = {
                        "model": self.model,  # Use configured model
                        "messages": messages,
                        "temperature": self.temperature,
                        "stream": False,
                    }

                    # Add tools if available
                    if self.functions:
                        api_params["tools"] = self.functions
                        api_params["tool_choice"] = "auto"

                    response = client.chat.completions.create(**api_params)
                    update_status("superuser@iopex.com", "Thinking...")

                    if enable_analytics and analytics_service:
                        analytics_service.logger.debug(
                            f"OpenAI API response received for streaming execution {execution_id}"
                        )

                    # Handle tool calls
                    if (
                        response.choices[0].finish_reason == "tool_calls"
                        and response.choices[0].message.tool_calls is not None
                    ):
                        # Check if we've exceeded max tool calls
                        if tool_call_count >= max_tool_calls:
                            yield f"Maximum tool calls ({max_tool_calls}) reached. Ending conversation.\n"
                            break

                        tool_call_count += 1
                        tool_calls = response.choices[0].message.tool_calls

                        _message: ChatCompletionAssistantMessageParam = {
                            "role": "assistant",
                            "tool_calls": cast(
                                List[ChatCompletionMessageToolCallParam], tool_calls
                            ),
                        }
                        messages.append(_message)

                        for tool in tool_calls:
                            yield f"Agent Called: {tool.function.name}\n"

                            if enable_analytics and analytics_service:
                                analytics_service.logger.info(
                                    f"Executing tool: {tool.function.name}"
                                )

                            tool_id = tool.id
                            arguments = json.loads(tool.function.arguments)
                            function_name = tool.function.name
                            update_status("superuser@iopex.com", function_name)

                            # Track tool usage
                            usage_id = None
                            tool_context = None
                            if enable_analytics and analytics_service and execution_id:
                                tool_context = analytics_service.track_tool_usage(
                                    tool_name=function_name,
                                    execution_id=execution_id,
                                    input_data=arguments,
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
                                        output_data={"result": str(result)[:1000]},
                                    )

                                # Track tool call for execution metrics
                                tools_called.append(
                                    {
                                        "tool_name": function_name,
                                        "arguments": arguments,
                                        "usage_id": str(usage_id) if usage_id else None,
                                    }
                                )
                                update_status("superuser@iopex.com", "Thinking...")

                                # Add tool response message
                                messages.append(
                                    {
                                        "role": "tool",
                                        "tool_call_id": tool_id,
                                        "content": str(result),
                                    }
                                )

                                # Yield tool result
                                try:
                                    if isinstance(result, str):
                                        parsed_result = json.loads(result)
                                        yield parsed_result.get(
                                            "content", "Agent Responded"
                                        ) + "\n"
                                    else:
                                        yield str(result) + "\n"
                                except json.JSONDecodeError:
                                    yield str(result) + "\n"

                            finally:
                                # Exit tool tracking context if it was entered
                                if tool_context:
                                    tool_context.__exit__(None, None, None)

                        # Continue the conversation after processing all tool calls
                        tries += 1

                    else:
                        if response.choices[0].message.content is None:
                            raise Exception("No content in response")

                        yield "Agent Responded\n"

                        # Update execution metrics before yielding final response
                        if enable_analytics and analytics_service and execution_id:
                            analytics_service.update_execution_metrics(
                                execution_id=execution_id,
                                response=response.choices[0].message.content,
                                tools_called=tools_called,
                                tool_count=len(tools_called),
                                retry_count=tries,
                                api_calls_count=api_calls_count,
                            )

                        # Yield final response
                        try:
                            parsed_content = json.loads(
                                response.choices[0].message.content
                            )
                            yield parsed_content.get(
                                "content", "Agent Could Not Respond"
                            ) + "\n\n"
                        except json.JSONDecodeError:
                            yield response.choices[0].message.content + "\n\n"
                        return

                except Exception as e:
                    if enable_analytics and analytics_service:
                        analytics_service.logger.error(
                            f"Error in {self.name} streaming execution: {str(e)}"
                        )

                    print(f"❌ Error in streaming agent execution: {e}")
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
                            )
                        yield f"Error after {self.max_retries} attempts: {str(e)}\n"
                        return

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
