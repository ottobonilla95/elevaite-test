"""
Phase 4.2: Circuit Breaker Tests

Test circuit breaker implementation including state transitions, retry logic,
and exponential backoff.
"""

import time

import pytest

from rbac_sdk.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
)


class TestCircuitBreakerStates:
    """Test circuit breaker state transitions."""

    def test_initial_state_is_closed(self):
        """Test that circuit breaker starts in CLOSED state."""
        breaker = CircuitBreaker()
        assert breaker.state == CircuitState.CLOSED

    def test_transition_to_open_after_failures(self):
        """Test transition from CLOSED to OPEN after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        def failing_func():
            raise Exception("Service error")

        # First 2 failures should keep circuit closed
        for _ in range(2):
            with pytest.raises(Exception):
                breaker.call(failing_func)
            assert breaker.state == CircuitState.CLOSED

        # 3rd failure should open circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN

    def test_open_circuit_rejects_calls(self):
        """Test that OPEN circuit rejects calls without executing function."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker(config)

        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Service error")

        # First call fails and opens circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN
        assert call_count == 1

        # Subsequent calls should be rejected without calling function
        with pytest.raises(CircuitBreakerOpenError):
            breaker.call(failing_func)
        assert call_count == 1  # Function not called

    def test_transition_to_half_open_after_timeout(self):
        """Test transition from OPEN to HALF_OPEN after timeout."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.1)
        breaker = CircuitBreaker(config)

        def failing_func():
            raise Exception("Service error")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        # Next call should transition to HALF_OPEN
        def success_func():
            return "success"

        result = breaker.call(success_func)
        assert result == "success"
        # After one success in half-open, still need more successes to close
        # (default success_threshold is 2)

    def test_transition_to_closed_from_half_open(self):
        """Test transition from HALF_OPEN to CLOSED after successful calls."""
        config = CircuitBreakerConfig(
            failure_threshold=1, timeout=0.1, success_threshold=2
        )
        breaker = CircuitBreaker(config)

        def failing_func():
            raise Exception("Service error")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        def success_func():
            return "success"

        # First success transitions to HALF_OPEN
        result1 = breaker.call(success_func)
        assert result1 == "success"
        assert breaker.state == CircuitState.HALF_OPEN

        # Second success closes the circuit
        result2 = breaker.call(success_func)
        assert result2 == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_half_open_reopens_on_failure(self):
        """Test that HALF_OPEN reopens on any failure."""
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.1)
        breaker = CircuitBreaker(config)

        def failing_func():
            raise Exception("Service error")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        # First call transitions to HALF_OPEN
        def success_func():
            return "success"

        breaker.call(success_func)
        assert breaker.state == CircuitState.HALF_OPEN

        # Failure in HALF_OPEN should reopen circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerFallback:
    """Test circuit breaker fallback behavior."""

    def test_fallback_on_open_circuit(self):
        """Test that fallback is returned when circuit is open."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker(config)

        def failing_func():
            raise Exception("Service error")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN

        # Call with fallback should return fallback value
        result = breaker.call(failing_func, fallback="fallback_value")
        assert result == "fallback_value"

    def test_fallback_on_failure(self):
        """Test that fallback is returned on failure."""
        breaker = CircuitBreaker()

        def failing_func():
            raise Exception("Service error")

        result = breaker.call(failing_func, fallback="fallback_value")
        assert result == "fallback_value"


class TestCircuitBreakerRetry:
    """Test circuit breaker retry logic."""

    def test_retry_with_exponential_backoff(self):
        """Test retry with exponential backoff."""
        config = CircuitBreakerConfig(
            max_retries=3, retry_backoff_base=0.1, failure_threshold=10
        )
        breaker = CircuitBreaker(config)

        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Service error")

        start = time.time()
        result = breaker.call_with_retry(failing_func, fallback="fallback")
        elapsed = time.time() - start

        # Should have tried 4 times (initial + 3 retries)
        assert call_count == 4
        assert result == "fallback"

        # Should have waited: 0.1 + 0.2 + 0.4 = 0.7 seconds
        assert elapsed >= 0.7

    def test_retry_stops_on_success(self):
        """Test that retry stops on first success."""
        config = CircuitBreakerConfig(max_retries=3, failure_threshold=10)
        breaker = CircuitBreaker(config)

        call_count = 0

        def sometimes_failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Service error")
            return "success"

        result = breaker.call_with_retry(sometimes_failing_func)
        assert result == "success"
        assert call_count == 3  # Failed twice, succeeded on 3rd

    def test_retry_respects_max_backoff(self):
        """Test that retry respects maximum backoff delay."""
        config = CircuitBreakerConfig(
            max_retries=5,
            retry_backoff_base=1.0,
            retry_backoff_max=2.0,
            failure_threshold=10,
        )
        breaker = CircuitBreaker(config)

        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Service error")

        start = time.time()
        result = breaker.call_with_retry(failing_func, fallback="fallback")
        elapsed = time.time() - start

        # Should have tried 6 times (initial + 5 retries)
        assert call_count == 6
        assert result == "fallback"

        # Backoff delays: 1.0, 2.0 (capped), 2.0 (capped), 2.0 (capped), 2.0 (capped)
        # Total: 9.0 seconds
        assert elapsed >= 9.0

    def test_retry_stops_on_open_circuit(self):
        """Test that retry stops when circuit opens."""
        config = CircuitBreakerConfig(
            max_retries=10, failure_threshold=3, retry_backoff_base=0.01
        )
        breaker = CircuitBreaker(config)

        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Service error")

        result = breaker.call_with_retry(failing_func, fallback="fallback")

        # Should stop after circuit opens (3 failures)
        assert call_count == 3
        assert result == "fallback"
        assert breaker.state == CircuitState.OPEN


class TestCircuitBreakerStats:
    """Test circuit breaker statistics."""

    def test_stats_track_calls(self):
        """Test that stats track total calls."""
        breaker = CircuitBreaker()

        def success_func():
            return "success"

        for _ in range(10):
            breaker.call(success_func)

        assert breaker.stats.total_calls == 10
        assert breaker.stats.total_successes == 10
        assert breaker.stats.total_failures == 0

    def test_stats_track_failures(self):
        """Test that stats track failures."""
        config = CircuitBreakerConfig(failure_threshold=10)
        breaker = CircuitBreaker(config)

        def failing_func():
            raise Exception("Service error")

        for _ in range(5):
            with pytest.raises(Exception):
                breaker.call(failing_func)

        assert breaker.stats.total_calls == 5
        assert breaker.stats.total_successes == 0
        assert breaker.stats.total_failures == 5

    def test_stats_track_rejections(self):
        """Test that stats track rejections when circuit is open."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker(config)

        def failing_func():
            raise Exception("Service error")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)

        # Try 5 more calls (should be rejected)
        for _ in range(5):
            with pytest.raises(CircuitBreakerOpenError):
                breaker.call(failing_func)

        assert breaker.stats.total_rejections == 5


class TestCircuitBreakerReset:
    """Test circuit breaker reset functionality."""

    def test_reset_closes_circuit(self):
        """Test that reset closes the circuit."""
        config = CircuitBreakerConfig(failure_threshold=1)
        breaker = CircuitBreaker(config)

        def failing_func():
            raise Exception("Service error")

        # Open the circuit
        with pytest.raises(Exception):
            breaker.call(failing_func)
        assert breaker.state == CircuitState.OPEN

        # Reset should close the circuit
        breaker.reset()
        assert breaker.state == CircuitState.CLOSED

    def test_reset_clears_counters(self):
        """Test that reset clears failure counters."""
        config = CircuitBreakerConfig(failure_threshold=5)
        breaker = CircuitBreaker(config)

        def failing_func():
            raise Exception("Service error")

        # Accumulate some failures
        for _ in range(3):
            with pytest.raises(Exception):
                breaker.call(failing_func)

        assert breaker.stats.failure_count == 3

        # Reset should clear counters
        breaker.reset()
        assert breaker.stats.failure_count == 0
        assert breaker.stats.success_count == 0


class TestCircuitBreakerCustomFailure:
    """Test circuit breaker with custom failure detection."""

    def test_custom_failure_detection(self):
        """Test circuit breaker with custom is_failure function."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker(config)

        def api_call():
            # Returns None on failure
            return None

        def is_failure(result):
            return result is None

        # First 2 failures should keep circuit closed
        for _ in range(2):
            result = breaker.call(api_call, is_failure=is_failure, fallback="fallback")
            assert result is None or result == "fallback"
            assert breaker.state == CircuitState.CLOSED

        # 3rd failure should open circuit
        result = breaker.call(api_call, is_failure=is_failure, fallback="fallback")
        assert breaker.state == CircuitState.OPEN

