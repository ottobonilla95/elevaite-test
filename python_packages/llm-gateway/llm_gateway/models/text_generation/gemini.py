import logging
import time
import json
from typing import Dict, Any, Optional, List, Iterable

from .core.base import BaseTextGenerationProvider
from .core.interfaces import TextGenerationResponse, ToolCall

from google import genai
from google.genai import types


class GeminiTextGenerationProvider(BaseTextGenerationProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

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
    ) -> TextGenerationResponse:
        if files:
            raise NotImplementedError("File search is only supported by the OpenAI provider")
        model_name = model_name or "gemini-1.5-flash"
        temperature = temperature or 0.5
        max_tokens = max_tokens or 10000  # Higher default to accommodate Gemini 2.5's thinking tokens
        prompt = prompt or ""
        retries = retries or 5
        config = config or {}

        # Convert OpenAI-style tools to Gemini format
        gemini_tools = None
        if tools:
            gemini_tools = self._convert_tools_to_gemini_format(tools)

        # Extract system instruction from messages or sys_msg
        system_instruction = None
        if messages and isinstance(messages, list) and len(messages) > 0:
            # Check if first message is a system message
            if messages[0].get("role") == "system":
                system_instruction = messages[0].get("content", "")
        if not system_instruction and sys_msg:
            system_instruction = sys_msg

        # Create generation config with system instruction
        # Note: Gemini 2.5+ models have a "thinking" feature that uses tokens from max_output_tokens.
        # We use a higher default (10k) to accommodate both thinking and response generation.
        generation_config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction if system_instruction else None,
        )

        if gemini_tools:
            generation_config.tools = gemini_tools

        # Create content with messages (excluding system messages, which go in system_instruction)
        contents = []
        if messages and isinstance(messages, list) and len(messages) > 0:
            # Map generic {role, content} messages to Gemini's Content/Part
            role_map = {"user": "user", "assistant": "model", "tool": "user"}
            for m in messages:
                msg_role = str(m.get("role", "user")).lower()
                # Skip system messages - they're handled via system_instruction
                if msg_role == "system":
                    continue
                role = role_map.get(msg_role, "user")
                text = m.get("content")
                if text is None:
                    continue
                contents.append(types.Content(role=role, parts=[types.Part(text=str(text))]))
        else:
            if sys_msg:
                # sys_msg already set as system_instruction, just add the user prompt
                contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))
            else:
                contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

        for attempt in range(retries):
            try:
                start_time = time.time()

                # Make the API call
                response = self.client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=generation_config,
                )

                latency = time.time() - start_time

                # Handle response with potential function calls
                text_content = ""
                tool_calls = []
                finish_reason = "stop"

                # Check for function calls in the modern API
                if hasattr(response, "function_calls") and response.function_calls:
                    for func_call in response.function_calls:
                        tool_calls.append(
                            ToolCall(
                                id=f"call_{len(tool_calls)}",
                                name=func_call.name or "unknown_function",
                                arguments=func_call.args or {},
                            )
                        )
                        finish_reason = "tool_calls"

                # Get text content
                if hasattr(response, "text") and response.text:
                    text_content = response.text

                # Get token counts from usage_metadata (Gemini's response structure)
                tokens_in = len(prompt.split())  # fallback
                tokens_out = len(text_content.split()) if text_content else 0  # fallback
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage = response.usage_metadata
                    if hasattr(usage, "prompt_token_count") and usage.prompt_token_count:
                        tokens_in = usage.prompt_token_count
                    if hasattr(usage, "candidates_token_count") and usage.candidates_token_count:
                        tokens_out = usage.candidates_token_count

                return TextGenerationResponse(
                    text=text_content.strip(),
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    latency=latency,
                    tool_calls=tool_calls if tool_calls else None,
                    finish_reason=finish_reason,
                )

            except Exception as e:
                logging.warning(f"Attempt {attempt + 1}/{retries} failed: {e}. Retrying...")
                if attempt == retries - 1:
                    raise RuntimeError(f"Text generation failed after {retries} attempts: {e}")
                time.sleep((2**attempt) * 0.5)

        # This should never be reached due to the exception handling above,
        # but adding for type safety
        raise RuntimeError("Text generation failed: unexpected code path")

    def _convert_tools_to_gemini_format(self, openai_tools: List[Dict[str, Any]]) -> List[Any]:
        """
        Convert OpenAI-style tool definitions to Gemini format.

        OpenAI format:
        {
            "type": "function",
            "function": {
                "name": "function_name",
                "description": "Function description",
                "parameters": {...}
            }
        }

        Gemini format uses google.genai.types.Tool
        """
        try:
            gemini_functions = []
            for tool in openai_tools:
                if tool.get("type") == "function":
                    func_def = tool["function"]

                    # Create Gemini function declaration
                    gemini_func = types.FunctionDeclaration(
                        name=func_def["name"],
                        description=func_def.get("description", ""),
                        parameters=func_def.get("parameters", {}),
                    )
                    gemini_functions.append(gemini_func)

            # Return as Gemini Tool
            if gemini_functions:
                return [types.Tool(function_declarations=gemini_functions)]

        except Exception as e:
            logging.warning(f"Could not convert tools to Gemini format: {e}")
            logging.warning("Tools will be ignored for Gemini provider")

        return []

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
    ) -> Iterable[Dict[str, Any]]:
        """Stream text generation using Gemini's streaming API."""
        if files:
            raise NotImplementedError("File search is only supported by the OpenAI provider")

        model_name = model_name or "gemini-1.5-flash"
        temperature = temperature or 0.5
        max_tokens = max_tokens or 100
        prompt = prompt or ""
        retries = retries or 5
        config = config or {}

        # Convert OpenAI-style tools to Gemini format
        gemini_tools = None
        if tools:
            gemini_tools = self._convert_tools_to_gemini_format(tools)

        # Create generation config
        generation_config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        if gemini_tools:
            generation_config.tools = gemini_tools

        # Create content with system instruction or use provided messages
        contents = []
        if messages and isinstance(messages, list) and len(messages) > 0:
            # Map generic {role, content} messages to Gemini's Content/Part
            role_map = {"system": "user", "user": "user", "assistant": "model", "tool": "user"}
            for m in messages:
                role = role_map.get(str(m.get("role", "user")).lower(), "user")
                text = m.get("content")
                if text is None:
                    continue
                contents.append(types.Content(role=role, parts=[types.Part(text=str(text))]))
        else:
            if sys_msg:
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=f"System: {sys_msg}\n\nUser: {prompt}")],
                    )
                )
            else:
                contents.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

        for attempt in range(retries):
            try:
                start_time = time.time()
                full_text = ""
                tool_calls_collected: List[Dict[str, Any]] = []
                finish_reason: Optional[str] = None
                tokens_in: int = -1
                tokens_out: int = -1

                # Use streaming API
                for chunk in self.client.models.generate_content_stream(
                    model=model_name,
                    contents=contents,
                    config=generation_config,
                ):
                    # Handle parts from candidates (proper structure for thinking models)
                    if hasattr(chunk, "candidates") and chunk.candidates:
                        for candidate in chunk.candidates:
                            if hasattr(candidate, "content") and candidate.content:
                                if hasattr(candidate.content, "parts") and candidate.content.parts:
                                    for part in candidate.content.parts:
                                        # Skip thought parts - only stream actual text response
                                        if hasattr(part, "thought") and part.thought:
                                            continue
                                        # Handle text parts
                                        if hasattr(part, "text") and part.text:
                                            delta_text = part.text
                                            full_text += delta_text
                                            yield {"type": "delta", "text": delta_text}
                                        # Handle function call parts
                                        if hasattr(part, "function_call") and part.function_call:
                                            func_call = part.function_call
                                            tool_call = {
                                                "id": f"call_{len(tool_calls_collected)}",
                                                "type": "function",
                                                "function": {
                                                    "name": getattr(func_call, "name", None) or "unknown_function",
                                                    "arguments": json.dumps(getattr(func_call, "args", {}) or {}),
                                                },
                                            }
                                            tool_calls_collected.append(tool_call)
                                            finish_reason = "tool_calls"

                    # Fallback: try chunk.text for non-thinking models
                    elif hasattr(chunk, "text") and chunk.text:
                        delta_text = chunk.text
                        full_text += delta_text
                        yield {"type": "delta", "text": delta_text}

                    # Handle function calls at chunk level (alternative API structure)
                    if hasattr(chunk, "function_calls") and chunk.function_calls:
                        for func_call in chunk.function_calls:
                            tool_call = {
                                "id": f"call_{len(tool_calls_collected)}",
                                "type": "function",
                                "function": {
                                    "name": func_call.name or "unknown_function",
                                    "arguments": json.dumps(func_call.args or {}),
                                },
                            }
                            tool_calls_collected.append(tool_call)
                        finish_reason = "tool_calls"

                    # Try to get usage metadata from chunk (usually only in final chunk)
                    if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                        usage = chunk.usage_metadata
                        logging.debug(f"Gemini usage_metadata: {usage}")
                        if hasattr(usage, "prompt_token_count") and usage.prompt_token_count is not None:
                            tokens_in = usage.prompt_token_count
                            logging.debug(f"Gemini tokens_in from usage: {tokens_in}")
                        if hasattr(usage, "candidates_token_count") and usage.candidates_token_count is not None:
                            tokens_out = usage.candidates_token_count
                            logging.debug(f"Gemini tokens_out from usage: {tokens_out}")

                latency = time.time() - start_time

                if not finish_reason:
                    finish_reason = "stop"

                # Build final response
                response = TextGenerationResponse(
                    text=full_text.strip(),
                    tokens_in=tokens_in if tokens_in > 0 else len(prompt.split()),
                    tokens_out=tokens_out if tokens_out > 0 else len(full_text.split()),
                    latency=latency,
                    tool_calls=[
                        ToolCall(
                            id=tc["id"],
                            name=tc["function"]["name"],
                            arguments=json.loads(tc["function"]["arguments"]),
                        )
                        for tc in tool_calls_collected
                    ]
                    if tool_calls_collected
                    else None,
                    finish_reason=finish_reason,
                )

                final_data: Dict[str, Any] = {"type": "final", "response": response.model_dump()}
                if tool_calls_collected:
                    final_data["tool_calls"] = tool_calls_collected
                if finish_reason:
                    final_data["finish_reason"] = finish_reason

                yield final_data
                return

            except Exception as e:
                logging.warning(f"Streaming attempt {attempt + 1}/{retries} failed: {e}. Retrying...")
                if attempt == retries - 1:
                    raise RuntimeError(f"Streaming failed after {retries} attempts: {e}")
                time.sleep((2**attempt) * 0.5)

    def validate_config(self, config: Dict[str, Any]) -> bool:
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
            assert "model" in config, "Model name is required in config"
            assert isinstance(config["model"], str), "Model name must be a string"
            return True
        except AssertionError as e:
            logging.error(f"Config validation failed: {e}")
            return False
