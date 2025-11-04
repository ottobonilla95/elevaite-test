"""
E2E test for interactive per-agent chat in workflow engine POC.

Uses async tests with httpx.AsyncClient for proper background task execution.
"""

import time
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
@pytest.mark.integration
async def test_interactive_flow(async_client: AsyncClient):
    # 1) Create a workflow with trigger and two agents; first is interactive by default
    wf = {
        "name": "Interactive Test WF",
        "description": "Interactive agent then analyzer",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "status": "active",
        "steps": [
            {
                "step_id": "trigger",
                "step_type": "trigger",
                "config": {
                    "kind": "chat",
                    "need_history": False,
                    "allowed_modalities": ["text"],
                },
            },
            {
                "step_id": "agent_1",
                "step_type": "agent_execution",
                "dependencies": ["trigger"],
                "config": {
                    "agent_name": "Research Agent",
                    "system_prompt": "You ask clarifying questions before answering.",
                    "query": "{current_message}",
                    "multi_turn": True,
                },
            },
            {
                "step_id": "agent_2",
                "step_type": "agent_execution",
                "dependencies": ["agent_1"],
                "config": {
                    "agent_name": "Analysis Agent",
                    "system_prompt": "Analyze prior research.",
                    "query": "Analyze: {agent_1}",
                    "interactive": False,
                },
                "input_mapping": {"agent_1": "agent_1"},
            },
        ],
    }

    resp = await async_client.post("/workflows/", json=wf)
    assert resp.status_code == 200, resp.text
    workflow_id = resp.json()["id"]

    # 2) Execute workflow (local backend) with a chat trigger but no user message yet
    body = {"backend": "local", "trigger": {"kind": "chat", "messages": []}, "wait": False}
    resp = await async_client.post(f"/workflows/{workflow_id}/execute", json=body)
    assert resp.status_code == 200, resp.text
    execution_id = resp.json()["id"]

    # 3) Poll until engine pauses (we expect status to be running or waiting)
    # Give it a moment to start
    time.sleep(1)
    resp = await async_client.get(f"/executions/{execution_id}")
    assert resp.status_code == 200
    status = resp.json()
    assert status["status"] in ["running", "waiting"], f"Unexpected status: {status}"

    # 4) Send a user message to agent_1 via API
    resp = await async_client.post(
        f"/executions/{execution_id}/steps/agent_1/messages",
        json={"role": "user", "content": "I want to research AI trends in healthcare.", "metadata": {}},
    )
    assert resp.status_code == 200
    msg = resp.json()
    assert msg["role"] == "user"

    # 5) Wait a bit and then send final_turn message to complete step
    time.sleep(1)
    resp = await async_client.post(
        f"/executions/{execution_id}/steps/agent_1/messages",
        json={"role": "user", "content": "That's enough, please proceed.", "metadata": {"final_turn": True}},
    )
    assert resp.status_code == 200

    # 6) Wait for completion
    for _ in range(30):
        resp = await async_client.get(f"/executions/{execution_id}")
        assert resp.status_code == 200
        status = resp.json()
        if status["status"] in ["completed", "failed", "cancelled"]:
            break
        time.sleep(1)

    assert status["status"] == "completed", f"Execution did not complete: {status}"

    # 7) Verify messages persisted
    resp = await async_client.get(f"/executions/{execution_id}/steps/agent_1/messages")
    assert resp.status_code == 200
    msgs = resp.json()
    assert len(msgs) >= 2
