import logging
import time
import json
from typing import Dict, Any, Optional, List

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
    ) -> TextGenerationResponse:
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

                # Get token counts (if available)
                tokens_in = getattr(response, "input_tokens", len(prompt.split()))
                tokens_out = getattr(
                    response,
                    "output_tokens",
                    len(text_content.split()) if text_content else 0,
                )

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

    def validate_config(self, config: Dict[str, Any]) -> bool:
        try:
            assert isinstance(config, dict), "Config must be a dictionary"
            assert "model" in config, "Model name is required in config"
            assert isinstance(config["model"], str), "Model name must be a string"
            return True
        except AssertionError as e:
            logging.error(f"Config validation failed: {e}")
            return False
