"""
Code Execution Step

Allows executing Python code in a secure sandbox via the Code Execution Service.
The service uses Nsjail for isolation with defense-in-depth security.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict

import httpx

from ..execution_context import ExecutionContext
from ..streaming import stream_manager

logger = logging.getLogger(__name__)

# Get code execution service URL from environment
CODE_EXECUTION_SERVICE_URL = os.getenv(
    "CODE_EXECUTION_SERVICE_URL", "http://localhost:8007"
)


async def code_execution_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Execute Python code via the Code Execution Service.

    Config options (step_config["config"]):
    - code: str                   # Python code to execute (required)
    - timeout: int                # Execution timeout in seconds (default: 30, max: 60)
    - memory_mb: int              # Memory limit in MB (default: 256, max: 512)

    The step passes input_data to the sandbox, making it available as the
    `input_data` variable within the executed code.

    Args:
        step_config: Step configuration containing the code and limits
        input_data: Input data from previous steps (available in sandbox)
        execution_context: Execution context

    Returns:
        Dict with success, stdout, stderr, exit_code, and execution_time_ms
    """
    config = step_config.get("config", {})
    step_id = step_config.get("step_id", "code_execution")

    code = config.get("code", "")
    timeout = config.get("timeout", 30)
    memory_mb = config.get("memory_mb", 256)

    if not code:
        return {
            "success": False,
            "error": "No code provided",
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "execution_time_ms": 0,
        }

    logger.info(
        f"Executing code for step {step_id} (timeout={timeout}s, memory={memory_mb}MB)"
    )

    try:
        # Emit step event for running status
        try:
            from ..streaming import create_step_event

            step_event = create_step_event(
                execution_id=execution_context.execution_id,
                step_id=step_id,
                step_status="running",
                workflow_id=execution_context.workflow_id,
                step_type="code_execution",
                output_data={"status": "executing"},
            )
            await stream_manager.emit_execution_event(step_event)
            if execution_context.workflow_id:
                await stream_manager.emit_workflow_event(step_event)
        except Exception as e:
            logger.debug(f"Failed to emit running event: {e}")

        # Call code execution service
        # Add buffer to HTTP timeout to allow for service-side timeout
        http_timeout = timeout + 10

        async with httpx.AsyncClient(timeout=http_timeout) as client:
            response = await client.post(
                f"{CODE_EXECUTION_SERVICE_URL}/execute",
                json={
                    "language": "python",
                    "code": code,
                    "timeout_seconds": timeout,
                    "memory_mb": memory_mb,
                    "input_data": input_data,
                },
            )
            response.raise_for_status()
            result = response.json()

        # Build response
        return {
            "success": result.get("success", False),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exit_code", -1),
            "execution_time_ms": result.get("execution_time_ms", 0),
            "error": result.get("error"),
            "executed_at": datetime.now().isoformat(),
        }

    except httpx.TimeoutException:
        error_msg = f"Code execution timed out after {http_timeout}s"
        logger.error(error_msg)

        # Emit failed event
        try:
            from ..streaming import create_step_event

            error_event = create_step_event(
                execution_id=execution_context.execution_id,
                step_id=step_id,
                step_status="failed",
                workflow_id=execution_context.workflow_id,
                step_type="code_execution",
                output_data={"error": error_msg},
            )
            await stream_manager.emit_execution_event(error_event)
            if execution_context.workflow_id:
                await stream_manager.emit_workflow_event(error_event)
        except Exception as emit_error:
            logger.debug(f"Failed to emit timeout error event: {emit_error}")

        return {
            "success": False,
            "error": error_msg,
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "execution_time_ms": timeout * 1000,
            "executed_at": datetime.now().isoformat(),
        }

    except httpx.HTTPStatusError as e:
        error_msg = f"Code execution service error: {e.response.status_code}"
        logger.error(f"{error_msg}: {e.response.text}")

        # Emit failed event
        try:
            from ..streaming import create_step_event

            error_event = create_step_event(
                execution_id=execution_context.execution_id,
                step_id=step_id,
                step_status="failed",
                workflow_id=execution_context.workflow_id,
                step_type="code_execution",
                output_data={"error": error_msg},
            )
            await stream_manager.emit_execution_event(error_event)
            if execution_context.workflow_id:
                await stream_manager.emit_workflow_event(error_event)
        except Exception as emit_error:
            logger.debug(f"Failed to emit HTTP error event: {emit_error}")

        return {
            "success": False,
            "error": error_msg,
            "stdout": "",
            "stderr": e.response.text,
            "exit_code": -1,
            "execution_time_ms": 0,
            "executed_at": datetime.now().isoformat(),
        }

    except Exception as e:
        error_msg = f"Failed to execute code: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # Emit failed event
        try:
            from ..streaming import create_step_event

            error_event = create_step_event(
                execution_id=execution_context.execution_id,
                step_id=step_id,
                step_status="failed",
                workflow_id=execution_context.workflow_id,
                step_type="code_execution",
                output_data={"error": error_msg},
            )
            await stream_manager.emit_execution_event(error_event)
            if execution_context.workflow_id:
                await stream_manager.emit_workflow_event(error_event)
        except Exception as emit_error:
            logger.debug(f"Failed to emit generic error event: {emit_error}")

        return {
            "success": False,
            "error": error_msg,
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "execution_time_ms": 0,
            "executed_at": datetime.now().isoformat(),
        }
