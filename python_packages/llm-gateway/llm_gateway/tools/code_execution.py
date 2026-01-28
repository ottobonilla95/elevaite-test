"""
Code execution tool for LLM Gateway.

Provides a secure Python code execution implementation using the
Code Execution Service (Nsjail-based sandbox).

This tool is used by all providers that support the code_execution tool type.
"""

import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Environment variable for code execution service URL
CODE_EXECUTION_SERVICE_URL = os.getenv(
    "CODE_EXECUTION_SERVICE_URL", "http://localhost:8007"
)


def execute_python(
    code: str,
    timeout: int = 30,
    memory_mb: int = 256,
    input_data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Execute Python code in a secure sandbox and return the output.

    The code runs in an isolated Nsjail environment with limited resources.
    This function is used as the executor for the code_execution tool type
    across all LLM providers.

    Args:
        code: The Python code to execute
        timeout: Maximum execution time in seconds (default: 30, max: 60)
        memory_mb: Memory limit in MB (default: 256, max: 512)
        input_data: Optional data to pass to the sandbox (available as `input_data` variable)

    Returns:
        A string containing stdout output, or error message if execution failed
    """
    # Clamp timeout and memory to valid ranges
    timeout = max(1, min(timeout, 60))
    memory_mb = max(64, min(memory_mb, 512))

    logger.info(
        f"Executing Python code via code-execution-service (timeout={timeout}s)"
    )

    try:
        response = requests.post(
            f"{CODE_EXECUTION_SERVICE_URL}/execute",
            json={
                "language": "python",
                "code": code,
                "timeout_seconds": timeout,
                "memory_mb": memory_mb,
                "input_data": input_data,
            },
            timeout=timeout + 10,  # HTTP timeout with buffer
        )
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            output = result.get("stdout", "").strip()
            logger.info(
                f"Code executed successfully in {result.get('execution_time_ms', 0)}ms"
            )
            return output if output else "(No output)"
        else:
            stderr = result.get("stderr", "").strip()
            error = result.get("error", "Unknown error")
            logger.warning(f"Code execution failed: {error}")
            if stderr:
                return f"Execution failed: {error}\nStderr: {stderr}"
            return f"Execution failed: {error}"

    except requests.exceptions.Timeout:
        logger.error(f"Code execution timed out after {timeout + 10}s")
        return f"Error: Code execution timed out after {timeout} seconds"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to code execution service: {e}")
        return f"Error: Could not connect to code execution service. Is it running at {CODE_EXECUTION_SERVICE_URL}?"
    except requests.exceptions.RequestException as e:
        logger.error(f"Code execution service error: {e}")
        return f"Error: Code execution service request failed: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in execute_python: {e}")
        return f"Error: {e}"


# OpenAI-compatible function schema for execute_python
EXECUTE_PYTHON_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_python",
        "description": "Execute Python code in a secure sandbox. Returns stdout output, or error message if execution failed.",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The Python code to execute",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Maximum execution time in seconds (default: 30, max: 60)",
                },
            },
            "required": ["code"],
        },
    },
}
