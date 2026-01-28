"""Code execution router."""

import logging

from fastapi import APIRouter, Depends

from ..schemas.requests import ExecuteRequest
from ..schemas.responses import ExecuteResponse
from ..services.executor import CodeExecutor, get_executor

logger = logging.getLogger(__name__)

router = APIRouter(tags=["execute"])


@router.post("/execute", response_model=ExecuteResponse)
async def execute_code(
    request: ExecuteRequest,
    executor: CodeExecutor = Depends(get_executor),
) -> ExecuteResponse:
    """Execute code in a secure sandbox.

    This endpoint:
    1. Validates the code for security issues (blocked imports, functions, patterns)
    2. Executes the code in an Nsjail sandbox with resource limits
    3. Returns the execution result (stdout, stderr, exit_code, timing)

    Args:
        request: Execution request with code, timeout, memory, and optional input_data

    Returns:
        ExecuteResponse with execution results or validation/execution errors
    """
    logger.info(f"Received execute request: language={request.language}, timeout={request.timeout_seconds}s")

    response = await executor.execute(request)

    if response.success:
        logger.info(f"Code executed successfully in {response.execution_time_ms}ms")
    else:
        logger.warning(f"Code execution failed: {response.error or response.validation_errors}")

    return response

