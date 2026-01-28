"""Unit tests for the code executor."""

import pytest

from code_execution_service.core.config import settings
from code_execution_service.schemas.requests import ExecuteRequest
from code_execution_service.services.executor import CodeExecutor


class TestCodeExecutor:
    """Tests for CodeExecutor class."""

    @pytest.mark.asyncio
    async def test_unsupported_language_rejected(self, executor: CodeExecutor):
        """Test that unsupported languages are rejected."""
        request = ExecuteRequest(
            language="javascript",
            code="console.log('hello')",
        )
        response = await executor.execute(request)

        assert not response.success
        assert response.error is not None
        assert "Unsupported language" in response.error
        assert "javascript" in response.error

    @pytest.mark.asyncio
    async def test_python_language_accepted(self, executor: CodeExecutor):
        """Test that Python language is accepted."""
        request = ExecuteRequest(
            language="python",
            code="print('hello')",
        )
        response = await executor.execute(request)

        # Should not fail due to language
        assert response.error is None or "Unsupported language" not in response.error

    @pytest.mark.asyncio
    async def test_python_case_insensitive(self, executor: CodeExecutor):
        """Test that language check is case-insensitive."""
        request = ExecuteRequest(
            language="PYTHON",
            code="print('hello')",
        )
        response = await executor.execute(request)

        assert response.error is None or "Unsupported language" not in response.error

    @pytest.mark.asyncio
    async def test_code_length_limit_enforced(self, executor: CodeExecutor):
        """Test that code exceeding max length is rejected."""
        # Create code that exceeds the limit
        long_code = "x = 1\n" * (settings.max_code_length // 5)

        request = ExecuteRequest(
            language="python",
            code=long_code,
        )
        response = await executor.execute(request)

        assert not response.success
        assert response.error is not None
        assert "maximum length" in response.error

    @pytest.mark.asyncio
    async def test_timeout_at_max_boundary(self, executor: CodeExecutor):
        """Test that timeout at max boundary is accepted."""
        request = ExecuteRequest(
            language="python",
            code="print('hello')",
            timeout_seconds=60,  # At max
        )
        response = await executor.execute(request)

        # Should process without error about timeout
        assert response.error is None or "timeout" not in response.error.lower()

    @pytest.mark.asyncio
    async def test_timeout_at_min_boundary(self, executor: CodeExecutor):
        """Test that timeout at min boundary is accepted."""
        request = ExecuteRequest(
            language="python",
            code="print('hello')",
            timeout_seconds=1,  # At min
        )
        response = await executor.execute(request)

        # Should process without error about timeout
        assert response.error is None or "timeout" not in response.error.lower()

    @pytest.mark.asyncio
    async def test_memory_at_max_boundary(self, executor: CodeExecutor):
        """Test that memory at max boundary is accepted."""
        request = ExecuteRequest(
            language="python",
            code="print('hello')",
            memory_mb=512,  # At max
        )
        response = await executor.execute(request)

        # Should process without error about memory
        assert response.error is None or "memory" not in response.error.lower()

    @pytest.mark.asyncio
    async def test_memory_at_min_boundary(self, executor: CodeExecutor):
        """Test that memory at min boundary is accepted."""
        request = ExecuteRequest(
            language="python",
            code="print('hello')",
            memory_mb=64,  # At min
        )
        response = await executor.execute(request)

        # Should process without error about memory
        assert response.error is None or "memory" not in response.error.lower()

    @pytest.mark.asyncio
    async def test_validation_errors_returned(self, executor: CodeExecutor):
        """Test that validation errors are properly returned."""
        request = ExecuteRequest(
            language="python",
            code="import os\nos.system('ls')",
        )
        response = await executor.execute(request)

        assert not response.success
        assert response.validation_errors is not None
        assert len(response.validation_errors) > 0
        assert any("os" in error for error in response.validation_errors)

    @pytest.mark.asyncio
    async def test_multiple_validation_errors(self, executor: CodeExecutor):
        """Test that multiple validation errors are collected."""
        request = ExecuteRequest(
            language="python",
            code="import os\nimport subprocess\neval('1')",
        )
        response = await executor.execute(request)

        assert not response.success
        assert response.validation_errors is not None
        assert len(response.validation_errors) >= 3
