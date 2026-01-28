"""
Enhanced Error Handling and Retry Mechanisms

Provides robust error handling, retry logic with exponential backoff,
and graceful failure recovery for production reliability.
"""

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Type
from enum import Enum
from dataclasses import dataclass
import random
import traceback


logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryStrategy(str, Enum):
    """Retry strategy types"""

    NONE = "none"
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    CUSTOM = "custom"


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""

    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff_multiplier: float = 2.0
    jitter: bool = True  # Add random jitter to prevent thundering herd
    retryable_exceptions: List[Type[Exception]] = None
    non_retryable_exceptions: List[Type[Exception]] = None


@dataclass
class ErrorContext:
    """Context information for errors"""

    error_id: str
    timestamp: float
    severity: ErrorSeverity
    component: str
    operation: str
    error_type: str
    error_message: str
    stack_trace: str
    retry_attempt: int = 0
    max_retries: int = 0
    metadata: Dict[str, Any] = None


class WorkflowError(Exception):
    """Base exception for workflow-related errors"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        component: str = "unknown",
        operation: str = "unknown",
        metadata: Dict[str, Any] = None,
    ):
        super().__init__(message)
        self.severity = severity
        self.component = component
        self.operation = operation
        self.metadata = metadata or {}


class StepExecutionError(WorkflowError):
    """Error during step execution"""

    pass


class ValidationError(WorkflowError):
    """Error during validation"""

    pass


class ConfigurationError(WorkflowError):
    """Error in configuration"""

    pass


class RetryableError(WorkflowError):
    """Error that can be retried"""

    pass


class NonRetryableError(WorkflowError):
    """Error that should not be retried"""

    pass


class CircuitBreakerError(WorkflowError):
    """Error when circuit breaker is open"""

    pass


class ErrorHandler:
    """Enhanced error handler with retry mechanisms"""

    def __init__(self):
        self.error_history: List[ErrorContext] = []
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.default_retry_config = RetryConfig()

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        retry_config: Optional[RetryConfig] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Any:
        """
        Execute a function with retry logic and error handling.

        Args:
            func: Function to execute
            *args: Function arguments
            retry_config: Retry configuration
            context: Additional context for error reporting
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all retry attempts fail
        """
        config = retry_config or self.default_retry_config
        context = context or {}

        last_exception = None

        for attempt in range(config.max_attempts):
            try:
                # Check circuit breaker
                component = context.get("component", "unknown")
                if self._is_circuit_breaker_open(component):
                    raise CircuitBreakerError(
                        f"Circuit breaker open for component: {component}",
                        severity=ErrorSeverity.HIGH,
                        component=component,
                    )

                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # Success - reset circuit breaker
                self._record_success(component)

                if attempt > 0:
                    logger.info(f"Function succeeded after {attempt + 1} attempts")

                return result

            except Exception as e:
                last_exception = e

                # Record error
                error_context = self._create_error_context(
                    e, attempt + 1, config.max_attempts, context
                )
                self._record_error(error_context)

                # Check if error is retryable
                if not self._is_retryable(e, config):
                    logger.error(f"Non-retryable error: {e}")
                    raise e

                # Check if we've exhausted retries
                if attempt >= config.max_attempts - 1:
                    logger.error(f"All retry attempts exhausted for {func.__name__}")
                    break

                # Calculate delay and wait
                delay = self._calculate_delay(attempt, config)
                logger.warning(
                    f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}"
                )

                await asyncio.sleep(delay)

        # All retries failed
        if last_exception:
            raise last_exception

    def _create_error_context(
        self,
        error: Exception,
        retry_attempt: int,
        max_retries: int,
        context: Dict[str, Any],
    ) -> ErrorContext:
        """Create error context from exception"""

        import uuid

        severity = ErrorSeverity.MEDIUM
        if isinstance(error, WorkflowError):
            severity = error.severity
        elif isinstance(error, (ConnectionError, TimeoutError)):
            severity = ErrorSeverity.HIGH
        elif isinstance(error, (MemoryError, SystemError)):
            severity = ErrorSeverity.CRITICAL

        return ErrorContext(
            error_id=str(uuid.uuid4()),
            timestamp=time.time(),
            severity=severity,
            component=context.get("component", "unknown"),
            operation=context.get("operation", "unknown"),
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            retry_attempt=retry_attempt,
            max_retries=max_retries,
            metadata=context,
        )

    def _record_error(self, error_context: ErrorContext):
        """Record error for monitoring and circuit breaker logic"""
        self.error_history.append(error_context)

        # Update circuit breaker
        component = error_context.component
        if component not in self.circuit_breakers:
            self.circuit_breakers[component] = {
                "failure_count": 0,
                "last_failure_time": 0,
                "state": "closed",  # closed, open, half_open
                "failure_threshold": 5,
                "recovery_timeout": 60,
            }

        breaker = self.circuit_breakers[component]
        breaker["failure_count"] += 1
        breaker["last_failure_time"] = time.time()

        # Open circuit breaker if threshold exceeded
        if breaker["failure_count"] >= breaker["failure_threshold"]:
            breaker["state"] = "open"
            logger.warning(f"Circuit breaker opened for component: {component}")

    def _record_success(self, component: str):
        """Record successful execution"""
        if component in self.circuit_breakers:
            breaker = self.circuit_breakers[component]
            breaker["failure_count"] = 0
            breaker["state"] = "closed"

    def _is_circuit_breaker_open(self, component: str) -> bool:
        """Check if circuit breaker is open for component"""
        if component not in self.circuit_breakers:
            return False

        breaker = self.circuit_breakers[component]

        if breaker["state"] == "closed":
            return False

        if breaker["state"] == "open":
            # Check if recovery timeout has passed
            if time.time() - breaker["last_failure_time"] > breaker["recovery_timeout"]:
                breaker["state"] = "half_open"
                logger.info(f"Circuit breaker half-open for component: {component}")
                return False
            return True

        # half_open state - allow one attempt
        return False

    def _is_retryable(self, error: Exception, config: RetryConfig) -> bool:
        """Check if error is retryable based on configuration"""

        # Check non-retryable exceptions first
        if config.non_retryable_exceptions:
            for exc_type in config.non_retryable_exceptions:
                if isinstance(error, exc_type):
                    return False

        # Check retryable exceptions
        if config.retryable_exceptions:
            for exc_type in config.retryable_exceptions:
                if isinstance(error, exc_type):
                    return True
            return False  # If retryable list is specified, only those are retryable

        # Default retryable errors
        retryable_types = (
            ConnectionError,
            TimeoutError,
            RetryableError,
            asyncio.TimeoutError,
        )

        # Default non-retryable errors
        non_retryable_types = (
            ValidationError,
            ConfigurationError,
            NonRetryableError,
            ValueError,
            TypeError,
            AttributeError,
        )

        if isinstance(error, non_retryable_types):
            return False

        if isinstance(error, retryable_types):
            return True

        # For unknown errors, be conservative and don't retry
        return False

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for retry attempt"""

        if config.strategy == RetryStrategy.NONE:
            return 0

        elif config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay

        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * (attempt + 1)

        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_multiplier**attempt)

        else:
            delay = config.base_delay

        # Apply maximum delay limit
        delay = min(delay, config.max_delay)

        # Add jitter to prevent thundering herd
        if config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)

    def get_error_statistics(self, component: Optional[str] = None) -> Dict[str, Any]:
        """Get error statistics for monitoring"""

        errors = self.error_history
        if component:
            errors = [e for e in errors if e.component == component]

        if not errors:
            return {"total_errors": 0}

        # Calculate statistics
        total_errors = len(errors)
        error_types = {}
        severity_counts = {}

        for error in errors:
            error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
            severity_counts[error.severity] = severity_counts.get(error.severity, 0) + 1

        recent_errors = [
            e for e in errors if time.time() - e.timestamp < 3600
        ]  # Last hour

        return {
            "total_errors": total_errors,
            "recent_errors": len(recent_errors),
            "error_types": error_types,
            "severity_counts": severity_counts,
            "circuit_breakers": self.circuit_breakers,
        }


# Global error handler instance
error_handler = ErrorHandler()
