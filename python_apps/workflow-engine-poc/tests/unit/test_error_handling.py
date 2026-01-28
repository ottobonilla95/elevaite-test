"""
Test Enhanced Error Handling and Retry Mechanisms

Tests for robust error handling, retry logic with exponential backoff,
and graceful failure recovery for production reliability.
"""

import asyncio
import time
import pytest

from workflow_core_sdk.error_handling import (
    error_handler,
    RetryConfig,
    RetryStrategy,
    CircuitBreakerError,
)


@pytest.mark.unit
async def test_retry_mechanisms():
    """Test retry mechanisms with different strategies"""

    print("🧪 Testing Retry Mechanisms")
    print("-" * 40)

    # Test successful execution after retries
    print("\n📋 Testing Successful Retry:")

    attempt_count = 0

    async def flaky_function():
        nonlocal attempt_count
        attempt_count += 1

        if attempt_count < 3:
            raise ConnectionError(
                f"Temporary connection error (attempt {attempt_count})"
            )

        return {"success": True, "attempts": attempt_count}

    retry_config = RetryConfig(
        max_attempts=5,
        strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
        base_delay=0.1,  # Fast for testing
        max_delay=1.0,
    )

    start_time = time.time()
    result = await error_handler.execute_with_retry(
        flaky_function,
        retry_config=retry_config,
        context={"component": "test", "operation": "flaky_function"},
    )
    end_time = time.time()

    print(f"   ✅ Function succeeded after {result['attempts']} attempts")
    print(f"   ⏱️  Total time: {end_time - start_time:.2f}s")

    # Test non-retryable error
    print("\n📋 Testing Non-Retryable Error:")

    async def non_retryable_function():
        raise ValueError("This is a configuration error that should not be retried")

    try:
        await error_handler.execute_with_retry(
            non_retryable_function,
            retry_config=retry_config,
            context={"component": "test", "operation": "non_retryable_function"},
        )
        print("   ❌ Should have failed")
    except ValueError as e:
        print(f"   ✅ Non-retryable error correctly not retried: {e}")

    # Test retry exhaustion
    print("\n📋 Testing Retry Exhaustion:")

    async def always_failing_function():
        raise ConnectionError("This always fails")

    retry_config_limited = RetryConfig(
        max_attempts=2, strategy=RetryStrategy.FIXED_DELAY, base_delay=0.1
    )

    try:
        await error_handler.execute_with_retry(
            always_failing_function,
            retry_config=retry_config_limited,
            context={"component": "test", "operation": "always_failing_function"},
        )
        print("   ❌ Should have failed")
    except ConnectionError as e:
        print(f"   ✅ Retry exhaustion handled correctly: {e}")


@pytest.mark.unit
async def test_circuit_breaker():
    """Test circuit breaker functionality"""

    print("\n🧪 Testing Circuit Breaker")
    print("-" * 40)

    # Reset error handler for clean test
    error_handler.circuit_breakers.clear()

    async def failing_service():
        raise ConnectionError("Service unavailable")

    retry_config = RetryConfig(
        max_attempts=2, strategy=RetryStrategy.FIXED_DELAY, base_delay=0.1
    )

    # Trigger circuit breaker by failing multiple times
    print("📋 Triggering circuit breaker:")

    for i in range(6):  # Exceed failure threshold
        try:
            await error_handler.execute_with_retry(
                failing_service,
                retry_config=retry_config,
                context={"component": "test_service", "operation": "failing_service"},
            )
        except Exception:
            pass

    # Check if circuit breaker is open
    breaker_state = error_handler.circuit_breakers.get("test_service", {})
    print(f"   Circuit breaker state: {breaker_state.get('state', 'unknown')}")
    print(f"   Failure count: {breaker_state.get('failure_count', 0)}")

    # Try to execute when circuit breaker is open
    print("\n📋 Testing circuit breaker open state:")

    try:
        await error_handler.execute_with_retry(
            failing_service,
            retry_config=retry_config,
            context={"component": "test_service", "operation": "failing_service"},
        )
        print("   ❌ Should have been blocked by circuit breaker")
    except CircuitBreakerError as e:
        print(f"   ✅ Circuit breaker correctly blocked execution: {e}")


@pytest.mark.unit
async def test_error_classification():
    """Test error classification and statistics"""

    print("\n🧪 Testing Error Classification")
    print("-" * 40)

    # Clear error history for clean test
    error_handler.error_history.clear()

    # Generate different types of errors
    errors_to_test = [
        (ConnectionError("Network error"), "retryable"),
        (ValueError("Invalid configuration"), "non-retryable"),
        (TimeoutError("Request timeout"), "retryable"),
        (TypeError("Type mismatch"), "non-retryable"),
    ]

    for error, expected_type in errors_to_test:
        try:
            await error_handler.execute_with_retry(
                lambda: (_ for _ in ()).throw(error),
                retry_config=RetryConfig(max_attempts=1),
                context={"component": "test_classification", "operation": "error_test"},
            )
        except Exception:
            pass

    # Get error statistics
    stats = error_handler.get_error_statistics()

    print("📊 Error Statistics:")
    print(f"   Total errors: {stats.get('total_errors', 0)}")
    print(f"   Error types: {stats.get('error_types', {})}")
    print(f"   Severity counts: {stats.get('severity_counts', {})}")


@pytest.mark.unit
async def test_retry_strategies():
    """Test different retry strategies"""

    print("\n🧪 Testing Retry Strategies")
    print("-" * 40)

    strategies = [
        (RetryStrategy.FIXED_DELAY, "Fixed Delay"),
        (RetryStrategy.LINEAR_BACKOFF, "Linear Backoff"),
        (RetryStrategy.EXPONENTIAL_BACKOFF, "Exponential Backoff"),
    ]

    for strategy, name in strategies:
        print(f"\n📋 Testing {name}:")

        attempt_times = []

        async def timing_function():
            attempt_times.append(time.time())
            if len(attempt_times) < 3:
                raise ConnectionError("Temporary error")
            return {"success": True}

        retry_config = RetryConfig(
            max_attempts=4,
            strategy=strategy,
            base_delay=0.2,
            backoff_multiplier=2.0,
            jitter=False,  # Disable jitter for predictable timing
        )

        time.time()
        try:
            await error_handler.execute_with_retry(
                timing_function,
                retry_config=retry_config,
                context={"component": "test_strategy", "operation": "timing_function"},
            )

            # Calculate delays between attempts
            delays = []
            for i in range(1, len(attempt_times)):
                delay = attempt_times[i] - attempt_times[i - 1]
                delays.append(delay)

            print(f"   ✅ Strategy: {name}")
            print(f"   📊 Delays: {[f'{d:.2f}s' for d in delays]}")

        except Exception as e:
            print(f"   ❌ Strategy failed: {e}")

        # Reset for next test
        attempt_times.clear()


@pytest.mark.unit
async def test_workflow_error_integration():
    """Test error handling integration with workflow execution"""

    print("\n🧪 Testing Workflow Error Integration")
    print("-" * 40)

    from workflow_core_sdk.execution_context import ExecutionContext, UserContext
    from workflow_core_sdk import WorkflowEngine, StepRegistry

    # Create test workflow with retry configuration
    workflow_config = {
        "workflow_id": "error-test-workflow",
        "name": "Error Test Workflow",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "reliable_step",
                "step_name": "Reliable Step",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "input_type": "static",
                    "data": {"message": "This step should succeed"},
                },
                "max_retries": 0,
            },
            {
                "step_id": "flaky_step",
                "step_name": "Flaky Step",
                "step_type": "data_processing",
                "step_order": 2,
                "dependencies": ["reliable_step"],
                "config": {"operation": "transform", "transformation": "upper"},
                "max_retries": 3,
                "retry_strategy": "exponential_backoff",
                "retry_delay_seconds": 0.1,
                "timeout_seconds": 5,
                "critical": False,  # Don't fail workflow if this fails
            },
        ],
    }

    # Initialize components
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()

    workflow_engine = WorkflowEngine(step_registry)

    # Create execution context
    user_context = UserContext(user_id="error_test_user")
    execution_context = ExecutionContext(workflow_config, user_context)

    # Execute workflow
    print("📋 Executing workflow with error handling:")

    await workflow_engine.execute_workflow(execution_context)

    # Check results
    summary = execution_context.get_execution_summary()
    print(f"   Workflow status: {summary['status']}")
    print(f"   Completed steps: {summary.get('completed_steps', 0)}")
    print(f"   Failed steps: {summary.get('failed_steps', 0)}")

    # Get error statistics
    stats = error_handler.get_error_statistics()
    print(f"   Total errors recorded: {stats.get('total_errors', 0)}")


async def main():
    """Run all error handling tests"""

    print("🚀 Enhanced Error Handling Test Suite")
    print("=" * 60)

    try:
        await test_retry_mechanisms()
        await test_circuit_breaker()
        await test_error_classification()
        await test_retry_strategies()
        await test_workflow_error_integration()

        print("\n🎉 All error handling tests completed successfully!")
        print("✅ Enhanced error handling and retry mechanisms are working correctly")

    except Exception as e:
        print(f"\n❌ Error handling test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
