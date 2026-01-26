"""
Circuit Breaker implementation for RBAC SDK.

Implements the Circuit Breaker pattern to prevent cascading failures when
external services (Auth API, RBAC service) are down or degraded.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests fail fast without calling service
- HALF_OPEN: Testing if service has recovered, limited requests pass through
"""

from __future__ import annotations
import time
from enum import Enum
from typing import Callable, Optional, TypeVar, Any
from dataclasses import dataclass, field


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5  # Number of failures before opening
    success_threshold: int = 2  # Number of successes to close from half-open
    timeout: float = 60.0  # Seconds to wait before trying half-open
    max_retries: int = 3  # Maximum number of retries
    retry_backoff_base: float = 1.0  # Base delay for exponential backoff (seconds)
    retry_backoff_max: float = 30.0  # Maximum retry delay (seconds)


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""

    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    total_calls: int = 0
    total_failures: int = 0
    total_successes: int = 0
    total_rejections: int = 0  # Calls rejected due to open circuit


T = TypeVar("T")


class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    Usage:
        breaker = CircuitBreaker()

        def risky_operation():
            # Call external service
            return result

        result = breaker.call(risky_operation)
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """Initialize circuit breaker."""
        self.config = config or CircuitBreakerConfig()
        self.stats = CircuitBreakerStats()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self.stats.state

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset from OPEN to HALF_OPEN."""
        if self.stats.state != CircuitState.OPEN:
            return False

        if self.stats.last_failure_time is None:
            return False

        elapsed = time.time() - self.stats.last_failure_time
        return elapsed >= self.config.timeout

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        if new_state != self.stats.state:
            self.stats.state = new_state
            self.stats.last_state_change = time.time()

            # Reset counters on state change
            if new_state == CircuitState.CLOSED:
                self.stats.failure_count = 0
                self.stats.success_count = 0
            elif new_state == CircuitState.HALF_OPEN:
                self.stats.success_count = 0

    def _record_success(self) -> None:
        """Record a successful call."""
        self.stats.total_calls += 1
        self.stats.total_successes += 1

        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.success_count += 1
            if self.stats.success_count >= self.config.success_threshold:
                self._transition_to(CircuitState.CLOSED)
        elif self.stats.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.stats.failure_count = 0

    def _record_failure(self) -> None:
        """Record a failed call."""
        self.stats.total_calls += 1
        self.stats.total_failures += 1
        self.stats.last_failure_time = time.time()

        if self.stats.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state reopens the circuit
            self._transition_to(CircuitState.OPEN)
        elif self.stats.state == CircuitState.CLOSED:
            self.stats.failure_count += 1
            if self.stats.failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def call(
        self,
        func: Callable[[], T],
        *,
        fallback: Optional[T] = None,
        is_failure: Optional[Callable[[Any], bool]] = None,
    ) -> T:
        """
        Call a function through the circuit breaker.

        Args:
            func: Function to call
            fallback: Value to return if circuit is open or call fails
            is_failure: Optional function to determine if result is a failure
                       (default: any exception is a failure)

        Returns:
            Result of func() or fallback value

        Raises:
            CircuitBreakerOpenError: If circuit is open and no fallback provided
        """
        # Check if we should attempt reset
        if self._should_attempt_reset():
            self._transition_to(CircuitState.HALF_OPEN)

        # Reject if circuit is open
        if self.stats.state == CircuitState.OPEN:
            self.stats.total_rejections += 1
            if fallback is not None:
                return fallback
            raise CircuitBreakerOpenError("Circuit breaker is open")

        # Try to call the function
        try:
            result = func()

            # Check if result indicates failure
            if is_failure and is_failure(result):
                self._record_failure()
                if fallback is not None:
                    return fallback
                return result

            self._record_success()
            return result

        except Exception:
            self._record_failure()
            if fallback is not None:
                return fallback
            raise

    def call_with_retry(
        self,
        func: Callable[[], T],
        *,
        fallback: Optional[T] = None,
        is_failure: Optional[Callable[[Any], bool]] = None,
    ) -> T:
        """
        Call a function with retry logic and exponential backoff.

        Args:
            func: Function to call
            fallback: Value to return if all retries fail
            is_failure: Optional function to determine if result is a failure

        Returns:
            Result of func() or fallback value
        """
        last_exception = None
        attempt = 0

        while attempt <= self.config.max_retries:
            try:
                # Use circuit breaker for the call
                result = self.call(func, is_failure=is_failure)
                return result

            except CircuitBreakerOpenError:
                # Circuit is open, don't retry
                if fallback is not None:
                    return fallback
                raise

            except Exception as e:
                last_exception = e
                attempt += 1

                if attempt <= self.config.max_retries:
                    # Calculate exponential backoff delay
                    delay = min(
                        self.config.retry_backoff_base * (2 ** (attempt - 1)),
                        self.config.retry_backoff_max,
                    )
                    time.sleep(delay)

        # All retries failed
        if fallback is not None:
            return fallback

        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("All retries failed")

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self._transition_to(CircuitState.CLOSED)
        self.stats.failure_count = 0
        self.stats.success_count = 0
        self.stats.last_failure_time = None


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejects a call."""

    pass
