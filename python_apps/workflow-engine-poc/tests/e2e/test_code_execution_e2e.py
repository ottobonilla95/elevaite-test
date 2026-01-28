"""
E2E test for Code Execution Sandbox integration.

Tests that an agent can use the code_execution tool to execute Python code
in the secure Nsjail sandbox via the code-execution-service.

This test runs against live Docker services:
- workflow-engine at BASE_URL (default: http://localhost:8006)
- code-execution-service (called by workflow-engine)

Configuration:
- Set BASE_URL env var to override the workflow engine URL
- Set CODE_EXEC_E2E=0 to skip this test
- Requires OPENAI_API_KEY to be set in the workflow-engine container

Usage:
    CODE_EXEC_E2E=1 uv run pytest python_apps/workflow-engine-poc/tests/e2e/test_code_execution_e2e.py -v -s
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8006")
CODE_EXEC_E2E = os.environ.get("CODE_EXEC_E2E", "0")
TIMEOUT = float(os.environ.get("CODE_EXEC_TIMEOUT", "90"))
POLL_INTERVAL = float(os.environ.get("CODE_EXEC_POLL_INTERVAL", "2"))

# Authentication headers for the workflow engine
# These can be overridden via environment variables
AUTH_HEADERS = {
    "X-Tenant-ID": os.environ.get("TEST_TENANT_ID", "default"),
    "X-elevAIte-apikey": os.environ.get(
        "TEST_API_KEY",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidHlwZSI6ImFwaV9rZXkiLCJ0ZW5hbnRfaWQiOiJkZWZhdWx0IiwiZXhwIjoyMDg0ODg3NzM3fQ.RKCTQ9YkBIzYzaMmvkuMQeywcfQ64D1vlsb8QCFjN-4",
    ),
    "X-elevAIte-OrganizationId": os.environ.get(
        "TEST_ORG_ID", "00000000-0000-0000-0000-000000000001"
    ),
    "X-elevAIte-ProjectId": os.environ.get(
        "TEST_PROJECT_ID", "00000000-0000-0000-0000-000000000001"
    ),
    "X-elevAIte-AccountId": os.environ.get(
        "TEST_ACCOUNT_ID", "00000000-0000-0000-0000-000000000001"
    ),
}


def _now_suffix() -> str:
    return str(int(time.time()))


def _http(
    method: str, path: str, json_body: Optional[Dict[str, Any]] = None
) -> httpx.Response:
    """Make HTTP request to the workflow engine."""
    if not path.startswith("/"):
        path = "/" + path
    url = BASE_URL + path
    with httpx.Client(timeout=TIMEOUT, headers=AUTH_HEADERS) as client:
        return client.request(method, url, json=json_body)


@pytest.mark.skipif(CODE_EXEC_E2E != "1", reason="CODE_EXEC_E2E not enabled")
def test_agent_with_code_execution_tool():
    """
    Test that an agent with code_execution tool can execute Python code.

    This test:
    1. Creates a workflow with an agent that has the code_execution tool
    2. Asks the agent to calculate something using Python code
    3. Verifies the agent used the tool and got the correct result
    """
    # Quick reachability check
    try:
        resp = _http("GET", "/health")
    except Exception as e:
        pytest.skip(f"Workflow engine not reachable at {BASE_URL}: {e}")
    if resp.status_code >= 500:
        pytest.skip(
            f"Workflow engine unhealthy at {BASE_URL}/health: {resp.status_code}"
        )

    suffix = _now_suffix()

    # Create workflow with code_execution tool
    workflow_payload = {
        "name": f"Code Execution E2E Test {suffix}",
        "description": "Tests agent using code execution tool",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "status": "active",
        "steps": [
            {
                "step_id": "trigger",
                "step_type": "trigger",
                "name": "Trigger",
                "config": {
                    "kind": "chat",
                    "need_history": False,
                    "allowed_modalities": ["text"],
                },
            },
            {
                "step_id": "code_agent",
                "step_type": "agent_execution",
                "name": "Code Agent",
                "dependencies": ["trigger"],
                "config": {
                    "agent_name": "Code Executor",
                    "system_prompt": (
                        "You are a helpful assistant that can execute Python code. "
                        "When asked to perform calculations or run code, use the execute_python tool. "
                        "Always use the tool for any calculations - do NOT calculate yourself."
                    ),
                    "query": "{current_message}",
                    "tools": [{"type": "code_execution"}],
                    "force_real_llm": True,
                    "interactive": False,
                },
            },
        ],
        "tags": ["e2e-test", "code-execution"],
        "timeout_seconds": 120,
    }

    # Create the workflow
    resp = _http("POST", "/workflows/", workflow_payload)
    assert resp.status_code == 200, f"Failed to create workflow: {resp.text}"
    workflow = resp.json()
    workflow_id = workflow["id"]

    try:
        # Execute workflow with a query that requires code execution
        execute_payload = {
            "user_id": "e2e-test",
            "session_id": f"code-exec-{suffix}",
            "trigger": {
                "kind": "chat",
                "current_message": (
                    "Calculate the sum of squares from 1 to 10 using Python code. Use print() to output the result."
                ),
            },
            "wait": False,
        }
        resp = _http("POST", f"/workflows/{workflow_id}/execute", execute_payload)
        assert resp.status_code == 200, f"Failed to execute workflow: {resp.text}"
        execution = resp.json()
        execution_id = execution.get("id") or execution.get("execution_id")
        assert execution_id, f"No execution ID returned: {execution}"

        # Poll for completion
        deadline = time.time() + TIMEOUT
        final_status = None
        status_data = {}
        while time.time() < deadline:
            resp = _http("GET", f"/executions/{execution_id}")
            assert resp.status_code == 200, f"Failed to get execution: {resp.text}"
            status_data = resp.json()
            final_status = status_data.get("status")

            if final_status in ("completed", "failed", "error"):
                break

            time.sleep(POLL_INTERVAL)

        # Verify execution completed
        assert final_status == "completed", (
            f"Execution did not complete. Status: {final_status}, Details: {status_data}"
        )

        # Debug: Print the full status_data to understand the structure
        import json

        print(
            f"\n=== Full status_data ===\n{json.dumps(status_data, indent=2, default=str)}\n"
        )

        # Check the results contain the expected output
        # Sum of squares from 1 to 10 = 1 + 4 + 9 + 16 + 25 + 36 + 49 + 64 + 81 + 100 = 385
        step_io_data = status_data.get("step_io_data", {})
        code_agent_result = step_io_data.get("code_agent", {})
        response_text = code_agent_result.get("response", "")

        # The response should mention 385 (the correct answer)
        assert "385" in response_text, (
            f"Expected '385' in response but got: {response_text}"
        )

        # Check that tool calls were made
        tool_calls = code_agent_result.get("tool_calls", [])
        assert len(tool_calls) > 0, "Expected at least one tool call"

        # Verify the execute_python tool was called
        tool_names = [tc.get("tool_name") for tc in tool_calls]
        assert "execute_python" in tool_names, (
            f"Expected execute_python tool to be called. Tools called: {tool_names}"
        )

    finally:
        # Clean up - delete the workflow
        _http("DELETE", f"/workflows/{workflow_id}")
