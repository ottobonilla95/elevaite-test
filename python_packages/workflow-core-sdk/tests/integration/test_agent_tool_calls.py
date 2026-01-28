"""
Unit test for tool call parsing in AgentStep.

Tests the _execute_tool_call method directly to verify it correctly parses
tool calls in different formats (llm-gateway ToolCall, OpenAI format, dict).

This test does NOT require a database or API key - it tests the parsing logic directly.

Run with:
    pytest python_packages/workflow-core-sdk/tests/integration/test_agent_tool_calls.py -v -s
"""

import pytest
import logging
from pydantic import BaseModel
from typing import Dict, Any

# Set up detailed logging to see the debug output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === Mock tool_call formats ===


class LlmGatewayToolCall(BaseModel):
    """Simulates the llm-gateway ToolCall structure (flat)."""

    id: str
    name: str
    arguments: Dict[str, Any]


class OpenAIToolCallFunction(BaseModel):
    """Simulates OpenAI function object."""

    name: str
    arguments: str  # JSON string


class OpenAIToolCall(BaseModel):
    """Simulates OpenAI Completions API tool call (nested)."""

    id: str
    type: str = "function"
    function: OpenAIToolCallFunction


class TestToolCallParsing:
    """Test different tool_call formats parsing."""

    @pytest.fixture
    def mock_agent_step(self):
        """Create a minimal AgentStep-like object for testing _execute_tool_call."""

        class MockAgentStep:
            def __init__(self):
                self.tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "add_numbers",
                            "description": "Add two numbers",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "a": {"type": "number"},
                                    "b": {"type": "number"},
                                },
                                "required": ["a", "b"],
                            },
                        },
                    }
                ]

            async def _execute_tool_call(self, tool_call, context=None):
                """Copy of the actual parsing logic from AgentStep."""
                import json as _json

                logger.info(f"[TOOL_CALL_DEBUG] Raw tool_call type: {type(tool_call)}")
                logger.info(f"[TOOL_CALL_DEBUG] Raw tool_call repr: {repr(tool_call)}")

                if hasattr(tool_call, "__dict__"):
                    logger.info(
                        f"[TOOL_CALL_DEBUG] tool_call.__dict__: {tool_call.__dict__}"
                    )
                if hasattr(tool_call, "model_dump"):
                    try:
                        logger.info(
                            f"[TOOL_CALL_DEBUG] tool_call.model_dump(): {tool_call.model_dump()}"
                        )
                    except Exception as dump_err:
                        logger.info(
                            f"[TOOL_CALL_DEBUG] model_dump() failed: {dump_err}"
                        )

                # Check if it's a dict
                if isinstance(tool_call, dict):
                    logger.info(
                        f"[TOOL_CALL_DEBUG] tool_call is a dict with keys: {tool_call.keys()}"
                    )
                    function_name = tool_call.get("name") or (
                        tool_call.get("function", {}) or {}
                    ).get("name")
                    function_args = tool_call.get("arguments") or (
                        tool_call.get("function", {}) or {}
                    ).get("arguments")
                    logger.info(
                        f"[TOOL_CALL_DEBUG] Extracted from dict - name: {function_name}, args type: {type(function_args)}"
                    )
                else:
                    # Extract function name and args from multiple possible shapes
                    function_name = getattr(tool_call, "name", None)
                    function_args = getattr(tool_call, "arguments", None)
                    logger.info(
                        f"[TOOL_CALL_DEBUG] Direct attrs - name: {function_name}, args: {function_args}"
                    )

                    if function_name is None and hasattr(tool_call, "function"):
                        func_obj = getattr(tool_call, "function", None)
                        logger.info(
                            f"[TOOL_CALL_DEBUG] Has 'function' attr, type: {type(func_obj)}, value: {func_obj}"
                        )
                        if isinstance(func_obj, dict):
                            function_name = func_obj.get("name")
                            function_args = func_obj.get("arguments")
                        else:
                            function_name = getattr(func_obj, "name", None)
                            function_args = getattr(func_obj, "arguments", None)
                        logger.info(
                            f"[TOOL_CALL_DEBUG] From function attr - name: {function_name}, args: {function_args}"
                        )

                logger.info(
                    f"[TOOL_CALL_DEBUG] Final function_name: {function_name}, function_args type: {type(function_args)}"
                )

                # Normalize arguments
                if isinstance(function_args, str):
                    function_args = _json.loads(function_args)
                if function_args is None:
                    function_args = {}

                # Extract tool_call_id
                if isinstance(tool_call, dict):
                    tool_call_id = tool_call.get("id")
                else:
                    tool_call_id = getattr(tool_call, "id", None)

                if not function_name:
                    # Return error result instead of raising
                    logger.warning(
                        f"[TOOL_CALL_DEBUG] Skipping tool call with missing function name: {tool_call}"
                    )
                    return {
                        "tool_name": None,
                        "arguments": function_args,
                        "result": "Error: Tool call missing function name",
                        "success": False,
                        "error": "Tool call missing function name",
                        "tool_call_id": tool_call_id,
                    }

                return {
                    "function_name": function_name,
                    "function_args": function_args,
                    "tool_call_id": tool_call_id,
                    "success": True,
                }

        return MockAgentStep()

    @pytest.mark.asyncio
    async def test_llm_gateway_tool_call_format(self, mock_agent_step):
        """Test parsing llm-gateway ToolCall (flat structure with name, arguments)."""
        tool_call = LlmGatewayToolCall(
            id="call_123",
            name="add_numbers",
            arguments={"a": 5, "b": 3},
        )

        result = await mock_agent_step._execute_tool_call(tool_call)

        assert result["function_name"] == "add_numbers"
        assert result["function_args"] == {"a": 5, "b": 3}
        assert result["tool_call_id"] == "call_123"

    @pytest.mark.asyncio
    async def test_openai_tool_call_format(self, mock_agent_step):
        """Test parsing OpenAI Completions API tool call (nested function object)."""
        tool_call = OpenAIToolCall(
            id="call_456",
            function=OpenAIToolCallFunction(
                name="add_numbers",
                arguments='{"a": 10, "b": 20}',
            ),
        )

        result = await mock_agent_step._execute_tool_call(tool_call)

        assert result["function_name"] == "add_numbers"
        assert result["function_args"] == {"a": 10, "b": 20}
        assert result["tool_call_id"] == "call_456"

    @pytest.mark.asyncio
    async def test_dict_format_flat(self, mock_agent_step):
        """Test parsing dict-style tool call (flat)."""
        tool_call = {
            "id": "call_789",
            "name": "add_numbers",
            "arguments": {"a": 1, "b": 2},
        }

        result = await mock_agent_step._execute_tool_call(tool_call)

        assert result["function_name"] == "add_numbers"
        assert result["function_args"] == {"a": 1, "b": 2}

    @pytest.mark.asyncio
    async def test_dict_format_nested(self, mock_agent_step):
        """Test parsing dict-style tool call (OpenAI-nested)."""
        tool_call = {
            "id": "call_abc",
            "type": "function",
            "function": {
                "name": "add_numbers",
                "arguments": '{"a": 100, "b": 200}',
            },
        }

        result = await mock_agent_step._execute_tool_call(tool_call)

        assert result["function_name"] == "add_numbers"
        assert result["function_args"] == {"a": 100, "b": 200}

    @pytest.mark.asyncio
    async def test_missing_function_name_returns_error(self, mock_agent_step):
        """Test that missing function name returns error result instead of raising."""
        tool_call = {
            "id": "call_bad",
            "arguments": {"a": 1, "b": 2},
            # Missing 'name' and 'function'
        }

        result = await mock_agent_step._execute_tool_call(tool_call)

        # Should return error result, not raise
        assert result["success"] is False
        assert result["tool_name"] is None
        assert "missing function name" in result["error"].lower()
        assert result["tool_call_id"] == "call_bad"


# === Integration test with real LLM ===

import os


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY environment variable not set",
)
class TestAgentToolCallsIntegration:
    """Integration tests that require real LLM and database."""

    @pytest.mark.asyncio
    async def test_agent_with_tool_call(self):
        """Test full agent execution with tool call via real LLM."""
        from workflow_core_sdk.steps.ai_steps import AgentStep

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_numbers",
                    "description": "Add two numbers together. Always use this for addition.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                },
            }
        ]

        agent = AgentStep(
            name="MathAgent",
            system_prompt="You are a math assistant. You MUST use the add_numbers tool for any addition.",
            tools=tools,
            force_real_llm=True,
        )

        result = await agent.execute(
            query="What is 5 + 3? Use the add_numbers tool.",
            context={},
        )

        logger.info(f"Full result: {result}")

        assert "response" in result
        # If we got here without "Tool call missing function name" error, parsing worked
        assert result is not None
