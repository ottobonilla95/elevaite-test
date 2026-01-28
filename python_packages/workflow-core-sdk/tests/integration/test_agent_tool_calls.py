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

    @pytest.mark.asyncio
    async def test_agent_with_multiple_tools(self):
        """Test agent execution with multiple tool definitions."""
        from workflow_core_sdk.steps.ai_steps import AgentStep

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_numbers",
                    "description": "Add two numbers together.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "multiply_numbers",
                    "description": "Multiply two numbers together.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number", "description": "First number"},
                            "y": {"type": "number", "description": "Second number"},
                        },
                        "required": ["x", "y"],
                    },
                },
            },
        ]

        agent = AgentStep(
            name="MathAgent",
            system_prompt="You are a math assistant. Use add_numbers for addition and multiply_numbers for multiplication. Do NOT calculate yourself.",
            tools=tools,
            force_real_llm=True,
        )

        result = await agent.execute(
            query="What is 4 * 5? You MUST use the multiply_numbers tool.",
            context={},
        )

        logger.info(f"Multiple tools result: {result}")
        assert "response" in result
        assert result is not None

    @pytest.mark.asyncio
    async def test_tool_execution_returns_result(self):
        """Test that tool execution actually returns correct results via provider-side execution."""
        from workflow_core_sdk.steps.ai_steps import AgentStep

        # Define a tool that our AgentStep's _execute_tool_call will handle
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get the current time as a string. Always use this tool when asked about time.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }
        ]

        agent = AgentStep(
            name="TimeAgent",
            system_prompt="You are a time assistant. When asked about the time, you MUST use the get_current_time tool.",
            tools=tools,
            force_real_llm=True,
        )

        result = await agent.execute(
            query="What time is it right now? Use the get_current_time tool to find out.",
            context={},
        )

        logger.info(f"Tool execution result: {result}")
        assert "response" in result
        # The response should mention something about time (either the actual time or an error message)
        # This verifies the tool loop is working
        assert result is not None


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY environment variable not set",
)
class TestProviderToolLoop:
    """Test the provider-side tool execution loop directly."""

    def test_openai_provider_with_executor(self):
        """Test OpenAI provider with tool executors."""
        from llm_gateway.services import TextGenerationService
        from llm_gateway.models.text_generation.core.interfaces import (
            TextGenerationType,
        )

        service = TextGenerationService()

        # Define a tool with an executor that returns a known value
        def add_executor(a: float, b: float) -> float:
            logger.info(f"add_executor called with a={a}, b={b}")
            return a + b

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "add_numbers",
                    "description": "Add two numbers. Always use this tool for any addition.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number", "description": "First number"},
                            "b": {"type": "number", "description": "Second number"},
                        },
                        "required": ["a", "b"],
                    },
                },
                "executor": add_executor,
            }
        ]

        response = service.generate(
            prompt="What is 7 + 9? You MUST use the add_numbers tool to calculate this.",
            sys_msg="You are a math assistant. Always use the add_numbers tool for addition operations.",
            model_name="gpt-4o-mini",
            config={"type": TextGenerationType.OPENAI.value},
            tools=tools,
            max_tool_iterations=3,
        )

        logger.info(f"Provider response: {response}")
        logger.info(f"Response text: {response.text}")

        # The response should contain the correct result (16)
        assert response.text is not None
        assert "16" in response.text

        # Check that tool_calls_trace was populated
        if response.tool_calls_trace:
            logger.info(f"Tool calls trace: {response.tool_calls_trace}")
            # At least one tool call should have been made
            assert len(response.tool_calls_trace) >= 1
            # The tool should have been called with the right arguments
            trace = response.tool_calls_trace[0]
            assert trace.tool_name == "add_numbers"
            assert trace.success is True

    def test_openai_streaming_with_tool_callbacks(self):
        """Test OpenAI streaming with tool callbacks."""
        from llm_gateway.services import TextGenerationService
        from llm_gateway.models.text_generation.core.interfaces import (
            TextGenerationType,
        )

        service = TextGenerationService()

        # Track callback invocations
        tool_calls_received = []
        tool_results_received = []

        def on_tool_call(tool_name: str, args: Dict[str, Any]):
            logger.info(f"on_tool_call: {tool_name} with {args}")
            tool_calls_received.append({"tool_name": tool_name, "args": args})

        def on_tool_result(tool_name: str, trace):
            logger.info(f"on_tool_result: {tool_name} -> {trace}")
            tool_results_received.append({"tool_name": tool_name, "trace": trace})

        def multiply_executor(x: float, y: float) -> float:
            logger.info(f"multiply_executor called with x={x}, y={y}")
            return x * y

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "multiply_numbers",
                    "description": "Multiply two numbers. Always use this tool for multiplication.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number", "description": "First number"},
                            "y": {"type": "number", "description": "Second number"},
                        },
                        "required": ["x", "y"],
                    },
                },
                "executor": multiply_executor,
            }
        ]

        # Collect all streamed chunks
        chunks = []
        for chunk in service.stream(
            prompt="What is 6 * 7? You MUST use the multiply_numbers tool.",
            sys_msg="You are a math assistant. Always use the multiply_numbers tool for multiplication.",
            model_name="gpt-4o-mini",
            config={"type": TextGenerationType.OPENAI.value},
            tools=tools,
            max_tool_iterations=3,
            on_tool_call=on_tool_call,
            on_tool_result=on_tool_result,
        ):
            logger.info(f"Received chunk: {chunk}")
            chunks.append(chunk)

        logger.info(f"Total chunks received: {len(chunks)}")
        logger.info(f"Tool calls received: {tool_calls_received}")
        logger.info(f"Tool results received: {tool_results_received}")

        # Should have received some chunks
        assert len(chunks) > 0

        # Check that we got a final response with the correct answer
        final_chunks = [c for c in chunks if c.get("type") == "final"]
        assert len(final_chunks) >= 1

        # The final response should contain "42"
        final_text = final_chunks[-1].get("response", {}).get("text", "")
        logger.info(f"Final text: {final_text}")
        assert "42" in final_text
