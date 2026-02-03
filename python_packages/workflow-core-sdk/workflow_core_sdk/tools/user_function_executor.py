"""
User Function Executor

Executes user-provided Python code in a secure sandbox.
Used for inline user_function tools where users provide both
the schema and implementation.

The function wraps user code with argument injection and calls
the Code Execution Service (Nsjail-based sandbox).
"""

import os
import json
import logging
import requests
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Environment variable for code execution service URL
CODE_EXECUTION_SERVICE_URL = os.getenv(
    "CODE_EXECUTION_SERVICE_URL", "http://localhost:8007"
)


def execute_user_function(
    code: str,
    function_name: str,
    arguments: Dict[str, Any],
    timeout_seconds: int = 30,
    memory_mb: int = 256,
) -> str:
    """
    Execute a user-provided function in a secure sandbox.

    The user's code is wrapped with:
    1. Argument injection (from the agent's tool call)
    2. Function invocation
    3. Result serialization to JSON

    Args:
        code: The user's Python code containing the function definition
        function_name: The name of the function to call
        arguments: Arguments to pass to the function (from agent's tool call)
        timeout_seconds: Maximum execution time in seconds (default: 30, max: 60)
        memory_mb: Memory limit in MB (default: 256, max: 512)

    Returns:
        A string containing the JSON-serialized return value, or error message
    """
    # Clamp timeout and memory to valid ranges
    timeout_seconds = max(1, min(timeout_seconds, 60))
    memory_mb = max(64, min(memory_mb, 512))

    # Build wrapper code that:
    # 1. Defines the user's function
    # 2. Injects arguments
    # 3. Calls the function
    # 4. Serializes the result
    wrapped_code = f"""
{code}

# --- ElevAIte Wrapper ---
import json as _json

_args = {json.dumps(arguments)}

try:
    _result = {function_name}(**_args)
    # Serialize result to JSON for transport
    if _result is None:
        print("null")
    else:
        print(_json.dumps(_result))
except Exception as _e:
    print(_json.dumps({{"error": str(_e), "type": type(_e).__name__}}))
"""

    logger.info(
        f"Executing user function '{function_name}' via code-execution-service "
        f"(timeout={timeout_seconds}s, memory={memory_mb}MB)"
    )

    try:
        response = requests.post(
            f"{CODE_EXECUTION_SERVICE_URL}/execute",
            json={
                "language": "python",
                "code": wrapped_code,
                "timeout_seconds": timeout_seconds,
                "memory_mb": memory_mb,
            },
            timeout=timeout_seconds + 10,  # HTTP timeout with buffer
        )
        response.raise_for_status()
        result = response.json()

        if result.get("success"):
            output = result.get("stdout", "").strip()
            stderr = result.get("stderr", "").strip()
            execution_time_ms = result.get("execution_time_ms", 0)

            logger.info(
                f"User function '{function_name}' executed successfully "
                f"in {execution_time_ms}ms"
            )

            # Check if output is a JSON error from the wrapper
            if output:
                try:
                    parsed = json.loads(output)
                    if isinstance(parsed, dict) and "error" in parsed:
                        return f"Function error: {parsed['error']}"
                except json.JSONDecodeError:
                    pass  # Not JSON, return as-is

            return output if output else "(No output)"
        else:
            stderr = result.get("stderr", "").strip()
            error = result.get("error", "Unknown error")
            logger.warning(f"User function execution failed: {error}")
            if stderr:
                return f"Execution failed: {error}\nStderr: {stderr}"
            return f"Execution failed: {error}"

    except requests.exceptions.Timeout:
        logger.error(f"User function execution timed out after {timeout_seconds + 10}s")
        return f"Error: Function execution timed out after {timeout_seconds} seconds"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Could not connect to code execution service: {e}")
        return (
            f"Error: Could not connect to code execution service. "
            f"Is it running at {CODE_EXECUTION_SERVICE_URL}?"
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Code execution service error: {e}")
        return f"Error: Code execution service request failed: {e}"
    except Exception as e:
        logger.error(f"Unexpected error in execute_user_function: {e}")
        return f"Error: {e}"
