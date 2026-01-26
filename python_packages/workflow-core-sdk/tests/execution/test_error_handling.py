"""
Unit tests for error handling and retry mechanisms

Tests error handling, retry logic, circuit breakers, and error classification.
"""

import pytest
from unittest.mock import AsyncMock
import time

from workflow_core_sdk.execution.error_handling import (
    ErrorHandler,
    ErrorSeverity,
    RetryStrategy,
    RetryConfig,
    WorkflowError,
    StepExecutionError,
    ValidationError,
    ConfigurationError,
    RetryableError,
    NonRetryableError,
    CircuitBreakerError,
)


@pytest.fixture
def error_handler():
    """Create a fresh error handler for each test"""
    return ErrorHandler()


@pytest.fixture
def retry_config():
    """Create a default retry configuration"""
    return RetryConfig(
        max_attempts=3,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=0.1,  # Short delay for tests
        max_delay=1.0,
        backoff_multiplier=2.0,
        jitter=False,  # Disable jitter for predictable tests
    )


class TestRetryStrategies:
    """Tests for different retry strategies"""

    @pytest.mark.asyncio
    async def test_successful_execution_no_retry(self, error_handler, retry_config):
        """Test successful execution requires no retry"""
        mock_func = AsyncMock(return_value="success")

        result = await error_handler.execute_with_retry(mock_func, retry_config=retry_config)

        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_retryable_error(self, error_handler, retry_config):
        """Test retry on retryable error"""
        mock_func = AsyncMock(side_effect=[RetryableError("Temporary failure"), "success"])

        result = await error_handler.execute_with_retry(mock_func, retry_config=retry_config)

        assert result == "success"
        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_non_retryable_error(self, error_handler, retry_config):
        """Test no retry on non-retryable error"""
        mock_func = AsyncMock(side_effect=ValidationError("Invalid input"))

        with pytest.raises(ValidationError):
            await error_handler.execute_with_retry(mock_func, retry_config=retry_config)

        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_exhausted_retries(self, error_handler, retry_config):
        """Test all retries exhausted"""
        mock_func = AsyncMock(side_effect=RetryableError("Persistent failure"))

        with pytest.raises(RetryableError):
            await error_handler.execute_with_retry(mock_func, retry_config=retry_config)

        assert mock_func.call_count == 3  # max_attempts

    @pytest.mark.asyncio
    async def test_exponential_backoff_delay(self, error_handler):
        """Test exponential backoff delay calculation"""
        config = RetryConfig(
            max_attempts=4,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            backoff_multiplier=2.0,
            jitter=False,
        )

        delays = [error_handler._calculate_delay(i, config) for i in range(4)]

        assert delays[0] == 1.0  # 1.0 * 2^0
        assert delays[1] == 2.0  # 1.0 * 2^1
        assert delays[2] == 4.0  # 1.0 * 2^2
        assert delays[3] == 8.0  # 1.0 * 2^3

    @pytest.mark.asyncio
    async def test_linear_backoff_delay(self, error_handler):
        """Test linear backoff delay calculation"""
        config = RetryConfig(
            max_attempts=4,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=1.0,
            jitter=False,
        )

        delays = [error_handler._calculate_delay(i, config) for i in range(4)]

        assert delays[0] == 1.0  # 1.0 * 1
        assert delays[1] == 2.0  # 1.0 * 2
        assert delays[2] == 3.0  # 1.0 * 3
        assert delays[3] == 4.0  # 1.0 * 4

    @pytest.mark.asyncio
    async def test_fixed_delay(self, error_handler):
        """Test fixed delay calculation"""
        config = RetryConfig(
            max_attempts=4,
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=2.0,
            jitter=False,
        )

        delays = [error_handler._calculate_delay(i, config) for i in range(4)]

        assert all(d == 2.0 for d in delays)

    @pytest.mark.asyncio
    async def test_max_delay_limit(self, error_handler):
        """Test maximum delay limit is enforced"""
        config = RetryConfig(
            max_attempts=5,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=5.0,
            backoff_multiplier=2.0,
            jitter=False,
        )

        delays = [error_handler._calculate_delay(i, config) for i in range(5)]

        # 1, 2, 4, 8 (capped to 5), 16 (capped to 5)
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0
        assert delays[3] == 5.0  # Capped
        assert delays[4] == 5.0  # Capped


class TestCircuitBreaker:
    """Tests for circuit breaker functionality"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens_after_threshold(self, error_handler):
        """Test circuit breaker opens after failure threshold"""
        config = RetryConfig(max_attempts=1)  # No retries
        mock_func = AsyncMock(side_effect=RetryableError("Failure"))

        # Trigger failures to open circuit breaker
        for _ in range(5):
            try:
                await error_handler.execute_with_retry(mock_func, retry_config=config, context={"component": "test-component"})
            except RetryableError:
                pass

        # Circuit breaker should be open
        assert error_handler._is_circuit_breaker_open("test-component") is True

        # Next call should fail with CircuitBreakerError
        with pytest.raises(CircuitBreakerError):
            await error_handler.execute_with_retry(mock_func, retry_config=config, context={"component": "test-component"})

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, error_handler):
        """Test circuit breaker recovers after timeout"""
        config = RetryConfig(max_attempts=1)
        mock_func = AsyncMock(side_effect=RetryableError("Failure"))

        # Open circuit breaker
        for _ in range(5):
            try:
                await error_handler.execute_with_retry(mock_func, retry_config=config, context={"component": "test-component"})
            except RetryableError:
                pass

        # Manually set recovery timeout to 0 for testing
        error_handler.circuit_breakers["test-component"]["recovery_timeout"] = 0
        error_handler.circuit_breakers["test-component"]["last_failure_time"] = time.time() - 1

        # Circuit breaker should transition to half-open
        assert error_handler._is_circuit_breaker_open("test-component") is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_resets_on_success(self, error_handler):
        """Test circuit breaker resets on successful execution"""
        config = RetryConfig(max_attempts=1)

        # Trigger some failures
        mock_func = AsyncMock(side_effect=RetryableError("Failure"))
        for _ in range(3):
            try:
                await error_handler.execute_with_retry(mock_func, retry_config=config, context={"component": "test-component"})
            except RetryableError:
                pass

        # Now succeed
        mock_func = AsyncMock(return_value="success")
        result = await error_handler.execute_with_retry(mock_func, retry_config=config, context={"component": "test-component"})

        assert result == "success"
        # Circuit breaker should be reset
        assert error_handler.circuit_breakers["test-component"]["failure_count"] == 0
        assert error_handler.circuit_breakers["test-component"]["state"] == "closed"


class TestErrorClassification:
    """Tests for error classification and severity"""

    def test_workflow_error_severity(self):
        """Test WorkflowError severity classification"""
        error = WorkflowError("Test error", severity=ErrorSeverity.HIGH)
        assert error.severity == ErrorSeverity.HIGH

    def test_step_execution_error(self):
        """Test StepExecutionError creation"""
        error = StepExecutionError("Step failed", severity=ErrorSeverity.MEDIUM, component="step1", operation="execute")
        assert isinstance(error, WorkflowError)
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.component == "step1"

    def test_validation_error_not_retryable(self, error_handler):
        """Test ValidationError is not retryable"""
        config = RetryConfig()
        error = ValidationError("Invalid input")
        assert error_handler._is_retryable(error, config) is False

    def test_configuration_error_not_retryable(self, error_handler):
        """Test ConfigurationError is not retryable"""
        config = RetryConfig()
        error = ConfigurationError("Bad config")
        assert error_handler._is_retryable(error, config) is False

    def test_retryable_error_is_retryable(self, error_handler):
        """Test RetryableError is retryable"""
        config = RetryConfig()
        error = RetryableError("Temporary issue")
        assert error_handler._is_retryable(error, config) is True

    def test_non_retryable_error_not_retryable(self, error_handler):
        """Test NonRetryableError is not retryable"""
        config = RetryConfig()
        error = NonRetryableError("Permanent failure")
        assert error_handler._is_retryable(error, config) is False

    def test_connection_error_retryable(self, error_handler):
        """Test ConnectionError is retryable"""
        config = RetryConfig()
        error = ConnectionError("Connection lost")
        assert error_handler._is_retryable(error, config) is True

    def test_timeout_error_retryable(self, error_handler):
        """Test TimeoutError is retryable"""
        config = RetryConfig()
        error = TimeoutError("Request timeout")
        assert error_handler._is_retryable(error, config) is True

    def test_value_error_not_retryable(self, error_handler):
        """Test ValueError is not retryable"""
        config = RetryConfig()
        error = ValueError("Invalid value")
        assert error_handler._is_retryable(error, config) is False


class TestCustomRetryConfiguration:
    """Tests for custom retry configurations"""

    @pytest.mark.asyncio
    async def test_custom_retryable_exceptions(self, error_handler):
        """Test custom retryable exceptions list"""
        config = RetryConfig(
            max_attempts=2,
            retryable_exceptions=[ValueError],  # Make ValueError retryable
        )

        mock_func = AsyncMock(side_effect=[ValueError("Retryable"), "success"])

        result = await error_handler.execute_with_retry(mock_func, retry_config=config)

        assert result == "success"
        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_custom_non_retryable_exceptions(self, error_handler):
        """Test custom non-retryable exceptions list"""
        config = RetryConfig(
            max_attempts=3,
            non_retryable_exceptions=[ConnectionError],  # Make ConnectionError non-retryable
        )

        mock_func = AsyncMock(side_effect=ConnectionError("Non-retryable"))

        with pytest.raises(ConnectionError):
            await error_handler.execute_with_retry(mock_func, retry_config=config)

        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_no_retry_strategy(self, error_handler):
        """Test NONE retry strategy"""
        config = RetryConfig(max_attempts=3, strategy=RetryStrategy.NONE)

        mock_func = AsyncMock(side_effect=[RetryableError("Failure"), "success"])

        result = await error_handler.execute_with_retry(mock_func, retry_config=config)

        assert result == "success"
        # Delay should be 0
        delay = error_handler._calculate_delay(0, config)
        assert delay == 0


class TestErrorContext:
    """Tests for error context creation and tracking"""

    @pytest.mark.asyncio
    async def test_error_context_creation(self, error_handler, retry_config):
        """Test error context is created correctly"""
        mock_func = AsyncMock(side_effect=RetryableError("Test error"))

        try:
            await error_handler.execute_with_retry(
                mock_func, retry_config=retry_config, context={"component": "test", "operation": "test_op"}
            )
        except RetryableError:
            pass

        assert len(error_handler.error_history) > 0
        error_ctx = error_handler.error_history[0]
        assert error_ctx.component == "test"
        assert error_ctx.operation == "test_op"
        assert error_ctx.error_type == "RetryableError"
        assert "Test error" in error_ctx.error_message

    @pytest.mark.asyncio
    async def test_error_statistics(self, retry_config):
        """Test error statistics collection"""
        # Use a fresh error handler to avoid circuit breaker interference
        handler = ErrorHandler()
        mock_func = AsyncMock(side_effect=RetryableError("Test error"))

        # Generate some errors (use different components to avoid circuit breaker)
        for i in range(3):
            try:
                await handler.execute_with_retry(mock_func, retry_config=retry_config, context={"component": f"test-{i}"})
            except RetryableError:
                pass

        stats = handler.get_error_statistics()
        assert stats["total_errors"] >= 3
        assert "RetryableError" in stats["error_types"]

    @pytest.mark.asyncio
    async def test_error_statistics_by_component(self, error_handler, retry_config):
        """Test error statistics filtered by component"""
        mock_func = AsyncMock(side_effect=RetryableError("Test error"))

        # Generate errors for different components
        for component in ["comp1", "comp2"]:
            try:
                await error_handler.execute_with_retry(mock_func, retry_config=retry_config, context={"component": component})
            except RetryableError:
                pass

        stats_comp1 = error_handler.get_error_statistics(component="comp1")
        assert stats_comp1["total_errors"] >= 1


class TestSyncAndAsyncFunctions:
    """Tests for both sync and async function execution"""

    @pytest.mark.asyncio
    async def test_async_function_execution(self, error_handler, retry_config):
        """Test async function execution"""

        async def async_func():
            return "async_result"

        result = await error_handler.execute_with_retry(async_func, retry_config=retry_config)
        assert result == "async_result"

    @pytest.mark.asyncio
    async def test_sync_function_execution(self, error_handler, retry_config):
        """Test sync function execution"""

        def sync_func():
            return "sync_result"

        result = await error_handler.execute_with_retry(sync_func, retry_config=retry_config)
        assert result == "sync_result"

    @pytest.mark.asyncio
    async def test_function_with_args_and_kwargs(self, error_handler, retry_config):
        """Test function execution with args and kwargs"""

        async def func_with_params(a, b, c=None):
            return f"{a}-{b}-{c}"

        result = await error_handler.execute_with_retry(func_with_params, "arg1", "arg2", c="kwarg1", retry_config=retry_config)
        assert result == "arg1-arg2-kwarg1"
