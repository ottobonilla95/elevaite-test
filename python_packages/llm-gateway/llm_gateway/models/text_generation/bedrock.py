import json
import logging
import time
from typing import Dict, Any, Optional, List, Iterable, Callable
import boto3
from botocore.exceptions import ClientError


from .core.base import BaseTextGenerationProvider
from .core.interfaces import TextGenerationResponse, ToolCall, ToolCallTrace
from ...tools.web_search import web_search, format_search_results


class BedrockTextGenerationProvider(BaseTextGenerationProvider):
    def __init__(
        self, aws_access_key_id: str, aws_secret_access_key: str, region_name: str
    ):
        self.client = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
        )

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
        if files:
            raise NotImplementedError(
                "File search is only supported by the OpenAI provider"
            )
        model_name = model_name or "anthropic.claude-instant-v1"
        temperature = temperature if temperature is not None else 0.5

        max_tokens = max_tokens if max_tokens is not None else 100
        sys_msg = sys_msg or ""
        prompt = prompt or ""
        retries = retries if retries is not None else 5
        config = config or {}

        # Check if model supports function calling
        supports_tools = self._model_supports_tools(model_name)

        if tools and not supports_tools:
            logging.warning(
                f"Model {model_name} does not support function calling. Ignoring tools parameter."
            )
            tools = None

        # Use Converse API if tools are provided or model supports it
        if supports_tools:
            return self._generate_with_converse_api(
                model_name,
                temperature,
                max_tokens,
                sys_msg,
                prompt,
                retries,
                tools,
                tool_choice,
                messages,
                config,
                max_tool_iterations,
            )
        else:
            return self._generate_with_legacy_api(
                model_name, temperature, max_tokens, sys_msg, prompt, retries
            )

    def _model_supports_tools(self, model_name: str) -> bool:
        """Check if the model supports function calling"""
        # Models that support function calling in Bedrock
        tool_supporting_models = [
            "anthropic.claude-3",
            "anthropic.claude-3-5",
            "meta.llama3-1",
            "meta.llama3-2",
            "cohere.command-r",
        ]

        return any(model_id in model_name for model_id in tool_supporting_models)

    def _generate_with_legacy_api(
        self,
        model_name: str,
        temperature: float,
        max_tokens: int,
        sys_msg: str,
        prompt: str,
        retries: int,
    ) -> TextGenerationResponse:
        """Generate text using legacy Bedrock API (for models without tool support)"""

        formatted_prompt = f"Human: {prompt}\n\nAssistant:{sys_msg}"

        payload = {
            "prompt": formatted_prompt,
            "temperature": temperature,
            "max_tokens_to_sample": max_tokens,
        }

        if any(keyword in model_name for keyword in ["meta", "llama"]):
            model_name = self.get_inference_profile_for_model(model_name)
            logging.info(f"Special handling for model: {model_name}")

        for attempt in range(retries):
            try:
                start_time = time.time()
                response = self.client.invoke_model(
                    modelId=model_name,
                    body=json.dumps(payload),
                )
                latency = time.time() - start_time

                response_body_raw = response["body"].read().decode("utf-8")
                logging.debug(f"Full response body: {response_body_raw}")
                response_body = json.loads(response_body_raw)

                if "completion" in response_body:
                    completion_text = response_body["completion"].strip()

                    # Attempt to retrieve token counts if available
                    tokens_in = response_body.get("input_tokens", len(prompt.split()))
                    tokens_out = response_body.get(
                        "output_tokens", len(completion_text.split())
                    )

                    return TextGenerationResponse(
                        text=completion_text,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        latency=latency,
                    )

                raise ValueError(
                    "Invalid response structure: Missing 'completion' key."
                )

            except ClientError as e:
                logging.warning(
                    f"Attempt {attempt + 1}/{retries} failed due to ClientError: {e}. Retrying..."
                )
                if attempt == retries - 1:
                    raise RuntimeError(
                        f"Text generation failed after {retries} attempts: {e}"
                    )
                time.sleep((2**attempt) * 0.5)

            except ValueError as ve:
                logging.error(f"ValueError encountered: {ve}")
                raise ve

        raise RuntimeError(f"Text generation failed after {retries} attempts")

    def _generate_with_converse_api(
        self,
        model_name: str,
        temperature: float,
        max_tokens: int,
        sys_msg: str,
        prompt: str,
        retries: int,
        tools: Optional[List[Dict[str, Any]]],
        tool_choice: Optional[str],
        messages: Optional[List[Dict[str, Any]]],
        config: Optional[Dict[str, Any]] = None,
        max_tool_iterations: int = 4,
    ) -> TextGenerationResponse:
        """Generate text using Bedrock Converse API with tool loop support"""

        # Extract executors from tools
        executors, clean_tools = self._extract_executors(tools)
        has_executors = bool(executors)

        # Prepare messages; prefer explicit messages if provided
        conversation_messages: List[Dict[str, Any]] = list(
            messages
            if isinstance(messages, list) and len(messages) > 0
            else [{"role": "user", "content": [{"text": prompt}]}]
        )

        # Prepare inference config
        inference_config = {
            "temperature": temperature,
            "maxTokens": max_tokens,
        }

        # Prepare system messages
        system_messages = []
        if sys_msg:
            system_messages.append({"text": sys_msg})

        # Convert tools to Bedrock format
        tool_config = None
        if clean_tools:
            tool_config = self._convert_tools_to_bedrock_format(clean_tools)

        # Tool loop state
        tool_calls_trace: List[ToolCallTrace] = []
        tokens_in_total = 0
        tokens_out_total = 0
        overall_start_time = time.time()

        for iteration in range(max_tool_iterations):
            for attempt in range(retries):
                try:
                    # Prepare converse parameters
                    converse_params: Dict[str, Any] = {
                        "modelId": model_name,
                        "messages": conversation_messages,
                        "inferenceConfig": inference_config,
                    }

                    if system_messages:
                        converse_params["system"] = system_messages

                    if tool_config:
                        converse_params["toolConfig"] = tool_config

                    # Enable extended thinking if requested via config
                    if config and config.get("enable_thinking"):
                        budget_tokens = config.get("thinking_budget_tokens", 1024)
                        converse_params["additionalModelRequestFields"] = {
                            "thinking": {
                                "type": "enabled",
                                "budget_tokens": budget_tokens,
                            }
                        }

                    response = self.client.converse(**converse_params)

                    # Extract response content
                    output = response.get("output", {})
                    message = output.get("message", {})
                    content = message.get("content", [])

                    text_content = ""
                    thinking_content = ""
                    tool_calls: List[ToolCall] = []
                    finish_reason = response.get("stopReason", "stop")

                    for content_block in content:
                        if content_block.get("type") == "thinking":
                            thinking_content += content_block.get("thinking", "")
                        elif "text" in content_block:
                            text_content += content_block["text"]
                        elif "toolUse" in content_block:
                            tool_use = content_block["toolUse"]
                            tool_calls.append(
                                ToolCall(
                                    id=tool_use.get(
                                        "toolUseId", f"call_{len(tool_calls)}"
                                    ),
                                    name=tool_use.get("name", "unknown_function"),
                                    arguments=tool_use.get("input", {}),
                                )
                            )

                    # Get token usage
                    usage = response.get("usage", {})
                    tokens_in = usage.get("inputTokens", len(prompt.split()))
                    tokens_out = usage.get(
                        "outputTokens", len(text_content.split()) if text_content else 0
                    )
                    tokens_in_total += tokens_in
                    tokens_out_total += tokens_out

                    # If no tool calls or no executors, return final response
                    if not tool_calls or not has_executors:
                        total_latency = time.time() - overall_start_time
                        return TextGenerationResponse(
                            text=text_content.strip(),
                            tokens_in=tokens_in_total,
                            tokens_out=tokens_out_total,
                            latency=total_latency,
                            tool_calls=tool_calls if tool_calls else None,
                            tool_calls_trace=tool_calls_trace
                            if tool_calls_trace
                            else None,
                            finish_reason=finish_reason,
                            thinking_content=thinking_content.strip()
                            if thinking_content
                            else None,
                        )

                    # Add assistant message with tool calls to conversation
                    conversation_messages.append(
                        {"role": "assistant", "content": content}
                    )

                    # Execute each tool and add results
                    tool_result_content = []
                    for tc in tool_calls:
                        trace = self._execute_tool(tc, executors)
                        tool_calls_trace.append(trace)

                        # Format result for Bedrock
                        result_value = (
                            trace.result if trace.success else {"error": trace.error}
                        )
                        tool_result_content.append(
                            {
                                "toolResult": {
                                    "toolUseId": tc.id,
                                    "content": [{"json": result_value}]
                                    if isinstance(result_value, dict)
                                    else [{"text": str(result_value)}],
                                }
                            }
                        )

                    conversation_messages.append(
                        {"role": "user", "content": tool_result_content}
                    )
                    break  # Success, continue to next iteration

                except ClientError as e:
                    logging.warning(
                        f"Attempt {attempt + 1}/{retries} failed due to ClientError: {e}. Retrying..."
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
            tool_calls_trace=tool_calls_trace if tool_calls_trace else None,
            finish_reason="max_iterations",
        )

    def _convert_tools_to_bedrock_format(
        self, openai_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Convert OpenAI-style tools to Bedrock toolConfig format.

        Built-in tools like web_search are converted to function tools that
        call our fallback implementation.
        """

        tool_specs = []
        for tool in openai_tools:
            tool_type = tool.get("type")

            # Handle web_search built-in tool by converting to a function
            if tool_type == "web_search":
                tool_spec = {
                    "toolSpec": {
                        "name": "web_search",
                        "description": "Search the web for current information. Use this to find up-to-date information about any topic.",
                        "inputSchema": {
                            "json": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "The search query to look up on the web",
                                    },
                                    "num_results": {
                                        "type": "integer",
                                        "description": "Number of results to return (1-10)",
                                        "default": 3,
                                    },
                                },
                                "required": ["query"],
                            }
                        },
                    }
                }
                tool_specs.append(tool_spec)
                logging.debug("Added web_search fallback tool for Bedrock")

            elif tool_type == "function":
                func_def = tool["function"]

                tool_spec = {
                    "toolSpec": {
                        "name": func_def["name"],
                        "description": func_def.get("description", ""),
                        "inputSchema": {"json": func_def.get("parameters", {})},
                    }
                }
                tool_specs.append(tool_spec)

        return {"tools": tool_specs} if tool_specs else {}

    def execute_web_search(self, query: str, num_results: int = 3) -> str:
        """
        Execute a web search using the fallback implementation.

        This is called when the model requests a web_search tool call.

        Args:
            query: The search query
            num_results: Number of results to return

        Returns:
            Formatted search results as a string
        """
        try:
            results = web_search(query=query, num_results=num_results)
            return format_search_results(results, include_content=True)
        except Exception as e:
            logging.error(f"Web search failed: {e}")
            return f"Web search failed: {e}"

    def get_inference_profile_for_model(self, model_name: str) -> str:
        """
        Retrieves the appropriate inference profile for a model containing 'meta' or 'llama'.
        """
        # We map the model names to their supported inferences profile.
        inference_profiles = {  # FIXME add the correct inference id
            "meta.llama3-3-70b-instruct-v1:0": "arn:aws:bedrock:region:account-id:inference-profile/inference-profile-id",
        }

        if model_name in inference_profiles:
            return inference_profiles[model_name]

        # Default behavior if no special case is found
        return model_name

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
        on_tool_result: Optional[Callable[[str, ToolCallTrace], None]] = None,
    ) -> Iterable[Dict[str, Any]]:
        """Stream text generation using Bedrock Converse Stream API with tool loop support."""
        if files:
            raise NotImplementedError(
                "File search is only supported by the OpenAI provider"
            )

        model_name = model_name or "anthropic.claude-instant-v1"
        temperature = temperature if temperature is not None else 0.5
        max_tokens = max_tokens if max_tokens is not None else 100
        sys_msg = sys_msg or ""
        prompt = prompt or ""
        retries = retries if retries is not None else 5
        config = config or {}

        # Check if model supports function calling
        supports_tools = self._model_supports_tools(model_name)

        if tools and not supports_tools:
            logging.warning(
                f"Model {model_name} does not support function calling. Ignoring tools parameter."
            )
            tools = None

        # Extract executors from tools
        executors, clean_tools = self._extract_executors(tools)
        has_executors = bool(executors)

        # Prepare messages
        conversation_messages: List[Dict[str, Any]] = list(
            messages
            if isinstance(messages, list) and len(messages) > 0
            else [{"role": "user", "content": [{"text": prompt}]}]
        )

        # Prepare inference config
        inference_config = {"temperature": temperature, "maxTokens": max_tokens}

        # Prepare system messages
        system_messages = []
        if sys_msg:
            system_messages.append({"text": sys_msg})

        # Convert tools to Bedrock format
        tool_config = None
        if clean_tools:
            tool_config = self._convert_tools_to_bedrock_format(clean_tools)

        # Tool loop state
        tool_calls_trace: List[ToolCallTrace] = []
        tokens_in_total = 0
        tokens_out_total = 0
        overall_start_time = time.time()

        for iteration in range(max_tool_iterations):
            for attempt in range(retries):
                try:
                    full_text = ""
                    tool_uses: List[Dict[str, Any]] = []
                    current_tool_use: Optional[Dict[str, Any]] = None
                    tokens_in: int = 0
                    tokens_out: int = 0

                    # Prepare converse parameters
                    converse_params: Dict[str, Any] = {
                        "modelId": model_name,
                        "messages": conversation_messages,
                        "inferenceConfig": inference_config,
                    }

                    if system_messages:
                        converse_params["system"] = system_messages
                    if tool_config:
                        converse_params["toolConfig"] = tool_config
                    if config and config.get("enable_thinking"):
                        budget_tokens = config.get("thinking_budget_tokens", 1024)
                        converse_params["additionalModelRequestFields"] = {
                            "thinking": {
                                "type": "enabled",
                                "budget_tokens": budget_tokens,
                            }
                        }

                    # Use streaming API
                    response = self.client.converse_stream(**converse_params)

                    for event in response.get("stream", []):
                        # Handle content block delta (text)
                        if "contentBlockDelta" in event:
                            delta = event["contentBlockDelta"].get("delta", {})
                            if "text" in delta:
                                text = delta["text"]
                                full_text += text
                                yield {"type": "delta", "text": text}
                            # Handle tool input JSON delta
                            if "toolUse" in delta and current_tool_use:
                                input_delta = delta["toolUse"].get("input", "")
                                current_tool_use["input_json"] += input_delta

                        # Handle content block start
                        if "contentBlockStart" in event:
                            start = event["contentBlockStart"].get("start", {})
                            if "toolUse" in start:
                                current_tool_use = {
                                    "toolUseId": start["toolUse"].get("toolUseId"),
                                    "name": start["toolUse"].get("name"),
                                    "input_json": "",
                                }

                        # Handle content block stop
                        if "contentBlockStop" in event:
                            if current_tool_use:
                                try:
                                    input_args = (
                                        json.loads(current_tool_use["input_json"])
                                        if current_tool_use["input_json"]
                                        else {}
                                    )
                                except json.JSONDecodeError:
                                    input_args = {}
                                tool_uses.append(
                                    {
                                        "toolUseId": current_tool_use["toolUseId"],
                                        "name": current_tool_use["name"],
                                        "input": input_args,
                                    }
                                )
                                current_tool_use = None

                        # Handle metadata (token counts)
                        if "metadata" in event:
                            usage = event["metadata"].get("usage", {})
                            tokens_in = usage.get("inputTokens", 0)
                            tokens_out = usage.get("outputTokens", 0)

                    tokens_in_total += (
                        tokens_in if tokens_in > 0 else len(prompt.split())
                    )
                    tokens_out_total += (
                        tokens_out if tokens_out > 0 else len(full_text.split())
                    )

                    # Convert tool_uses to ToolCall objects
                    tool_calls = [
                        ToolCall(
                            id=tu["toolUseId"], name=tu["name"], arguments=tu["input"]
                        )
                        for tu in tool_uses
                    ]

                    # If no tool calls or no executors, return final response
                    if not tool_calls or not has_executors:
                        total_latency = time.time() - overall_start_time
                        response_obj = TextGenerationResponse(
                            text=full_text.strip(),
                            tokens_in=tokens_in_total,
                            tokens_out=tokens_out_total,
                            latency=total_latency,
                            tool_calls=tool_calls if tool_calls else None,
                            tool_calls_trace=tool_calls_trace
                            if tool_calls_trace
                            else None,
                            finish_reason="tool_calls" if tool_calls else "stop",
                        )
                        yield {"type": "final", "response": response_obj.model_dump()}
                        return

                    # Yield tool_call events
                    for tc in tool_calls:
                        yield {
                            "type": "tool_call",
                            "tool_name": tc.name,
                            "arguments": tc.arguments,
                        }
                        if on_tool_call:
                            on_tool_call(tc.name, tc.arguments)

                    # Add assistant message with tool calls
                    assistant_content = []
                    if full_text:
                        assistant_content.append({"text": full_text})
                    for tu in tool_uses:
                        assistant_content.append({"toolUse": tu})
                    conversation_messages.append(
                        {"role": "assistant", "content": assistant_content}
                    )

                    # Execute each tool and add results
                    tool_result_content = []
                    for tc in tool_calls:
                        trace = self._execute_tool(tc, executors)
                        tool_calls_trace.append(trace)

                        yield {
                            "type": "tool_result",
                            "tool_name": tc.name,
                            "trace": trace.model_dump(),
                        }
                        if on_tool_result:
                            on_tool_result(tc.name, trace)

                        result_value = (
                            trace.result if trace.success else {"error": trace.error}
                        )
                        tool_result_content.append(
                            {
                                "toolResult": {
                                    "toolUseId": tc.id,
                                    "content": [{"json": result_value}]
                                    if isinstance(result_value, dict)
                                    else [{"text": str(result_value)}],
                                }
                            }
                        )

                    conversation_messages.append(
                        {"role": "user", "content": tool_result_content}
                    )
                    break  # Success, continue to next iteration

                except ClientError as e:
                    logging.warning(
                        f"Streaming attempt {attempt + 1}/{retries} failed: {e}. Retrying..."
                    )
                    if attempt == retries - 1:
                        raise RuntimeError(
                            f"Streaming failed after {retries} attempts: {e}"
                        )
                    time.sleep((2**attempt) * 0.5)

        # Max iterations reached
        total_latency = time.time() - overall_start_time
        response_obj = TextGenerationResponse(
            text="Reached tool iteration limit; see tool_calls_trace for details.",
            tokens_in=tokens_in_total,
            tokens_out=tokens_out_total,
            latency=total_latency,
            tool_calls_trace=tool_calls_trace if tool_calls_trace else None,
            finish_reason="max_iterations",
        )
        yield {
            "type": "final",
            "response": response_obj.model_dump(),
            "finish_reason": "max_iterations",
        }

    def validate_config(self, config: Dict[str, Any]) -> bool:
        try:
            assert isinstance(config, dict), "Config must be a dictionary."
            assert "model" in config, "Model ID is required in the config."
            assert isinstance(config.get("model"), str), "Model ID must be a string."
            assert isinstance(config.get("temperature", 0.7), (float, int)), (
                "Temperature must be a number."
            )
            assert isinstance(config.get("max_tokens", 256), int), (
                "Max tokens must be an integer."
            )
            return True
        except AssertionError as e:
            logging.error(f"Amazon Bedrock Provider Validation Failed: {e}")
            return False
