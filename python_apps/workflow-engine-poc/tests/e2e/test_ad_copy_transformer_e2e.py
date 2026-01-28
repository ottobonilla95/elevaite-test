"""
E2E Test: Ad Copy Transformer Demo Workflow (Live Server)

This test validates the complete workflow execution against a LIVE server:
  Input Node → Prompt Node → Agent Node → Output

The workflow transforms product specifications into compelling social media ad copy.

How to run:
- Start the workflow-engine-poc FastAPI server (default http://127.0.0.1:8006)
- Set SMOKE_DBOS=1 to enable this test
- Optionally set BASE_URL to override the default server URL

Example:
  SMOKE_DBOS=1 BASE_URL=http://127.0.0.1:8006 pytest tests/e2e/test_ad_copy_transformer_e2e.py -v -s
"""

from __future__ import annotations

import json
import os
from pprint import pprint
import time
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8006")
SMOKE_DBOS = os.environ.get("SMOKE_DBOS", "0")
TIMEOUT = float(os.environ.get("SMOKE_TIMEOUT", "60"))

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _http(
    method: str, path: str, json_body: Optional[Dict[str, Any]] = None
) -> httpx.Response:
    if not path.startswith("/"):
        path = "/" + path
    url = BASE_URL + path
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.request(method, url, json=json_body)


def _load_fixture(name: str) -> Dict[str, Any]:
    with open(FIXTURES_DIR / name, "r") as f:
        return json.load(f)


def _create_workflow(payload: Dict[str, Any]) -> str:
    r = _http("POST", "/workflows/", payload)
    assert r.status_code == 200, f"Failed to create workflow: {r.text}"
    data = r.json()
    return data.get("id") or data.get("workflow_id")


def _execute_workflow(workflow_id: str, body: Dict[str, Any]) -> str:
    r = _http("POST", f"/workflows/{workflow_id}/execute", body)
    assert r.status_code == 200, f"Failed to execute workflow: {r.text}"
    return r.json().get("id") or r.json().get("execution_id")


def _get_status(execution_id: str) -> Dict[str, Any]:
    r = _http("GET", f"/executions/{execution_id}")
    assert r.status_code == 200, f"Failed to get status: {r.text}"
    return r.json()


def _get_results(execution_id: str) -> Dict[str, Any]:
    r = _http("GET", f"/executions/{execution_id}/results")
    assert r.status_code == 200, f"Failed to get results: {r.text}"
    return r.json()


def _check_server():
    """Check if live server is reachable."""
    try:
        r = _http("GET", "/health")
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(
    SMOKE_DBOS != "1", reason="SMOKE_DBOS=1 required for live server tests"
)
@pytest.mark.parametrize("backend", ["dbos"])
def test_ad_copy_transformer_workflow_e2e(backend: str):
    """
    E2E test for the Ad Copy Transformer demo workflow against live DBOS server.

    Flow:
        Input Node (raw_copy) ──┐
                                ├──► Agent Node ──► Output
        Prompt Node ────────────┘

    Validates:
    1. Workflow creation succeeds
    2. Execution completes successfully with DBOS backend
    3. Input node provides raw_copy data
    4. Prompt node processes template with variable injection
    5. Agent node receives prompt configuration from connected prompt node
    6. Agent generates a response via real LLM
    """
    if not _check_server():
        pytest.skip(f"Server not reachable at {BASE_URL}")

    # Load the workflow fixture
    wf = _load_fixture("ad_copy_transformer.json")
    workflow_id = _create_workflow(wf)

    # Execute the workflow with DBOS backend
    body = {
        "backend": backend,
        "input_data": {},
        "wait": True,
    }
    execution_id = _execute_workflow(workflow_id, body)

    # Poll for completion
    deadline = time.time() + 60
    last_status = None
    while time.time() < deadline:
        status_response = _get_status(execution_id)
        last_status = status_response.get("status")
        if last_status in ("completed", "failed", "cancelled"):
            break
        time.sleep(0.5)

    # Get results - step_results now has parity between local and DBOS
    results = _get_results(execution_id)
    step_results = results.get("step_results", {})

    # Debug output
    print(f"Execution status: {last_status}")
    print(f"Step results keys: {list(step_results.keys())}")

    # Debug output if failed
    if last_status == "failed":
        print(
            f"Execution failed. Results: {json.dumps(results, indent=2, default=str)}"
        )

    # Validate execution completed
    assert last_status == "completed", f"Expected completed, got {last_status}"

    # Validate input-node executed and provided raw_copy
    assert "input-node" in step_results, "input-node step should be in results"
    input_output = step_results.get("input-node", {}).get("output_data", {})
    assert (
        input_output.get("data", {}).get("raw_copy")
        == "Arlo Pro 5 camera 2K video color night vision weather resistant"
    )

    # Validate prompt-node executed with proper structure
    assert "prompt-node" in step_results, "prompt-node step should be in results"
    prompt_output = step_results.get("prompt-node", {}).get("output_data", {})
    assert prompt_output.get("step_type") == "prompt"
    system_prompt = prompt_output.get("system_prompt", "")
    assert "advertising copywriter" in system_prompt, (
        f"Expected copywriter in system_prompt: {system_prompt}"
    )
    assert "under 100 characters" in system_prompt, (
        "Instructions should be in system prompt"
    )
    model_overrides = prompt_output.get("model_overrides", {})
    assert model_overrides.get("model_name") == "gpt-5.2"

    # Validate agent-node executed
    assert "agent-node" in step_results, "agent-node step should be in results"
    agent_output = step_results.get("agent-node", {}).get("output_data", {})
    print(f"Agent output: {agent_output}")
    assert agent_output.get("success") is True, f"Agent should succeed: {agent_output}"
    assert "response" in agent_output, f"Agent should have response: {agent_output}"

    # Validate output-node executed (final step in the workflow)
    assert "output-node" in step_results, "output-node step should be in results"
    output_data = step_results.get("output-node", {}).get("output_data", {})
    assert output_data.get("success") is True, "Output step should succeed"
    assert output_data.get("label") == "Ad Copy Result", (
        "Output should have correct label"
    )
    assert output_data.get("format") == "text", "Output should have correct format"
    assert "data" in output_data, "Output should contain data from agent"
    pprint("Output node data:")
    pprint(output_data)


@pytest.mark.integration
@pytest.mark.parametrize("backend", ["local"])
def test_ad_copy_transformer_variable_injection(
    authenticated_client: TestClient, backend: str
):
    """
    Verify that the agent node correctly injects the input data as the query.

    This tests the core variable injection feature:
    {{input-node.data.raw_copy}} in agent query config should be replaced with actual product specs.
    """
    wf = _load_fixture("ad_copy_transformer.json")
    workflow_id = _create_workflow(authenticated_client, wf)

    body = {
        "backend": backend,
        "input_data": {},
        "wait": True,
    }
    execution_id = _execute_workflow(authenticated_client, workflow_id, body)

    # Wait for completion
    deadline = time.time() + 30
    while time.time() < deadline:
        status = _get_status(authenticated_client, execution_id)
        if status.get("status") in ("completed", "failed"):
            break
        time.sleep(0.5)

    results = _get_results(authenticated_client, execution_id)
    step_results = results.get("step_results") or {}

    # Verify agent received the input data as the query
    agent_result = step_results.get("agent-node", {})
    agent_output = agent_result.get("output_data", {})
    query = agent_output.get("query", "")

    # The {{input-node.data.raw_copy}} should have been replaced with actual product specs
    assert "{{" not in query, "Variable should be injected"
    assert "Arlo Pro 5" in query, "Product name should be in query"
    assert "2K video" in query, "Product specs should be in query"
    assert "color night vision" in query, "Product specs should be in query"

    # Verify the prompt step provided system prompt to agent
    prompt_result = step_results.get("prompt-node", {})
    prompt_output = prompt_result.get("output_data", {})
    system_prompt = prompt_output.get("system_prompt", "")
    assert "advertising copywriter" in system_prompt, (
        "System prompt should have instructions"
    )
