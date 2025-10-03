from datetime import datetime
from typing import Any, Callable, Dict, List, Literal, Optional, cast, Generator
import uuid
import json
from openai import Stream
from pydantic import BaseModel, Field, ConfigDict
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
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


class AgentStreamChunk(BaseModel):
    type: Literal["content"] | Literal["info"] | Literal["error"] | Literal["agent_response"]
    message: str


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

    # Model configuration - simplified agent creation
    model: str = "gpt-4o-mini"
    temperature: float = 0.7

    max_retries: int = 10
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

    def _process_chat_history(
        self,
        chat_history: Optional[List[Dict[str, Any]]],
        system_prompt: str,
        query: str,
    ) -> List[ChatCompletionMessageParam]:
        """
        Process chat history and build messages array for both execution methods.
        Also sanitizes any invalid tool-call sequences that would cause OpenAI API errors
        (assistant message with tool_calls not followed by corresponding tool messages).
        """
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add chat history if provided
        if chat_history:
            # Convert chat history to proper OpenAI format
            converted_history: List[Dict[str, Any]] = []
            for msg in chat_history:
                if isinstance(msg, dict):
                    # Handle different possible formats
                    if "actor" in msg:
                        # Convert 'actor' format to 'role' format
                        role = "assistant" if msg.get("actor") == "bot" else msg.get("actor")
                        converted_history.append({"role": role, "content": msg.get("content", "")})
                    elif "role" in msg:
                        # Already in (approximately) correct format; shallow copy to allow edits
                        converted_history.append(dict(msg))
                    else:
                        # Skip malformed messages
                        continue

            # # Sanitize: An assistant message with tool_calls must be immediately followed by
            # # tool messages responding to each tool_call_id. If history lacks those tool messages,
            # # strip tool_calls from that assistant message to avoid API errors.
            # i = 0
            # while i < len(converted_history):
            #     m = converted_history[i]
            #     try:
            #         if (
            #             isinstance(m, dict)
            #             and m.get("role") == "assistant"
            #             and isinstance(m.get("tool_calls"), list)
            #             and m.get("tool_calls")
            #         ):
            #             # Collect tool_call ids from assistant message
            #             ids = []
            #             for tc in m.get("tool_calls") or []:
            #                 if isinstance(tc, dict):
            #                     tcid = tc.get("id") or tc.get("tool_call_id")
            #                     if isinstance(tcid, str) and tcid:
            #                         ids.append(tcid)
            #             # Scan following messages for tool responses
            #             found_ids = set()
            #             j = i + 1
            #             while j < len(converted_history):
            #                 mj = converted_history[j]
            #                 if isinstance(mj, dict) and mj.get("role") == "tool":
            #                     tcid2 = mj.get("tool_call_id")
            #                     if isinstance(tcid2, str) and tcid2:
            #                         found_ids.add(tcid2)
            #                     j += 1
            #                     continue
            #                 # Stop when we hit the next non-tool message
            #                 break
            #             if not ids or not set(ids).issubset(found_ids):
            #                 # Incomplete tool-call sequence in history; drop tool_calls to satisfy API
            #                 try:
            #                     m.pop("tool_calls", None)
            #                 except Exception:
            #                     pass
            #     except Exception:
            #         # Never let history sanitation break execution
            #         pass
            #     i += 1

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
        execution_id: Optional[str] = None,  # Allow custom execution_id to override UUID generation
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
                routing_options = "\n".join([f"{k}: {v}" for k, v in self.routing_options.items()])
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
                    analytics_service.logger.info(f"{self.name} attempt {tries + 1}/{self.max_retries}")

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
                        analytics_service.logger.debug(f"OpenAI API response received for execution {execution_id}")

                    # Handle tool calls
                    if response.choices[0].finish_reason == "tool_calls" and response.choices[0].message.tool_calls is not None:
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
                            "tool_calls": cast(List[ChatCompletionMessageToolCallParam], tool_calls),
                        }
                        messages.append(_message)

                        for tool in tool_calls:
                            if enable_analytics and analytics_service:
                                analytics_service.logger.info(f"Executing tool: {tool.function.name}")

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
                                    print(f"❌ Tool '{function_name}' failed: {str(tool_error)}")
                                    result = f"Error executing tool {function_name}: {str(tool_error)}"
                                    if enable_analytics and analytics_service:
                                        analytics_service.logger.error(
                                            f"Tool execution failed for {function_name}: {str(tool_error)}"
                                        )

                                # Update tool metrics if analytics enabled
                                if enable_analytics and analytics_service and usage_id:
                                    analytics_service.update_tool_metrics(
                                        usage_id=usage_id,
                                        output_data={"result": str(result)[:1000]},  # Truncate for storage
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
                        analytics_service.logger.error(f"Error in {self.name} execution: {str(e)}")

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
    ) -> Generator[AgentStreamChunk, None, None]:
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
            # if self.routing_options:
            #     routing_options = "\n".join([f"{k}: {v}" for k, v in self.routing_options.items()])
            #     system_prompt = (
            #         self.system_prompt.prompt
            #         + f"""
            #     Here are the routing options:
            #     {routing_options}

            #     Your response should be in the format:
            #     {{ "routing": "respond", "content": "The answer to the query."}}
            #     """
            #     )
            # else:
            #     system_prompt = self.system_prompt.prompt
            system_prompt = self.system_prompt.prompt

            # Build messages array using shared chat history processing
            messages = self._process_chat_history(chat_history, system_prompt, query)

            # Main conversation loop - separate from retries
            conversation_turns = 0
            max_conversation_turns = 10  # Prevent infinite loops

            while conversation_turns < max_conversation_turns:
                conversation_turns += 1
                if enable_analytics and analytics_service:
                    analytics_service.logger.info(f"{self.name} streaming conversation turn {conversation_turns}")

                try:
                    # Track API call
                    api_calls_count += 1

                    # Prepare API call parameters
                    api_params = {
                        "model": self.model,  # Use configured model
                        "messages": messages,
                        "temperature": self.temperature,
                        "stream": True,
                    }

                    # Add tools if available
                    if self.functions:
                        api_params["tools"] = self.functions
                        api_params["tool_choice"] = "auto"

                    response: Stream[ChatCompletionChunk] = client.chat.completions.create(**api_params)
                    update_status("superuser@iopex.com", "Thinking...")

                    if enable_analytics and analytics_service:
                        analytics_service.logger.debug(f"OpenAI API response received for streaming execution {execution_id}")

                    # Process streaming response
                    collected_content = ""
                    tool_calls = []
                    finish_reason = None

                    for chunk in response:
                        # Handle content streaming
                        if chunk.choices[0].delta.content is not None:
                            token = chunk.choices[0].delta.content
                            collected_content += token
                            yield AgentStreamChunk(type="content", message=token)

                        # Handle tool calls
                        if chunk.choices[0].delta.tool_calls:
                            # Tool calls are built incrementally across chunks
                            for i, tool_call_delta in enumerate(chunk.choices[0].delta.tool_calls):
                                # Extend tool_calls list if needed
                                while len(tool_calls) <= i:
                                    tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})

                                # Update tool call data incrementally
                                if tool_call_delta.id:
                                    tool_calls[i]["id"] = tool_call_delta.id
                                if tool_call_delta.function:
                                    if tool_call_delta.function.name:
                                        tool_calls[i]["function"]["name"] = tool_call_delta.function.name
                                    if tool_call_delta.function.arguments:
                                        # Handle arguments more carefully - sometimes OpenAI sends complete JSON objects
                                        new_args = tool_call_delta.function.arguments
                                        current_args = tool_calls[i]["function"]["arguments"]

                                        # If current args is empty, just use new args
                                        if not current_args:
                                            tool_calls[i]["function"]["arguments"] = new_args
                                        # If new args looks like a complete JSON object, replace current
                                        elif new_args.strip().startswith("{") and new_args.strip().endswith("}"):
                                            tool_calls[i]["function"]["arguments"] = new_args
                                        # Otherwise, concatenate (normal streaming behavior)
                                        else:
                                            tool_calls[i]["function"]["arguments"] += new_args

                        # Check for finish reason
                        if chunk.choices[0].finish_reason is not None:
                            finish_reason = chunk.choices[0].finish_reason
                            break

                    print(tool_calls)
                    # Handle tool calls after streaming is complete
                    if finish_reason == "tool_calls" and tool_calls:
                        # Check if we've exceeded max tool calls
                        if tool_call_count >= max_tool_calls:
                            yield AgentStreamChunk(
                                type="info", message=f"Maximum tool calls ({max_tool_calls}) reached. Ending conversation.\n"
                            )
                            break

                        tool_call_count += 1

                        # Convert our collected tool calls to the expected format
                        formatted_tool_calls = []
                        for tool_call in tool_calls:
                            formatted_tool_calls.append(
                                {
                                    "id": tool_call["id"],
                                    "type": tool_call["type"],
                                    "function": {
                                        "name": tool_call["function"]["name"],
                                        "arguments": tool_call["function"]["arguments"],
                                    },
                                }
                            )

                        _message: ChatCompletionAssistantMessageParam = {
                            "role": "assistant",
                            "tool_calls": cast(List[ChatCompletionMessageToolCallParam], formatted_tool_calls),
                        }
                        messages.append(_message)

                        # Process all tool calls and ensure tool response messages are added
                        # even if exceptions occur during individual tool execution
                        for tool in formatted_tool_calls:
                            tool_id = tool["id"]
                            function_name = tool["function"]["name"]
                            result = f"Error: Tool {function_name} failed to execute"  # Default fallback

                            try:
                                yield AgentStreamChunk(type="info", message=f"Agent Called: {function_name}\n")

                                if enable_analytics and analytics_service:
                                    analytics_service.logger.info(f"Executing tool: {function_name}")

                                try:
                                    print(f"🔍 DEBUG: Tool {function_name} arguments: '{tool['function']['arguments']}'")
                                    arguments = json.loads(tool["function"]["arguments"])
                                except json.JSONDecodeError as json_error:
                                    print(
                                        f"❌ Invalid JSON in tool arguments for {function_name}: '{tool['function']['arguments']}'"
                                    )
                                    result = f"Error: Invalid JSON arguments for tool {function_name}: {str(json_error)}"
                                    # Skip tool execution but still add tool response message
                                    messages.append(
                                        {
                                            "role": "tool",
                                            "tool_call_id": tool_id,
                                            "content": str(result),
                                        }
                                    )
                                    continue
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
                                        print(f"❌ Tool '{function_name}' failed: {str(tool_error)}")
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

                                    # Yield tool result
                                    try:
                                        if isinstance(result, str):
                                            json.loads(result)  # Validate JSON format
                                            yield AgentStreamChunk(type="agent_response", message=result + "\n")
                                        else:
                                            yield AgentStreamChunk(type="content", message=str(result) + "\n")
                                    except json.JSONDecodeError:
                                        yield AgentStreamChunk(type="content", message=str(result) + "\n")

                                finally:
                                    # Exit tool tracking context if it was entered
                                    if tool_context:
                                        tool_context.__exit__(None, None, None)

                            except Exception as tool_processing_error:
                                # If any error occurs during tool processing, still add a tool response message
                                # to maintain the required OpenAI message format
                                print(f"❌ Error processing tool '{function_name}': {str(tool_processing_error)}")
                                result = f"Error processing tool {function_name}: {str(tool_processing_error)}"

                                if enable_analytics and analytics_service:
                                    analytics_service.logger.error(
                                        f"Tool processing failed for {function_name}: {str(tool_processing_error)}"
                                    )

                            # Always add tool response message to maintain OpenAI format consistency
                            # This ensures that every tool_call in the assistant message has a corresponding tool response
                            messages.append(
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_id,
                                    "content": str(result),
                                }
                            )

                        # Continue the conversation after processing all tool calls
                        # Don't increment tries here - this is normal conversation flow, not a retry
                        print(
                            f"🔄 DEBUG: Continuing conversation after tool calls. Turn {conversation_turns}, Tool calls: {tool_call_count}"
                        )

                    else:
                        # Handle regular content response (not tool calls)
                        if not collected_content:
                            raise Exception("No content in response")

                        yield AgentStreamChunk(type="info", message="Agent Responded\n")

                        # Update execution metrics before yielding final response
                        if enable_analytics and analytics_service and execution_id:
                            analytics_service.update_execution_metrics(
                                execution_id=execution_id,
                                response=collected_content,
                                tools_called=tools_called,
                                tool_count=len(tools_called),
                                retry_count=tries,
                                api_calls_count=api_calls_count,
                            )

                        # Try to parse collected content as JSON for routing
                        try:
                            parsed_content = json.loads(collected_content)
                            yield AgentStreamChunk(
                                type="content", message=parsed_content.get("content", "Agent Could Not Respond") + "\n\n"
                            )
                        except json.JSONDecodeError:
                            # Content was already streamed token by token, just signal completion
                            yield AgentStreamChunk(type="info", message="[STREAM_COMPLETE]\n\n")
                        print("✅ DEBUG: Streaming complete. Final response delivered.")
                        return

                except Exception as e:
                    if enable_analytics and analytics_service:
                        analytics_service.logger.error(f"Error in {self.name} streaming execution: {str(e)}")

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
                        yield AgentStreamChunk(type="error", message=f"Error after {self.max_retries} attempts: {str(e)}\n")
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
                redis_manager.create_consumer_group(self.stream_name, self.consumer_group)
                self.register_message_handler(self._default_message_handler)

        except Exception:
            # Redis communication failed - continue without it
            pass

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
        except Exception:
            # Failed to register message handler - continue without it
            pass

    def _default_message_handler(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
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

    def send_message(self, target_stream: str, message: Dict[str, Any], priority: int = 0) -> Optional[str]:
        try:
            redis_manager = get_redis_manager()
            if redis_manager.is_connected:
                return redis_manager.publish_message(target_stream, message, priority=priority)
            else:
                return None
        except Exception:
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
                return None
        except Exception:
            return None
