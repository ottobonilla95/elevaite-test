"""
Unit tests for tool_execution_step

Tests tool execution with local tools, parameter mapping, and error handling.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import uuid

from workflow_core_sdk.steps.tool_steps import tool_execution_step
from workflow_core_sdk.execution_context import ExecutionContext


@pytest.fixture
def execution_context():
    """Create a mock execution context"""
    context = MagicMock(spec=ExecutionContext)
    context.execution_id = "test-execution-id"
    context.workflow_id = "test-workflow-id"
    context.step_io_data = {}
    return context


@pytest.fixture
def step_config():
    """Basic step configuration"""
    return {
        "step_id": "tool-step-1",
        "step_type": "tool_execution",
        "config": {},
    }


# Sample tool functions for testing
def add_numbers(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


def multiply_numbers(x: float, y: float) -> float:
    """Multiply two numbers"""
    return x * y


def greet_user(name: str, greeting: str = "Hello") -> str:
    """Greet a user"""
    return f"{greeting}, {name}!"


def failing_tool():
    """A tool that always fails"""
    raise ValueError("This tool always fails")


class TestLocalToolExecution:
    """Tests for executing local tools"""

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.get_all_tools")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_local_tool_by_name(
        self, mock_stream, mock_get_tools, step_config, execution_context
    ):
        """Test executing a local tool by name"""
        mock_get_tools.return_value = {"add_numbers": add_numbers}
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        step_config["config"] = {
            "tool_name": "add_numbers",
            "static_params": {"a": 5, "b": 3},
        }

        result = await tool_execution_step(step_config, {}, execution_context)

        assert result["success"] is True
        assert result["result"] == 8
        assert result["tool"]["name"] == "add_numbers"
        assert result["params"]["a"] == 5
        assert result["params"]["b"] == 3

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.get_all_tools")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_tool_with_param_mapping(
        self, mock_stream, mock_get_tools, step_config, execution_context
    ):
        """Test executing a tool with parameter mapping from input_data"""
        mock_get_tools.return_value = {"add_numbers": add_numbers}
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        step_config["config"] = {
            "tool_name": "add_numbers",
            "param_mapping": {"a": "first_number", "b": "second_number"},
        }
        input_data = {"first_number": 10, "second_number": 20}

        result = await tool_execution_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"] == 30
        assert result["params"]["a"] == 10
        assert result["params"]["b"] == 20

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.get_all_tools")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_tool_with_nested_param_mapping(
        self, mock_stream, mock_get_tools, step_config, execution_context
    ):
        """Test executing a tool with nested parameter mapping (dot notation)"""
        mock_get_tools.return_value = {"greet_user": greet_user}
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        step_config["config"] = {
            "tool_name": "greet_user",
            "param_mapping": {"name": "user.name", "greeting": "user.greeting"},
        }
        input_data = {"user": {"name": "Alice", "greeting": "Hi"}}

        result = await tool_execution_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"] == "Hi, Alice!"

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.get_all_tools")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_tool_with_static_and_mapped_params(
        self, mock_stream, mock_get_tools, step_config, execution_context
    ):
        """Test executing a tool with both static params and param mapping"""
        mock_get_tools.return_value = {"greet_user": greet_user}
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        step_config["config"] = {
            "tool_name": "greet_user",
            "static_params": {"greeting": "Welcome"},
            "param_mapping": {"name": "username"},
        }
        input_data = {"username": "Bob"}

        result = await tool_execution_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"] == "Welcome, Bob!"

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.get_all_tools")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_tool_with_type_coercion(
        self, mock_stream, mock_get_tools, step_config, execution_context
    ):
        """Test executing a tool with automatic type coercion"""
        mock_get_tools.return_value = {"add_numbers": add_numbers}
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        step_config["config"] = {
            "tool_name": "add_numbers",
            "static_params": {
                "a": "5",
                "b": "3",
            },  # Strings that should be coerced to int
        }

        result = await tool_execution_step(step_config, {}, execution_context)

        assert result["success"] is True
        assert result["result"] == 8
        assert isinstance(result["params"]["a"], int)
        assert isinstance(result["params"]["b"], int)

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.get_all_tools")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_tool_with_json_response_parsing(
        self, mock_stream, mock_get_tools, step_config, execution_context
    ):
        """Test parameter extraction from JSON response strings"""
        mock_get_tools.return_value = {"greet_user": greet_user}
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        step_config["config"] = {
            "tool_name": "greet_user",
            "param_mapping": {"name": "response.user_name"},
        }
        # Simulate agent response with JSON string
        input_data = {"response": '{"user_name": "Charlie", "age": 30}'}

        result = await tool_execution_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert "Charlie" in result["result"]


class TestToolNotFound:
    """Tests for tool not found scenarios"""

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.get_all_tools")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_tool_not_found_by_name(
        self, mock_stream, mock_get_tools, step_config, execution_context
    ):
        """Test error when tool is not found by name"""
        mock_get_tools.return_value = {}
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        step_config["config"] = {"tool_name": "nonexistent_tool"}

        with pytest.raises(Exception, match="Tool not found or unsupported"):
            await tool_execution_step(step_config, {}, execution_context)

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.Session")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_tool_not_found_by_id(
        self, mock_stream, mock_session_class, step_config, execution_context
    ):
        """Test error when tool is not found by ID in database"""
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        # Mock database session to return None
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_class.return_value = mock_session

        tool_id = str(uuid.uuid4())
        step_config["config"] = {"tool_id": tool_id}

        result = await tool_execution_step(step_config, {}, execution_context)

        assert result["success"] is False
        assert "Tool not found" in result["error"]
        assert result["resolved"]["tool_id"] == tool_id


class TestToolExecutionErrors:
    """Tests for tool execution error handling"""

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.get_all_tools")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_tool_parameter_mismatch(
        self, mock_stream, mock_get_tools, step_config, execution_context
    ):
        """Test error when tool is called with wrong parameters"""
        mock_get_tools.return_value = {"add_numbers": add_numbers}
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        step_config["config"] = {
            "tool_name": "add_numbers",
            "static_params": {"a": 5},  # Missing required parameter 'b'
        }

        result = await tool_execution_step(step_config, {}, execution_context)

        assert result["success"] is False
        assert "Parameter mismatch" in result["error"]

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.get_all_tools")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_tool_execution_failure(
        self, mock_stream, mock_get_tools, step_config, execution_context
    ):
        """Test error when tool execution raises an exception"""
        mock_get_tools.return_value = {"failing_tool": failing_tool}
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        step_config["config"] = {"tool_name": "failing_tool"}

        result = await tool_execution_step(step_config, {}, execution_context)

        assert result["success"] is False
        assert "raised an error" in result["error"]
        assert "This tool always fails" in result["error"]


class TestDatabaseToolExecution:
    """Tests for executing tools loaded from database"""

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.importlib.import_module")
    @patch("workflow_core_sdk.steps.tool_steps.Session")
    @patch("workflow_core_sdk.steps.tool_steps.get_all_tools")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_execute_db_tool_with_module_path(
        self,
        mock_stream,
        mock_get_tools,
        mock_session_class,
        mock_import,
        step_config,
        execution_context,
    ):
        """Test executing a tool loaded from database with module_path"""
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()
        mock_get_tools.return_value = {}

        # Mock the imported module and function
        mock_module = MagicMock()
        mock_module.add_numbers = add_numbers
        mock_import.return_value = mock_module

        # Mock database tool record
        mock_tool = MagicMock()
        mock_tool.id = str(uuid.uuid4())
        mock_tool.name = "add_numbers"
        mock_tool.module_path = "some.module.path"
        mock_tool.function_name = "add_numbers"

        # Mock database session
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_tool
        mock_session.exec.return_value = mock_result
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_class.return_value = mock_session

        step_config["config"] = {
            "tool_id": mock_tool.id,
            "static_params": {"a": 7, "b": 3},
        }

        result = await tool_execution_step(step_config, {}, execution_context)

        assert result["success"] is True
        assert result["result"] == 10
        mock_import.assert_called_once_with("some.module.path")

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.tool_steps.Session")
    @patch("workflow_core_sdk.steps.tool_steps.stream_manager")
    async def test_db_tool_import_failure(
        self, mock_stream, mock_session_class, step_config, execution_context
    ):
        """Test error when DB tool module import fails"""
        mock_stream.emit_execution_event = AsyncMock()
        mock_stream.emit_workflow_event = AsyncMock()

        # Mock database tool record with invalid module
        mock_tool = MagicMock()
        mock_tool.id = str(uuid.uuid4())
        mock_tool.name = "broken_tool"
        mock_tool.module_path = "nonexistent.module"
        mock_tool.function_name = "some_function"

        # Mock database session
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.first.return_value = mock_tool
        mock_session.exec.return_value = mock_result
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        mock_session_class.return_value = mock_session

        step_config["config"] = {"tool_id": mock_tool.id}

        result = await tool_execution_step(step_config, {}, execution_context)

        assert result["success"] is False
        assert "Failed to import" in result["error"]
