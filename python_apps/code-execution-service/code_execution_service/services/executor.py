"""Main executor service that orchestrates validation and sandbox execution."""

import logging

from ..core.config import settings
from ..schemas.requests import ExecuteRequest
from ..schemas.responses import ExecuteResponse
from .sandbox import SandboxExecutor
from .validator import CodeValidator

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Orchestrates code validation and execution."""

    def __init__(
        self,
        validator: CodeValidator | None = None,
        sandbox: SandboxExecutor | None = None,
    ):
        self.validator = validator or CodeValidator()
        self.sandbox = sandbox or SandboxExecutor()

    async def execute(self, request: ExecuteRequest) -> ExecuteResponse:
        """Execute code with validation and sandboxing.

        Args:
            request: The execution request containing code and parameters

        Returns:
            ExecuteResponse with execution results or validation errors
        """
        # Validate language (only Python in Phase 1)
        if request.language.lower() != "python":
            return ExecuteResponse(
                success=False,
                error=f"Unsupported language: {request.language}. Only 'python' is supported.",
            )

        # Validate code length
        if len(request.code) > settings.max_code_length:
            return ExecuteResponse(
                success=False,
                error=f"Code exceeds maximum length of {settings.max_code_length} bytes.",
            )

        # Validate timeout and memory bounds
        timeout = max(
            settings.min_timeout_seconds,
            min(request.timeout_seconds, settings.max_timeout_seconds),
        )
        memory = max(
            settings.min_memory_mb,
            min(request.memory_mb, settings.max_memory_mb),
        )

        # Pre-execution validation
        logger.debug("Validating code...")
        validation_result = self.validator.validate(request.code)

        if not validation_result.is_valid:
            logger.warning(f"Code validation failed: {validation_result.errors}")
            return ExecuteResponse(
                success=False,
                validation_errors=validation_result.errors,
            )

        # Execute in sandbox
        logger.debug(f"Executing code with timeout={timeout}s, memory={memory}MB")
        sandbox_result = await self.sandbox.execute(
            code=request.code,
            timeout_seconds=timeout,
            memory_mb=memory,
            input_data=request.input_data,
        )

        # Build response
        success = sandbox_result.exit_code == 0 and sandbox_result.error is None

        return ExecuteResponse(
            success=success,
            stdout=sandbox_result.stdout,
            stderr=sandbox_result.stderr,
            exit_code=sandbox_result.exit_code,
            execution_time_ms=sandbox_result.execution_time_ms,
            error=sandbox_result.error,
        )


# Global executor instance
_executor: CodeExecutor | None = None


def get_executor() -> CodeExecutor:
    """Get or create the global executor instance."""
    global _executor
    if _executor is None:
        _executor = CodeExecutor()
    return _executor
