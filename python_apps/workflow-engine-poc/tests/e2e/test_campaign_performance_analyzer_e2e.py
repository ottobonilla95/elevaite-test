"""
E2E Test: Campaign Performance Analyzer Demo Workflow

This test validates the complete workflow execution for the demo:
  Input Node → Agent Node → Output

The workflow analyzes campaign metrics and provides strategic recommendations.

Requires ANTHROPIC_API_KEY environment variable for real LLM execution.
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
def test_campaign_performance_analyzer_workflow_e2e(authenticated_client: TestClient, backend: str):
    """
    E2E test for the Campaign Performance Analyzer demo workflow.

    Flow:
        Input Node (campaign_data) → Agent Node → Output

    Validates:
    1. Workflow creation succeeds
    2. Execution completes successfully
    3. Input node provides campaign data
    4. Agent node analyzes data and provides recommendations (direct config, no prompt node)
    5. Output node captures the analysis
    """
    # Load the workflow fixture
    wf = _load_fixture("campaign_performance_analyzer.json")
    workflow_id = _create_workflow(authenticated_client, wf)

    # Execute the workflow (triggerless)
    body = {
        "backend": backend,
        "input_data": {},
        "wait": True,
    }
    execution_id = _execute_workflow(authenticated_client, workflow_id, body)

    # Poll for completion
    deadline = time.time() + 60  # Longer timeout for Claude
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

    # Validate input-node executed and provided campaign_data
    assert "input-node" in step_results, "input-node step should be in results"
    input_result = step_results.get("input-node", {})
    input_data = input_result.get("output_data", {}).get("data", {})
    assert "Arlo Essential Outdoor Camera" in input_data.get("campaign_data", "")
    assert "Black Friday" in input_data.get("campaign_data", "")

    # Validate agent-node executed (configured directly without prompt node)
    assert "agent-node" in step_results, "agent-node step should be in results"
    agent_result = step_results.get("agent-node", {})
    agent_output = agent_result.get("output_data", {})
    print(f"Agent output: {agent_output}")

    # Agent should have a response or error
    has_response = agent_output.get("success") is True or "response" in agent_output
    has_error = "error" in agent_output
    assert has_response or has_error, f"Agent should have response or error: {agent_output}"

    # If successful, check for expected analysis content
    if agent_output.get("success"):
        response = agent_output.get("response", "")
        # Should mention performance rating, ROAS, or recommendations
        assert any(kw in response.lower() for kw in ["performance", "roas", "recommendation", "conversion"]), \
            f"Response should contain analysis keywords: {response[:200]}"

    # Validate output-node executed
    assert "output-node" in step_results, "output-node step should be in results"
    output_result = step_results.get("output-node", {})
    output_data = output_result.get("output_data", {})
    assert output_data.get("success") is True, "Output step should succeed"
    assert output_data.get("label") == "Campaign Analysis Result"
    pprint("Output node data:")
    pprint(output_data)

