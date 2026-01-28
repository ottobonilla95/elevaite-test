"""
Interactive multi-agent E2E via API using TestClient.
"""

import time
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_interactive_multi_agent_api(authenticated_client: TestClient):
    # Build workflow with a trigger and two agent steps
    wf = {
        "name": "Interactive Multi-Agent (API)",
        "description": "Agent 1 pauses for user input, Agent 2 depends on Agent 1",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "status": "active",
        "steps": [
            {
                "step_id": "trigger",
                "step_type": "trigger",
                "parameters": {
                    "kind": "chat",
                    "need_history": True,
                    "allowed_modalities": ["text"],
                },
            },
            {
                "step_id": "agent_1",
                "step_type": "agent_execution",
                "dependencies": ["trigger"],
                "config": {
                    "agent_name": "Clarifier",
                    "system_prompt": "Ask clarifying questions before answering.",
                    "query": "{current_message}",
                    "multi_turn": True,
                },
            },
            {
                "step_id": "agent_2",
                "step_type": "agent_execution",
                "dependencies": ["agent_1"],
                "config": {
                    "agent_name": "Analyzer",
                    "system_prompt": "Analyze the prior agent's output.",
                    "query": "Analyze: {agent_1}",
                    "interactive": True,
                    "multi_turn": True,
                },
                "input_mapping": {"agent_1": "agent_1"},
            },
        ],
    }

    resp = authenticated_client.post("/workflows/", json=wf)
    assert resp.status_code == 200, resp.text
    workflow_id = resp.json()["id"]

    # Execute with chat trigger and wait=false
    body = {
        "backend": "local",
        "trigger": {"kind": "chat", "messages": []},
        "wait": False,
    }
    resp = authenticated_client.post(f"/workflows/{workflow_id}/execute", json=body)
    assert resp.status_code == 200, resp.text
    execution_id = resp.json()["id"]

    # Give engine time to reach WAITING
    for _ in range(10):
        resp = authenticated_client.get(f"/executions/{execution_id}")
        assert resp.status_code == 200
        s = resp.json()
        if s.get("status") in ("waiting", "running"):
            break
        time.sleep(0.5)

    # Send user message to agent_1
    resp = authenticated_client.post(
        f"/executions/{execution_id}/steps/agent_1/messages",
        json={
            "role": "user",
            "content": "Research AI trends in healthcare",
            "metadata": {},
        },
    )
    assert resp.status_code == 200
    time.sleep(1)

    # Send final turn to complete agent_1
    resp = authenticated_client.post(
        f"/executions/{execution_id}/steps/agent_1/messages",
        json={
            "role": "user",
            "content": "That's enough, proceed.",
            "metadata": {"final_turn": True},
        },
    )
    assert resp.status_code == 200

    # Now agent_2 should pause as well; send a final message to let it complete
    resp = authenticated_client.post(
        f"/executions/{execution_id}/steps/agent_2/messages",
        json={"role": "user", "content": "Analyze now.", "metadata": {}},
    )
    assert resp.status_code == 200
    time.sleep(1)

    resp = authenticated_client.post(
        f"/executions/{execution_id}/steps/agent_2/messages",
        json={"role": "user", "content": "Finalize.", "metadata": {"final_turn": True}},
    )
    assert resp.status_code == 200

    # Wait for completion
    last_status = None
    for _ in range(60):
        resp = authenticated_client.get(f"/executions/{execution_id}")
        assert resp.status_code == 200
        last_status = resp.json()
        if last_status.get("status") in ("completed", "failed", "cancelled"):
            break
        time.sleep(1)

    assert last_status and last_status.get("status") == "completed", (
        f"Execution did not complete: {last_status}"
    )

    resp = authenticated_client.get(
        f"/executions/{execution_id}/steps/agent_1/messages"
    )
    assert resp.status_code == 200
    msgs = resp.json()
    assert len(msgs) >= 2
