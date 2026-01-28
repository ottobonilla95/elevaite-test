import logging
import time
import json
from typing import Dict, Any, Optional, List, Iterable, Callable
from openai import (
    OpenAI,
    BadRequestError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    UnprocessableEntityError,
)

from .core.base import BaseTextGenerationProvider
from .core.interfaces import TextGenerationResponse, ToolCall

# Client errors that should not be retried (4xx errors)
NON_RETRYABLE_ERRORS = (
    BadRequestError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    UnprocessableEntityError,
)


class OpenAITextGenerationProvider(BaseTextGenerationProvider):
    """
    OpenAI provider using the Responses API (preferred over Chat Completions).

    The Responses API provides:
    - Built-in tools: file_search, web_search, code_interpreter
    - Conversation state via previous_response_id
    - Better performance with reasoning models (GPT-5, etc.)
    """

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self._vector_store_cache: Dict[str, str] = {}  # file_path -> vector_store_id

    def _convert_messages_to_responses_input(
        self,
        messages: List[Dict[str, Any]],
        sys_msg: str,
        prompt: str,
    ) -> tuple[str, List[Any]]:
        """
        Convert Chat Completions style messages to Responses API format.

        The Responses API expects input as a list of items, not a string.
        Tool calls and responses need special handling:
        - Assistant messages with tool_calls become function_call items
        - Tool messages become function_call_output items

        Returns:
            tuple of (instructions, input_items_list)
        """
        instructions = ""
        input_items: List[Any] = []

        if messages and len(messages) > 0:
            for msg in messages:
                msg_role = msg.get("role", "user")
                content = msg.get("content", "")
                msg_type = msg.get("type")  # For already-converted items

                # Handle already-converted Responses API format items
                if msg_type == "function_call":
                    input_items.append(msg)
                    continue
                elif msg_type == "function_call_output":
                    input_items.append(msg)
                    continue

                if msg_role == "system":
                    instructions = content
                elif msg_role == "user":
                    input_items.append({"role": "user", "content": content})
                elif msg_role == "assistant":
                    # Check if this assistant message has tool_calls
                    tool_calls = msg.get("tool_calls", [])
                    if tool_calls:
                        # Convert each tool call to a function_call item
                        for tc in tool_calls:
                            call_id = tc.get("id")
                            func = tc.get("function", {})
                            func_name = func.get("name")
                            func_args = func.get("arguments", "{}")

                            # Ensure arguments is a string
                            if isinstance(func_args, dict):
                                import json

                                func_args = json.dumps(func_args)

                            input_items.append(
                                {
                                    "type": "function_call",
                                    "call_id": call_id,
                                    "name": func_name,
                                    "arguments": func_args,
                                }
                            )

                        # If assistant also had content, add it as a separate item
                        if content:
                            input_items.append(
                                {"role": "assistant", "content": content}
                            )
                    else:
                        # Regular assistant message without tool calls
                        if content:
                            input_items.append(
                                {"role": "assistant", "content": content}
                            )
                elif msg_role == "tool":
                    # Convert tool response to function_call_output
                    tool_call_id = msg.get("tool_call_id")
                    tool_content = msg.get("content", "")

                    input_items.append(
                        {
                            "type": "function_call_output",
                            "call_id": tool_call_id,
                            "output": tool_content,
                        }
                    )
        else:
            # Fall back to sys_msg and prompt
            instructions = sys_msg
            if prompt:
                input_items.append({"role": "user", "content": prompt})

        # If input_items is empty but we have a prompt, add it
        if not input_items and prompt:
            input_items.append({"role": "user", "content": prompt})

        return instructions, input_items

    def _convert_tools_to_responses_format(
        self,
        tools: Optional[List[Dict[str, Any]]],
        config: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Convert Chat Completions tools to Responses API format.
        Also handles built-in tools like file_search.
        """
        responses_tools = []
        config = config or {}

        # Check for built-in file_search tool configuration
        file_search_config = config.get("file_search")
        if file_search_config:
            vector_store_ids = file_search_config.get("vector_store_ids", [])
            if vector_store_ids:
                responses_tools.append(
                    {
                        "type": "file_search",
                        "vector_store_ids": vector_store_ids,
                        "max_num_results": file_search_config.get("max_num_results", 5),
                    }
                )

        # Convert function tools from Chat Completions format to Responses API format
        if tools:
            for tool in tools:
                if tool.get("type") == "function":
                    # Check if it's Chat Completions format (nested under "function" key)
                    if "function" in tool:
                        # Convert from Chat Completions format:
                        # {type: "function", function: {name, description, parameters}}
                        # to Responses API format:
                        # {type: "function", name, description, parameters}
                        func_def = tool["function"]
                        responses_tools.append(
                            {
                                "type": "function",
                                "name": func_def.get("name"),
                                "description": func_def.get("description", ""),
                                "parameters": func_def.get("parameters", {}),
                            }
                        )
                    else:
                        # Already in Responses API format
                        responses_tools.append(tool)
                elif tool.get("type") in (
                    "file_search",
                    "web_search",
                    "code_interpreter",
                ):
                    # Built-in tools
                    responses_tools.append(tool)
                elif tool.get("type") == "code_execution":
                    # Convert code_execution to a function tool that we handle ourselves
                    # This ensures we use our secure Nsjail sandbox instead of OpenAI's code_interpreter
                    responses_tools.append(
                        {
                            "type": "function",
                            "name": "execute_python",
                            "description": "Execute Python code in a secure sandbox. Returns stdout, stderr, and exit code.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "code": {
                                        "type": "string",
                                        "description": "The Python code to execute",
                                    },
                                    "timeout": {
                                        "type": "integer",
                                        "description": "Maximum execution time in seconds (default: 30, max: 60)",
                                    },
                                },
                                "required": ["code"],
                            },
                        }
                    )
                    logging.debug(
                        "Added ElevAIte Code Execution function tool for OpenAI"
                    )

        return responses_tools

    def _extract_response_content(
        self, response
    ) -> tuple[str, List[ToolCall], str, str]:
        """
        Extract content, tool calls, finish reason, and reasoning content from Responses API output.

        Returns:
            tuple: (text_content, tool_calls, finish_reason, thinking_content)
        """
        text_content = ""
        thinking_content = ""
        tool_calls = []
        finish_reason = "stop"

        # The response.output is a list of output items
        for item in response.output:
            item_type = getattr(item, "type", None)

            if item_type == "message":
                # Extract text from message content
                for content_item in getattr(item, "content", []):
                    content_type = getattr(content_item, "type", None)
                    if content_type == "output_text":
                        text_content += getattr(content_item, "text", "")
                    elif content_type == "refusal":
                        text_content += (
                            f"[Refusal: {getattr(content_item, 'refusal', '')}]"
                        )

            elif item_type == "reasoning":
                # Extract reasoning/thinking content from reasoning models (o1, o3, o4-mini)
                # Reasoning items contain summary parts with the chain of thought
                for summary_item in getattr(item, "summary", []):
                    summary_type = getattr(summary_item, "type", None)
                    if summary_type == "summary_text":
                        thinking_content += getattr(summary_item, "text", "")

            elif item_type == "function_call":
                # Extract function/tool call
                try:
                    arguments = (
                        json.loads(item.arguments)
                        if isinstance(item.arguments, str)
                        else item.arguments
                    )
                except json.JSONDecodeError:
                    arguments = {"raw": item.arguments}

                tool_calls.append(
                    ToolCall(
                        id=getattr(item, "call_id", item.id)
                        if hasattr(item, "call_id")
                        else item.id,
                        name=item.name,
                        arguments=arguments,
                    )
                )
                finish_reason = "tool_calls"

            elif item_type == "file_search_call":
                # Built-in file search was invoked
                # The results are in the annotations of the message
                logging.debug(
                    f"File search performed with query: {getattr(item, 'queries', [])}"
                )

        return text_content.strip(), tool_calls, finish_reason, thinking_content.strip()

    def _prepare_files_for_search(
        self, files: List[str], timeout_seconds: int = 60
    ) -> str:
        """
        Upload files to a vector store for file search and wait for indexing.

        Args:
            files: List of file paths to upload
            timeout_seconds: Maximum time to wait for file indexing

        Returns:
            Vector store ID
        """
        import os

        # Create a vector store with a unique name
        file_names = [os.path.basename(f) for f in files]
        store_name = f"file_search_{file_names[0][:20]}_{int(time.time())}"
        vector_store_id = self.create_vector_store(store_name)

        # Upload each file
        file_ids = []
        for file_path in files:
            try:
                file_id = self.upload_file_to_vector_store(vector_store_id, file_path)
                file_ids.append(file_id)
            except Exception as e:
                logging.error(f"Failed to upload file {file_path}: {e}")
                # Clean up the vector store on failure
                self.delete_vector_store(vector_store_id)
                raise RuntimeError(f"Failed to upload file {file_path}: {e}")

        # Wait for all files to be indexed in the vector store
        self._wait_for_vector_store_ready(vector_store_id, timeout_seconds)

        return vector_store_id

    def _wait_for_vector_store_ready(
        self, vector_store_id: str, timeout_seconds: int = 60
    ) -> None:
        """
        Wait for a vector store to finish processing all files.

        Args:
            vector_store_id: The vector store ID to check
            timeout_seconds: Maximum time to wait
        """
        start_time = time.time()
        poll_interval = 1.0  # Start with 1 second

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logging.warning(
                    f"Timeout waiting for vector store {vector_store_id} to be ready after {timeout_seconds}s"
                )
                break

            # Check vector store status
            try:
                vs = self.client.vector_stores.retrieve(vector_store_id)
                file_counts = vs.file_counts

                # Check if all files are processed
                in_progress = file_counts.in_progress
                completed = file_counts.completed
                failed = file_counts.failed
                total = file_counts.total

                logging.debug(
                    f"Vector store {vector_store_id} status: {completed}/{total} completed, {in_progress} in progress, {failed} failed"
                )

                if in_progress == 0:
                    # All files have been processed (either completed or failed)
                    if failed > 0:
                        logging.warning(
                            f"Vector store {vector_store_id}: {failed} file(s) failed to process"
                        )
                    break

            except Exception as e:
                logging.warning(f"Error checking vector store status: {e}")

            # Wait before next poll (with exponential backoff, capped at 5 seconds)
            time.sleep(poll_interval)
            poll_interval = min(poll_interval * 1.5, 5.0)

    def generate_text(
        self,
        model_name: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        sys_msg: Optional[str],
        prompt: Optional[str],
        retries: Optional[int],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        files: Optional[List[str]] = None,
        max_tool_iterations: int = 4,
    ) -> TextGenerationResponse:
        from .core.interfaces import ToolCallTrace

        model_name = model_name or "gpt-4o"
        temperature = temperature if temperature is not None else 0.5
        max_tokens = max_tokens or 100
        prompt = prompt or ""
        sys_msg = sys_msg or ""
        retries = retries or 5
        config = config or {}

        # Extract executors from tools (if any have executor functions attached)
        executors, clean_tools = self._extract_executors(tools)
        has_executors = bool(executors)

        # Handle file uploads for file_search
        vector_store_id = None
        if files:
            vector_store_id = self._prepare_files_for_search(files)
            logging.debug(
                f"Created vector store {vector_store_id} for {len(files)} file(s)"
            )

        # Tool loop state
        tool_calls_trace: List[ToolCallTrace] = []
        tokens_in_total = 0
        tokens_out_total = 0
        conversation_messages = list(messages or [])
        overall_start_time = time.time()

        for iteration in range(max_tool_iterations):
            for attempt in range(retries):
                tokens_in = -1
                tokens_out = -1
                try:
                    start_time = time.time()

                    # Convert messages to Responses API format (returns list of input items)
                    instructions, input_items = (
                        self._convert_messages_to_responses_input(
                            conversation_messages,
                            sys_msg,
                            prompt if iteration == 0 else "",
                        )
                    )

                    # If we have a vector store from file uploads, add it to config for tool conversion
                    effective_config = config.copy()
                    if vector_store_id:
                        effective_config["file_search"] = {
                            "vector_store_ids": [vector_store_id],
                            "max_num_results": config.get("file_search", {}).get(
                                "max_num_results", 10
                            ),
                        }

                    # Convert tools to Responses API format
                    responses_tools = self._convert_tools_to_responses_format(
                        clean_tools, effective_config
                    )

                    # Build API params for Responses API
                    api_params: Dict[str, Any] = {
                        "model": model_name,
                        "input": input_items,
                    }

                    # Add instructions if present
                    if instructions:
                        api_params["instructions"] = instructions

                    # Add temperature (some models like o1 and gpt-5 don't support it)
                    if not model_name.startswith("o1") and not model_name.startswith(
                        "gpt-5"
                    ):
                        api_params["temperature"] = temperature

                    # Add max tokens
                    if max_tokens:
                        api_params["max_output_tokens"] = max_tokens

                    # Add tools if present
                    if responses_tools:
                        api_params["tools"] = responses_tools
                        if tool_choice:
                            api_params["tool_choice"] = tool_choice

                    # Add response format if provided (for JSON mode)
                    if response_format:
                        # Responses API uses text.format for structured output
                        fmt_type = response_format.get("type")
                        if fmt_type == "json_object":
                            api_params["text"] = {"format": {"type": "json_object"}}
                        elif fmt_type == "json_schema":
                            api_params["text"] = {
                                "format": {
                                    "type": "json_schema",
                                    "json_schema": response_format.get(
                                        "json_schema", {}
                                    ),
                                }
                            }
                        logging.debug(f"Using response format: {response_format}")

                    # Enable reasoning/thinking if requested via config
                    if config.get("enable_thinking"):
                        reasoning_summary = config.get("reasoning_summary", "auto")
                        api_params["reasoning"] = {"summary": reasoning_summary}

                    logging.debug(
                        f"Responses API params (iteration {iteration + 1}): {api_params}"
                    )
                    response = self.client.responses.create(**api_params)
                    latency = time.time() - start_time

                    # Extract usage
                    if hasattr(response, "usage") and response.usage:
                        tokens_in = getattr(response.usage, "input_tokens", -1)
                        tokens_out = getattr(response.usage, "output_tokens", -1)
                        if tokens_in > 0:
                            tokens_in_total += tokens_in
                        if tokens_out > 0:
                            tokens_out_total += tokens_out

                    # Extract content, tool calls, and reasoning content
                    text_content, tool_calls, finish_reason, thinking_content = (
                        self._extract_response_content(response)
                    )

                    # If no tool calls or no executors, return final response
                    if not tool_calls or not has_executors:
                        total_latency = time.time() - overall_start_time
                        return TextGenerationResponse(
                            text=text_content,
                            tokens_in=tokens_in_total
                            if tokens_in_total > 0
                            else tokens_in,
                            tokens_out=tokens_out_total
                            if tokens_out_total > 0
                            else tokens_out,
                            latency=total_latency,
                            tool_calls=tool_calls if tool_calls else None,
                            tool_calls_trace=tool_calls_trace
                            if tool_calls_trace
                            else None,
                            finish_reason=finish_reason,
                            thinking_content=thinking_content
                            if thinking_content
                            else None,
                        )

                    # Execute tool calls and continue the loop
                    # Add assistant message with tool calls to conversation
                    assistant_msg = self._format_assistant_message_with_tool_calls(
                        TextGenerationResponse(
                            text=text_content,
                            tokens_in=tokens_in,
                            tokens_out=tokens_out,
                            latency=latency,
                            tool_calls=tool_calls,
                            finish_reason=finish_reason,
                        )
                    )
                    conversation_messages.append(assistant_msg)

                    # Execute each tool call
                    for tc in tool_calls:
                        trace = self._execute_tool(tc, executors)
                        tool_calls_trace.append(trace)
                        # Add tool result to conversation
                        tool_msg = self._format_tool_result_as_message(tc, trace)
                        conversation_messages.append(tool_msg)

                    # Break retry loop, continue to next iteration
                    break

                except NON_RETRYABLE_ERRORS as e:
                    logging.error(f"Non-retryable error (client error): {e}")
                    raise RuntimeError(f"Text generation failed with client error: {e}")
                except Exception as e:
                    logging.warning(
                        f"Attempt {attempt + 1}/{retries} failed: {e}. Retrying..."
                    )
                    if attempt == retries - 1:
                        raise RuntimeError(
                            f"Text generation failed after {retries} attempts: {e}"
                        )
                    time.sleep((2**attempt) * 0.5)

        # Max iterations reached
        total_latency = time.time() - overall_start_time
        return TextGenerationResponse(
            text="Reached tool iteration limit; see tool_calls_trace for details.",
            tokens_in=tokens_in_total,
            tokens_out=tokens_out_total,
            latency=total_latency,
            tool_calls=None,
            tool_calls_trace=tool_calls_trace if tool_calls_trace else None,
            finish_reason="max_iterations",
        )

    def stream_text(
        self,
        model_name: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        sys_msg: Optional[str],
        prompt: Optional[str],
        retries: Optional[int],
        config: Optional[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        response_format: Optional[Dict[str, Any]] = None,
        files: Optional[List[str]] = None,
        max_tool_iterations: int = 4,
        on_tool_call: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        on_tool_result: Optional[Callable[[str, Any], None]] = None,
    ) -> Iterable[Dict[str, Any]]:
        """Stream text using the Responses API with streaming enabled.

        When tools with executors are provided, handles the full tool loop internally,
        yielding streaming events and invoking callbacks for tool executions.
        """
        from .core.interfaces import ToolCallTrace

        model_name = model_name or "gpt-4o"
        temperature = temperature if temperature is not None else 0.5
        max_tokens = max_tokens or 100
        prompt = prompt or ""
        sys_msg = sys_msg or ""
        retries = retries or 5
        config = config or {}

        # Extract executors from tools (if any have executor functions attached)
        executors, clean_tools = self._extract_executors(tools)
        has_executors = bool(executors)

        # Handle file uploads for file_search
        vector_store_id = None
        if files:
            vector_store_id = self._prepare_files_for_search(files)
            logging.debug(
                f"Created vector store {vector_store_id} for streaming with {len(files)} file(s)"
            )

        # Tool loop state
        tool_calls_trace: List[ToolCallTrace] = []
        tokens_in_total = 0
        tokens_out_total = 0
        conversation_messages = list(messages or [])

        overall_start_time = time.time()

        for iteration in range(max_tool_iterations):
            for attempt in range(retries):
                try:
                    # Convert messages to Responses API format (returns list of input items)
                    instructions, input_items = (
                        self._convert_messages_to_responses_input(
                            conversation_messages,
                            sys_msg,
                            prompt if iteration == 0 else "",
                        )
                    )

                    # If we have a vector store from file uploads, add it to config for tool conversion
                    effective_config = config.copy()
                    if vector_store_id:
                        effective_config["file_search"] = {
                            "vector_store_ids": [vector_store_id],
                            "max_num_results": config.get("file_search", {}).get(
                                "max_num_results", 10
                            ),
                        }

                    # Convert tools to Responses API format (use clean_tools without executors)
                    responses_tools = self._convert_tools_to_responses_format(
                        clean_tools, effective_config
                    )

                    # Build API params for Responses API streaming
                    api_params: Dict[str, Any] = {
                        "model": model_name,
                        "input": input_items,
                        "stream": True,
                    }

                    # Add instructions if present
                    if instructions:
                        api_params["instructions"] = instructions

                    # Add temperature (some models like o1 don't support it)
                    if not model_name.startswith("o1") and not model_name.startswith(
                        "gpt-5"
                    ):
                        api_params["temperature"] = temperature

                    # Add max tokens
                    if max_tokens:
                        api_params["max_output_tokens"] = max_tokens

                    # Add tools if present
                    if responses_tools:
                        api_params["tools"] = responses_tools
                        if tool_choice:
                            api_params["tool_choice"] = tool_choice

                    # Add response format if provided (for JSON mode)
                    if response_format:
                        fmt_type = response_format.get("type")
                        if fmt_type == "json_object":
                            api_params["text"] = {"format": {"type": "json_object"}}
                        elif fmt_type == "json_schema":
                            api_params["text"] = {
                                "format": {
                                    "type": "json_schema",
                                    "json_schema": response_format.get(
                                        "json_schema", {}
                                    ),
                                }
                            }

                    full_text = ""
                    tool_calls_collected: List[Dict[str, Any]] = []
                    finish_reason = None
                    tokens_in = -1
                    tokens_out = -1
                    start_time = time.time()

                    # Create streaming response
                    with self.client.responses.create(**api_params) as stream:
                        for event in stream:
                            event_type = getattr(event, "type", "")

                            # Handle text delta events
                            if event_type == "response.output_text.delta":
                                delta_text = getattr(event, "delta", "")
                                if delta_text:
                                    full_text += delta_text
                                    yield {"type": "delta", "text": delta_text}

                            elif event_type == "response.output_item.added":
                                item = getattr(event, "item", None)
                                if item:
                                    name = getattr(item, "name", None)
                                    item_id = getattr(item, "id", None)
                                    call_id = getattr(item, "call_id", None)
                                    existing = next(
                                        (
                                            tc
                                            for tc in tool_calls_collected
                                            if tc.get("item_id") == item_id
                                        ),
                                        None,
                                    )
                                    if existing:
                                        existing["function"]["name"] = name
                                        if call_id:
                                            existing["id"] = call_id
                                    else:
                                        tool_calls_collected.append(
                                            {
                                                "item_id": item_id,
                                                "type": "function",
                                                "function": {
                                                    "name": name,
                                                    "arguments": "",
                                                },
                                                "id": call_id,
                                            }
                                        )

                            # Handle function call events
                            elif event_type == "response.function_call_arguments.delta":
                                # Function arguments streaming
                                item_id = getattr(event, "item_id", "")
                                call_id = getattr(event, "call_id", "")
                                delta_args = getattr(event, "delta", "")
                                # Find or create the tool call entry
                                existing = next(
                                    (
                                        tc
                                        for tc in tool_calls_collected
                                        if tc.get("item_id") == item_id
                                    ),
                                    None,
                                )
                                if existing:
                                    existing["function"]["arguments"] += delta_args
                                    # Update call_id if we got it and don't have it yet
                                    if call_id and not existing.get("id"):
                                        existing["id"] = call_id
                                else:
                                    tool_calls_collected.append(
                                        {
                                            "item_id": item_id,
                                            "type": "function",
                                            "function": {
                                                "name": "",
                                                "arguments": delta_args,
                                            },
                                            "id": call_id,
                                        }
                                    )

                            elif event_type == "response.function_call_arguments.done":
                                # Function call complete
                                item_id = getattr(event, "item_id", "")
                                call_id = getattr(event, "call_id", "")
                                arguments = getattr(event, "arguments", "")
                                existing = next(
                                    (
                                        tc
                                        for tc in tool_calls_collected
                                        if tc.get("item_id") == item_id
                                    ),
                                    None,
                                )
                                if existing:
                                    existing["function"]["arguments"] = arguments
                                    # Update call_id if we got it and don't have it yet
                                    if call_id and not existing.get("id"):
                                        existing["id"] = call_id
                                else:
                                    tool_calls_collected.append(
                                        {
                                            "item_id": item_id,
                                            "id": call_id,
                                            "type": "function",
                                            "function": {
                                                "name": "",
                                                "arguments": arguments,
                                            },
                                        }
                                    )
                                finish_reason = "tool_calls"

                            # Handle file search events
                            elif event_type == "response.file_search_call.searching":
                                logging.debug(
                                    f"File search in progress: {getattr(event, 'queries', [])}"
                                )

                            elif event_type == "response.file_search_call.completed":
                                logging.debug("File search completed")

                            # Handle completion events
                            elif event_type == "response.completed":
                                response_obj = getattr(event, "response", None)
                                if response_obj:
                                    usage = getattr(response_obj, "usage", None)
                                    if usage:
                                        tokens_in = getattr(usage, "input_tokens", -1)
                                        tokens_out = getattr(usage, "output_tokens", -1)
                                        if tokens_in > 0:
                                            tokens_in_total += tokens_in
                                        if tokens_out > 0:
                                            tokens_out_total += tokens_out
                                if not finish_reason:
                                    finish_reason = "stop"

                    latency = time.time() - start_time

                    # Filter out any incomplete tool calls (missing function name)
                    valid_tool_calls = [
                        tc
                        for tc in tool_calls_collected
                        if tc.get("function", {}).get("name")
                    ]

                    # If no tool calls or no executors, yield final response and return
                    if not valid_tool_calls or not has_executors:
                        total_latency = time.time() - overall_start_time
                        response = TextGenerationResponse(
                            text=full_text.strip(),
                            tokens_in=tokens_in_total
                            if tokens_in_total > 0
                            else tokens_in,
                            tokens_out=tokens_out_total
                            if tokens_out_total > 0
                            else tokens_out,
                            latency=total_latency,
                            tool_calls_trace=tool_calls_trace
                            if tool_calls_trace
                            else None,
                        )

                        final_data: Dict[str, Any] = {
                            "type": "final",
                            "response": response.model_dump(),
                        }
                        if valid_tool_calls:
                            final_data["tool_calls"] = valid_tool_calls
                        if finish_reason:
                            final_data["finish_reason"] = finish_reason

                        yield final_data
                        return

                    # Execute tool calls and continue the loop
                    # Convert collected tool calls to ToolCall objects
                    tool_call_objects: List[ToolCall] = []
                    for tc in valid_tool_calls:
                        args_str = tc.get("function", {}).get("arguments", "{}")
                        try:
                            args = json.loads(args_str) if args_str else {}
                        except json.JSONDecodeError:
                            args = {}
                        tool_call_objects.append(
                            ToolCall(
                                id=tc.get("id") or tc.get("item_id") or "",
                                name=tc.get("function", {}).get("name", ""),
                                arguments=args,
                            )
                        )

                    # Add assistant message with tool calls to conversation
                    assistant_msg = self._format_assistant_message_with_tool_calls(
                        TextGenerationResponse(
                            text=full_text.strip(),
                            tokens_in=tokens_in,
                            tokens_out=tokens_out,
                            latency=latency,
                            tool_calls=tool_call_objects,
                            finish_reason=finish_reason,
                        )
                    )
                    conversation_messages.append(assistant_msg)

                    # Execute each tool call
                    for tc in tool_call_objects:
                        # Invoke on_tool_call callback if provided
                        if on_tool_call:
                            on_tool_call(tc.name, tc.arguments)

                        # Yield tool_call event
                        yield {
                            "type": "tool_call",
                            "tool_name": tc.name,
                            "arguments": tc.arguments,
                        }

                        # Execute the tool
                        trace = self._execute_tool(tc, executors)
                        tool_calls_trace.append(trace)

                        # Invoke on_tool_result callback if provided
                        if on_tool_result:
                            on_tool_result(tc.name, trace)

                        # Yield tool_result event
                        yield {
                            "type": "tool_result",
                            "tool_name": tc.name,
                            "result": trace.result if trace.success else trace.error,
                            "success": trace.success,
                        }

                        # Add tool result to conversation
                        tool_msg = self._format_tool_result_as_message(tc, trace)
                        conversation_messages.append(tool_msg)

                    # Break retry loop, continue to next iteration
                    break

                except NON_RETRYABLE_ERRORS as e:
                    logging.error(f"Non-retryable streaming error (client error): {e}")
                    raise RuntimeError(f"Streaming failed with client error: {e}")
                except Exception as e:
                    logging.warning(
                        f"Streaming attempt {attempt + 1}/{retries} failed: {e}. Retrying..."
                    )
                    logging.error(e)
                    if attempt == retries - 1:
                        raise RuntimeError(
                            f"Streaming failed after {retries} attempts: {e}"
                        )
                    time.sleep((2**attempt) * 0.5)

        # Max iterations reached
        total_latency = time.time() - overall_start_time
        response = TextGenerationResponse(
            text="Reached tool iteration limit; see tool_calls_trace for details.",
            tokens_in=tokens_in_total,
            tokens_out=tokens_out_total,
            latency=total_latency,
            tool_calls_trace=tool_calls_trace if tool_calls_trace else None,
        )
        yield {
            "type": "final",
            "response": response.model_dump(),
            "finish_reason": "max_iterations",
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
            assert "model" in config, "Model name is required in config"
            assert isinstance(config.get("model"), str), "Model name must be a string"
            assert isinstance(config.get("temperature", 0.7), (float, int)), (
                "Temperature must be a number"
            )
            assert isinstance(config.get("max_tokens", 256), int), (
                "Max tokens must be an integer"
            )
            return True
        except AssertionError as e:
            logging.error(f"OpenAI Provider Validation Failed: {e}")
            return False

    # ==================== File Search / Vector Store Methods ====================

    def create_vector_store(self, name: str) -> str:
        """
        Create a new vector store for file search.

        Args:
            name: Name for the vector store

        Returns:
            The vector store ID
        """
        vector_store = self.client.vector_stores.create(name=name)
        logging.debug(f"Created vector store: {vector_store.id} ({name})")
        return vector_store.id

    def upload_file_to_vector_store(
        self,
        vector_store_id: str,
        file_path: str,
    ) -> str:
        """
        Upload a file to a vector store for file search.

        Args:
            vector_store_id: The vector store ID to upload to
            file_path: Path to the file to upload

        Returns:
            The file ID
        """
        with open(file_path, "rb") as f:
            file_obj = self.client.files.create(file=f, purpose="assistants")

        # Add file to vector store
        self.client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_obj.id,
        )

        logging.debug(f"Uploaded file {file_path} to vector store {vector_store_id}")
        self._vector_store_cache[file_path] = vector_store_id
        return file_obj.id

    def create_vector_store_with_file(
        self,
        name: str,
        file_path: str,
    ) -> tuple[str, str]:
        """
        Create a vector store and upload a file to it in one operation.

        Args:
            name: Name for the vector store
            file_path: Path to the file to upload

        Returns:
            Tuple of (vector_store_id, file_id)
        """
        vector_store_id = self.create_vector_store(name)
        file_id = self.upload_file_to_vector_store(vector_store_id, file_path)
        return vector_store_id, file_id

    def delete_vector_store(self, vector_store_id: str) -> bool:
        """
        Delete a vector store.

        Args:
            vector_store_id: The vector store ID to delete

        Returns:
            True if deleted successfully
        """
        try:
            self.client.vector_stores.delete(vector_store_id)
            # Remove from cache
            self._vector_store_cache = {
                k: v
                for k, v in self._vector_store_cache.items()
                if v != vector_store_id
            }
            logging.debug(f"Deleted vector store: {vector_store_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to delete vector store {vector_store_id}: {e}")
            return False

    def get_vector_store_for_file(self, file_path: str) -> Optional[str]:
        """
        Get the vector store ID for a previously uploaded file.

        Args:
            file_path: Path to the file

        Returns:
            Vector store ID if found, None otherwise
        """
        return self._vector_store_cache.get(file_path)
