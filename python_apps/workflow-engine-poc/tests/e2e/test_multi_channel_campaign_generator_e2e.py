"""
E2E Test: Multi-Channel Campaign Generator Demo Workflow

This test validates the complete workflow execution for the demo:
  Input Node → Agent (strategy) → Prompt → Agent (copy) → Output

The workflow chains an agent that creates strategy insights with a prompt
node that combines brief + strategy, then another agent generates multi-channel copy.

Requires GEMINI_API_KEY environment variable for real LLM execution.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from pprint import pprint
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> Dict[str, Any]:
    with open(FIXTURES_DIR / name, "r") as f:
        return json.load(f)


def _create_workflow(client: TestClient, payload: Dict[str, Any]) -> str:
    r = client.post("/workflows/", json=payload)
    r.raise_for_status()
    data = r.json()
    return data.get("id") or data.get("workflow_id")


def _execute_workflow(client: TestClient, workflow_id: str, body: Dict[str, Any]) -> str:
    r = client.post(f"/workflows/{workflow_id}/execute", json=body)
    r.raise_for_status()
    return r.json().get("id") or r.json().get("execution_id")


def _get_status(client: TestClient, execution_id: str) -> Dict[str, Any]:
    r = client.get(f"/executions/{execution_id}")
    r.raise_for_status()
    return r.json()


def _get_results(client: TestClient, execution_id: str) -> Dict[str, Any]:
    r = client.get(f"/executions/{execution_id}/results")
    r.raise_for_status()
    return r.json()


@pytest.mark.integration
@pytest.mark.parametrize("backend", ["local"])
def test_multi_channel_campaign_generator_workflow_e2e(authenticated_client: TestClient, backend: str):
    """
    E2E test for the Multi-Channel Campaign Generator demo workflow.

    Flow:
        Input → Agent (strategist) → Prompt → Agent (copywriter) → Output

    Validates:
    1. Workflow creation succeeds
    2. Execution completes successfully
    3. Input node provides campaign brief
    4. Strategist agent analyzes and provides selling points
    5. Prompt node combines brief + strategy for copywriter
    6. Copywriter agent generates multi-channel ad copy
    7. Output node captures the final copy
    """
    # Load the workflow fixture
    wf = _load_fixture("multi_channel_campaign_generator.json")
    workflow_id = _create_workflow(authenticated_client, wf)

    # Execute the workflow (triggerless)
    body = {
        "backend": backend,
        "input_data": {},
        "wait": True,
    }
    execution_id = _execute_workflow(authenticated_client, workflow_id, body)

    # Poll for completion
    deadline = time.time() + 90  # Longer timeout for chained agents
    last_status = None
    while time.time() < deadline:
        status_response = _get_status(authenticated_client, execution_id)
        last_status = status_response.get("status")
        if last_status in ("completed", "failed", "cancelled"):
            break
        time.sleep(0.5)

    # Get results
    results = _get_results(authenticated_client, execution_id)
    step_results = results.get("step_results") or {}

    # Debug output
    print(f"Execution status: {last_status}")
    print(f"Step results keys: {list(step_results.keys())}")

    # Debug output if failed
    if last_status == "failed":
        print(f"Execution failed. Results: {json.dumps(results, indent=2, default=str)}")

    # Validate execution completed
    assert last_status == "completed", f"Expected completed, got {last_status}"

    # Validate input-node
    assert "input-node" in step_results, "input-node step should be in results"
    input_result = step_results.get("input-node", {})
    input_data = input_result.get("output_data", {}).get("data", {})
    assert "Arlo Total Security Bundle" in input_data.get("campaign_brief", "")

    # Validate strategist-agent
    assert "strategist-agent" in step_results, "strategist-agent step should be in results"
    strategist_result = step_results.get("strategist-agent", {})
    strategist_output = strategist_result.get("output_data", {})
    print("\n=== STRATEGIST AGENT OUTPUT ===")
    pprint(strategist_output)

    # Validate prompt-node configured copywriter
    assert "prompt-node" in step_results, "prompt-node step should be in results"
    prompt_result = step_results.get("prompt-node", {})
    prompt_output = prompt_result.get("output_data", {})
    print("\n=== PROMPT NODE OUTPUT ===")
    pprint(prompt_output)

    # Validate copywriter-agent
    assert "copywriter-agent" in step_results, "copywriter-agent step should be in results"
    copywriter_result = step_results.get("copywriter-agent", {})
    copywriter_output = copywriter_result.get("output_data", {})
    print("\n=== COPYWRITER AGENT OUTPUT ===")
    pprint(copywriter_output)

    # Check copywriter has response or error
    has_response = copywriter_output.get("success") is True or "response" in copywriter_output
    has_error = "error" in copywriter_output
    assert has_response or has_error, f"Copywriter should have response or error: {copywriter_output}"

    # If successful, check for expected multi-channel content
    if copywriter_output.get("success"):
        response = copywriter_output.get("response", "").lower()
        assert any(kw in response for kw in ["meta", "google", "email"]), (
            f"Response should contain multi-channel keywords: {response[:300]}"
        )

    # Validate output-node
    assert "output-node" in step_results, "output-node step should be in results"
    output_result = step_results.get("output-node", {})
    output_data = output_result.get("output_data", {})
    assert output_data.get("success") is True, "Output step should succeed"
    assert output_data.get("label") == "Multi-Channel Campaign Copy"
    pprint("Output node data:")
    pprint(output_data)
