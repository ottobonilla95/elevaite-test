"""
Unit tests for code execution step.

These tests don't require the Code Execution Service and test the step logic.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from workflow_core_sdk.execution_context import ExecutionContext


def create_mock_execution_context(
    execution_id: str = "exec-123", workflow_id: str = "wf-123"
) -> ExecutionContext:
    """Create a mock execution context for testing."""
    workflow_config = {
        "workflow_id": workflow_id,
        "name": "Test Workflow",
        "steps": [],
    }
    return ExecutionContext(
        workflow_config=workflow_config,
        execution_id=execution_id,
    )


def create_mock_http_client(
    mock_http_client, response_data: dict, raise_for_status=None
):
    """Helper to set up mock HTTP client with response."""
    mock_response = MagicMock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status = raise_for_status or MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.post = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)
    mock_http_client.return_value = mock_client_instance

    return mock_client_instance, mock_response


class TestCodeExecutionStep:
    """Tests for the code_execution_step function."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_successful_code_execution(self, mock_http_client):
        """Test that code execution returns success on valid code."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "stdout": "Hello World\n",
            "stderr": "",
            "exit_code": 0,
            "execution_time_ms": 50,
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        # Import step function
        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {
                "code": "print('Hello World')",
                "timeout": 30,
                "memory_mb": 256,
            },
        }
        input_data = {"key": "value"}
        ctx = create_mock_execution_context()

        result = await code_execution_step(step_config, input_data, ctx)

        assert result["success"] is True
        assert result["stdout"] == "Hello World\n"
        assert result["exit_code"] == 0
        mock_client_instance.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_empty_code_returns_error(self):
        """Test that empty code returns an error without calling the service."""
        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {
                "code": "",
            },
        }
        input_data = {}
        ctx = create_mock_execution_context()

        result = await code_execution_step(step_config, input_data, ctx)

        assert result["success"] is False
        assert "No code provided" in result["error"]

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_code_with_input_data(self, mock_http_client):
        """Test that input_data is passed to the service."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "stdout": "42",
            "stderr": "",
            "exit_code": 0,
            "execution_time_ms": 10,
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {
                "code": "print(input_data['value'])",
            },
        }
        input_data = {"value": 42}
        ctx = create_mock_execution_context()

        await code_execution_step(step_config, input_data, ctx)

        # Verify input_data was passed to the service
        call_args = mock_client_instance.post.call_args
        request_json = call_args[1]["json"]
        assert request_json["input_data"] == {"value": 42}

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_timeout_configuration(self, mock_http_client):
        """Test that custom timeout is passed to the service."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "stdout": "",
            "stderr": "",
            "exit_code": 0,
            "execution_time_ms": 100,
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {
                "code": "import time; time.sleep(1)",
                "timeout": 60,
                "memory_mb": 512,
            },
        }

        await code_execution_step(step_config, {}, create_mock_execution_context())

        call_args = mock_client_instance.post.call_args
        request_json = call_args[1]["json"]
        assert request_json["timeout_seconds"] == 60
        assert request_json["memory_mb"] == 512

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_http_timeout_error(self, mock_http_client):
        """Test handling of HTTP timeout."""
        import httpx

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "while True: pass", "timeout": 5},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert "timed out" in result["error"]

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_http_status_error(self, mock_http_client):
        """Test handling of HTTP error status codes."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )
        )

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "print('test')"},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert "service error" in result["error"]

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_failed_execution_returns_error(self, mock_http_client):
        """Test that failed code execution returns error info."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "stdout": "",
            "stderr": "Traceback...",
            "exit_code": 1,
            "execution_time_ms": 5,
            "error": "SyntaxError: invalid syntax",
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "print("},  # Invalid syntax
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert result["exit_code"] == 1
        assert "SyntaxError" in result["error"]

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_default_config_values(self, mock_http_client):
        """Test that default timeout and memory values are used."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "stdout": "",
            "stderr": "",
            "exit_code": 0,
            "execution_time_ms": 10,
        }
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "x = 1"},
            # No timeout or memory_mb specified
        }

        await code_execution_step(step_config, {}, create_mock_execution_context())

        call_args = mock_client_instance.post.call_args
        request_json = call_args[1]["json"]
        assert request_json["timeout_seconds"] == 30  # Default
        assert request_json["memory_mb"] == 256  # Default


class TestCodeExecutionStepEdgeCases:
    """Tests for edge cases in code_execution_step."""

    @pytest.mark.asyncio
    async def test_missing_config_key(self):
        """Test handling when step_config has no 'config' key."""
        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            # No 'config' key at all
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert "No code provided" in result["error"]

    @pytest.mark.asyncio
    async def test_missing_step_id_uses_default(self):
        """Test that missing step_id defaults to 'code_execution'."""
        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            # No step_id
            "config": {"code": ""},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        # Should still work (returns error for empty code, but doesn't crash)
        assert result["success"] is False
        assert "No code provided" in result["error"]

    @pytest.mark.asyncio
    async def test_none_code_value(self):
        """Test handling when code is None instead of empty string."""
        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": None},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert "No code provided" in result["error"]

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_whitespace_only_code_is_sent(self, mock_http_client):
        """Test that whitespace-only code is sent to service (service validates)."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": True,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 5,
            },
        )

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "   \n\t  "},  # Whitespace only
        }

        await code_execution_step(step_config, {}, create_mock_execution_context())

        # Whitespace code should be sent to service (it's not empty string)
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["code"] == "   \n\t  "


class TestCodeExecutionStepExceptionHandling:
    """Tests for exception handling in code_execution_step."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_generic_exception_handling(self, mock_http_client):
        """Test handling of generic exceptions (e.g., connection errors)."""
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "print('test')"},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert "Failed to execute code" in result["error"]
        assert "Connection refused" in result["error"]
        assert result["exit_code"] == -1

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_connection_error(self, mock_http_client):
        """Test handling when service is unreachable."""
        import httpx

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(
            side_effect=httpx.ConnectError("Failed to connect")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "print('test')"},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert "Failed to execute code" in result["error"]


class TestCodeExecutionStepEnvironment:
    """Tests for environment variable handling."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    @patch.dict(
        "os.environ", {"CODE_EXECUTION_SERVICE_URL": "http://custom-service:9000"}
    )
    async def test_custom_service_url_from_env(self, mock_http_client):
        """Test that CODE_EXECUTION_SERVICE_URL env var is used."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": True,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 5,
            },
        )

        # Need to reimport to pick up the env var change
        import importlib
        import workflow_core_sdk.steps.code_execution_step as step_module

        importlib.reload(step_module)

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "x = 1"},
        }

        await step_module.code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        call_args = mock_client.post.call_args
        called_url = call_args[0][0]
        assert called_url == "http://custom-service:9000/execute"


class TestCodeExecutionStepResponseHandling:
    """Tests for response edge cases."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_missing_response_fields_use_defaults(self, mock_http_client):
        """Test that missing response fields use sensible defaults."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {"success": True},  # Minimal response - missing stdout, stderr, etc.
        )

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "x = 1"},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is True
        assert result["stdout"] == ""  # Default
        assert result["stderr"] == ""  # Default
        assert result["exit_code"] == -1  # Default
        assert result["execution_time_ms"] == 0  # Default
        assert result["error"] is None  # Default

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_executed_at_field_is_present(self, mock_http_client):
        """Test that executed_at timestamp is added to response."""
        from datetime import datetime

        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": True,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 5,
            },
        )

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "x = 1"},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert "executed_at" in result
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(result["executed_at"])

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_error_field_preserved_from_service(self, mock_http_client):
        """Test that error field from service is preserved."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": False,
                "stdout": "",
                "stderr": "",
                "exit_code": 1,
                "execution_time_ms": 10,
                "error": "Blocked import: os",
            },
        )

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "import os"},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert result["error"] == "Blocked import: os"


class TestCodeExecutionStepHttpClient:
    """Tests for HTTP client configuration."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_http_timeout_includes_buffer(self, mock_http_client):
        """Test that HTTP timeout = step timeout + 10s buffer."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": True,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 5,
            },
        )

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "x = 1", "timeout": 45},
        }

        await code_execution_step(step_config, {}, create_mock_execution_context())

        # Verify AsyncClient was called with timeout = 45 + 10 = 55
        mock_http_client.assert_called_once_with(timeout=55)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_correct_url_construction(self, mock_http_client):
        """Test that the correct URL is constructed."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": True,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 5,
            },
        )

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "x = 1"},
        }

        await code_execution_step(step_config, {}, create_mock_execution_context())

        call_args = mock_client.post.call_args
        called_url = call_args[0][0]
        assert called_url.endswith("/execute")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_language_always_python(self, mock_http_client):
        """Test that language is always set to 'python'."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": True,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 5,
            },
        )

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "x = 1"},
        }

        await code_execution_step(step_config, {}, create_mock_execution_context())

        call_args = mock_client.post.call_args
        request_json = call_args[1]["json"]
        assert request_json["language"] == "python"


class TestCodeExecutionStepStreaming:
    """Tests for streaming event emission."""

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.code_execution_step.stream_manager")
    @patch("httpx.AsyncClient")
    async def test_streaming_event_emitted_on_execution(
        self, mock_http_client, mock_stream_manager
    ):
        """Test that streaming events are emitted during execution."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": True,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 5,
            },
        )
        mock_stream_manager.emit_execution_event = AsyncMock()
        mock_stream_manager.emit_workflow_event = AsyncMock()

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "x = 1"},
        }

        await code_execution_step(step_config, {}, create_mock_execution_context())

        # Verify streaming events were emitted
        mock_stream_manager.emit_execution_event.assert_called_once()
        mock_stream_manager.emit_workflow_event.assert_called_once()

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.code_execution_step.stream_manager")
    @patch("httpx.AsyncClient")
    async def test_streaming_failure_does_not_break_execution(
        self, mock_http_client, mock_stream_manager
    ):
        """Test that streaming failures don't break code execution."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": True,
                "stdout": "output",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 5,
            },
        )
        # Make streaming fail
        mock_stream_manager.emit_execution_event = AsyncMock(
            side_effect=Exception("Streaming error")
        )
        mock_stream_manager.emit_workflow_event = AsyncMock(
            side_effect=Exception("Streaming error")
        )

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "print('test')"},
        }

        # Should not raise, execution should complete successfully
        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is True
        assert result["stdout"] == "output"

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.code_execution_step.stream_manager")
    @patch("httpx.AsyncClient")
    async def test_streaming_event_contains_correct_data(
        self, mock_http_client, mock_stream_manager
    ):
        """Test that streaming event contains correct step data."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": True,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 5,
            },
        )
        mock_stream_manager.emit_execution_event = AsyncMock()
        mock_stream_manager.emit_workflow_event = AsyncMock()

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "my-code-step",
            "config": {"code": "x = 1"},
        }
        ctx = create_mock_execution_context(
            execution_id="exec-456", workflow_id="wf-789"
        )

        await code_execution_step(step_config, {}, ctx)

        # Check the event that was emitted (StreamEvent is a dataclass)
        call_args = mock_stream_manager.emit_execution_event.call_args
        event = call_args[0][0]

        # StreamEvent has execution_id, workflow_id as attributes
        # step_id, step_status, step_type are in the data dict
        assert event.execution_id == "exec-456"
        assert event.data["step_id"] == "my-code-step"
        assert event.data["step_status"] == "running"
        assert event.data["step_type"] == "code_execution"

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.code_execution_step.stream_manager")
    @patch("httpx.AsyncClient")
    async def test_no_workflow_event_when_workflow_id_none(
        self, mock_http_client, mock_stream_manager
    ):
        """Test that workflow event is not emitted when workflow_id is None."""
        mock_client, _ = create_mock_http_client(
            mock_http_client,
            {
                "success": True,
                "stdout": "",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 5,
            },
        )
        mock_stream_manager.emit_execution_event = AsyncMock()
        mock_stream_manager.emit_workflow_event = AsyncMock()

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "x = 1"},
        }

        # Create context - workflow_id will be auto-generated, but we can check the logic
        # by mocking the context's workflow_id to be falsy
        ctx = create_mock_execution_context()
        # Manually set workflow_id to None to test the conditional
        ctx.workflow_id = None

        await code_execution_step(step_config, {}, ctx)

        # Execution event should still be emitted
        mock_stream_manager.emit_execution_event.assert_called_once()
        # Workflow event should NOT be emitted when workflow_id is None
        mock_stream_manager.emit_workflow_event.assert_not_called()

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.code_execution_step.stream_manager")
    @patch("httpx.AsyncClient")
    async def test_failed_event_emitted_on_timeout(
        self, mock_http_client, mock_stream_manager
    ):
        """Test that 'failed' streaming event is emitted on timeout."""
        import httpx

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        mock_stream_manager.emit_execution_event = AsyncMock()
        mock_stream_manager.emit_workflow_event = AsyncMock()

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "timeout-step",
            "config": {"code": "while True: pass", "timeout": 5},
        }

        await code_execution_step(step_config, {}, create_mock_execution_context())

        # Should have emitted 2 events: "running" then "failed"
        assert mock_stream_manager.emit_execution_event.call_count == 2

        # Check the second (failed) event
        failed_event = mock_stream_manager.emit_execution_event.call_args_list[1][0][0]
        assert failed_event.data["step_status"] == "failed"
        assert "timed out" in failed_event.data["output_data"]["error"]

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.code_execution_step.stream_manager")
    @patch("httpx.AsyncClient")
    async def test_failed_event_emitted_on_http_error(
        self, mock_http_client, mock_stream_manager
    ):
        """Test that 'failed' streaming event is emitted on HTTP error."""
        import httpx

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )
        )

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        mock_stream_manager.emit_execution_event = AsyncMock()
        mock_stream_manager.emit_workflow_event = AsyncMock()

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "http-error-step",
            "config": {"code": "print('test')"},
        }

        await code_execution_step(step_config, {}, create_mock_execution_context())

        # Should have emitted 2 events: "running" then "failed"
        assert mock_stream_manager.emit_execution_event.call_count == 2

        # Check the second (failed) event
        failed_event = mock_stream_manager.emit_execution_event.call_args_list[1][0][0]
        assert failed_event.data["step_status"] == "failed"
        assert "service error" in failed_event.data["output_data"]["error"]

    @pytest.mark.asyncio
    @patch("workflow_core_sdk.steps.code_execution_step.stream_manager")
    @patch("httpx.AsyncClient")
    async def test_failed_event_emitted_on_generic_exception(
        self, mock_http_client, mock_stream_manager
    ):
        """Test that 'failed' streaming event is emitted on generic exception."""
        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        mock_stream_manager.emit_execution_event = AsyncMock()
        mock_stream_manager.emit_workflow_event = AsyncMock()

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "exception-step",
            "config": {"code": "print('test')"},
        }

        await code_execution_step(step_config, {}, create_mock_execution_context())

        # Should have emitted 2 events: "running" then "failed"
        assert mock_stream_manager.emit_execution_event.call_count == 2

        # Check the second (failed) event
        failed_event = mock_stream_manager.emit_execution_event.call_args_list[1][0][0]
        assert failed_event.data["step_status"] == "failed"
        assert "Failed to execute code" in failed_event.data["output_data"]["error"]


class TestCodeExecutionStepErrorResponses:
    """Tests for error response consistency."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_timeout_error_includes_executed_at(self, mock_http_client):
        """Test that timeout error response includes executed_at."""
        import httpx
        from datetime import datetime

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "while True: pass", "timeout": 5},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert "executed_at" in result
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(result["executed_at"])

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_http_error_includes_executed_at(self, mock_http_client):
        """Test that HTTP error response includes executed_at."""
        import httpx
        from datetime import datetime

        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_response.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )
        )

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "print('test')"},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert "executed_at" in result
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(result["executed_at"])

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_generic_exception_includes_executed_at(self, mock_http_client):
        """Test that generic exception response includes executed_at."""
        from datetime import datetime

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(
            side_effect=Exception("Connection refused")
        )
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        from workflow_core_sdk.steps.code_execution_step import code_execution_step

        step_config = {
            "step_id": "code-step-1",
            "config": {"code": "print('test')"},
        }

        result = await code_execution_step(
            step_config, {}, create_mock_execution_context()
        )

        assert result["success"] is False
        assert "executed_at" in result
        # Verify it's a valid ISO format timestamp
        datetime.fromisoformat(result["executed_at"])
