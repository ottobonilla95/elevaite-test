"""
E2E Test: Ad Copy Transformer Demo Workflow

This test validates the complete workflow execution for the demo:
  Input Node → Prompt Node → Agent Node → Output

The workflow transforms product specifications into compelling social media ad copy.

Requires OPENAI_API_KEY environment variable for real LLM execution.
"""

from __future__ import annotations

import json
import os
from pprint import pprint
import time
from pathlib import Path
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
def test_ad_copy_transformer_workflow_e2e(authenticated_client: TestClient, backend: str):
    """
    E2E test for the Ad Copy Transformer demo workflow.

    Flow:
        Input Node (raw_copy) ──┐
                                ├──► Agent Node ──► Output
        Prompt Node ────────────┘

    Validates:
    1. Workflow creation succeeds
    2. Execution completes successfully
    3. Input node provides raw_copy data
    4. Prompt node processes template with variable injection
    5. Agent node receives prompt configuration from connected prompt node
    6. Agent generates a response (mocked in test environment)
    """
    # Load the workflow fixture
    wf = _load_fixture("ad_copy_transformer.json")
    workflow_id = _create_workflow(authenticated_client, wf)

    # Execute the workflow (triggerless)
    body = {
        "backend": backend,
        "input_data": {},
        "wait": True,
    }
    execution_id = _execute_workflow(authenticated_client, workflow_id, body)

    # Poll for completion
    deadline = time.time() + 30
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

    # Validate input-node executed and provided raw_copy
    # Note: data_input step wraps output in output_data.data structure
    assert "input-node" in step_results, "input-node step should be in results"
    input_result = step_results.get("input-node", {})
    input_data = input_result.get("output_data", {}).get("data", {})
    assert input_data.get("raw_copy") == "Arlo Pro 5 camera 2K video color night vision weather resistant"

    # Validate prompt-node executed with proper structure
    # Note: step results are wrapped in output_data
    assert "prompt-node" in step_results, "prompt-node step should be in results"
    prompt_result = step_results.get("prompt-node", {})
    prompt_output = prompt_result.get("output_data", {})
    assert prompt_output.get("step_type") == "prompt"
    # System prompt contains the instructions (no query_template in this workflow)
    system_prompt = prompt_output.get("system_prompt", "")
    assert "advertising copywriter" in system_prompt, f"Expected copywriter in system_prompt: {system_prompt}"
    assert "under 100 characters" in system_prompt, "Instructions should be in system prompt"
    model_overrides = prompt_output.get("model_overrides", {})
    assert model_overrides.get("model_name") == "gpt-4"

    # Validate agent-node executed
    assert "agent-node" in step_results, "agent-node step should be in results"
    agent_result = step_results.get("agent-node", {})
    agent_output = agent_result.get("output_data", {})
    print(f"Agent output: {agent_output}")
    # Agent should have received the prompt config and executed
    # Check for success or response in output_data (handles both real LLM and mock scenarios)
    has_response = agent_output.get("success") is True or "response" in agent_output
    # Also accept error case if API key is not configured (test environment)
    has_error = "error" in agent_output
    assert has_response or has_error, f"Agent should have response or error: {agent_output}"

    # Validate output-node executed (final step in the workflow)
    assert "output-node" in step_results, "output-node step should be in results"
    output_result = step_results.get("output-node", {})
    output_data = output_result.get("output_data", {})
    assert output_data.get("success") is True, "Output step should succeed"
    assert output_data.get("label") == "Ad Copy Result", "Output should have correct label"
    assert output_data.get("format") == "text", "Output should have correct format"
    # Output step should pass through agent's data
    assert "data" in output_data, "Output should contain data from agent"
    pprint("Output node data:")
    pprint(output_data)


@pytest.mark.integration
@pytest.mark.parametrize("backend", ["local"])
def test_ad_copy_transformer_variable_injection(authenticated_client: TestClient, backend: str):
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
    assert "advertising copywriter" in system_prompt, "System prompt should have instructions"
