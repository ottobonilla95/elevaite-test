"""
E2E test for interactive per-agent chat in workflow engine POC using API endpoints only.
"""

import asyncio
import json
import time
import uuid
import httpx

API_BASE_URL = "http://localhost:8006"


async def check_api_health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{API_BASE_URL}/health")
            return resp.status_code == 200
    except Exception:
        return False


async def create_workflow_via_api(workflow_config: dict) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{API_BASE_URL}/workflows", json=workflow_config)
        resp.raise_for_status()
        data = resp.json()
        return data["id"]


async def execute_workflow_via_api(workflow_id: str, body: dict) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{API_BASE_URL}/workflows/{workflow_id}/execute/local", json=body)
        resp.raise_for_status()
        data = resp.json()
        return data["id"]


async def get_execution_status(execution_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{API_BASE_URL}/executions/{execution_id}")
        resp.raise_for_status()
        return resp.json()


async def send_message(execution_id: str, step_id: str, role: str, content: str, metadata: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{API_BASE_URL}/executions/{execution_id}/steps/{step_id}/messages",
            json={"role": role, "content": content, "metadata": metadata or {}},
        )
        resp.raise_for_status()
        return resp.json()


async def list_messages(execution_id: str, step_id: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{API_BASE_URL}/executions/{execution_id}/steps/{step_id}/messages")
        resp.raise_for_status()
        return resp.json()


async def test_interactive_flow():
    api_up = await check_api_health()
    assert api_up, "API must be running on port 8006 for this E2E test"

    # 1) Create a workflow with two agents; first is interactive by default
    wf = {
        "name": "Interactive Test WF",
        "description": "Interactive agent then analyzer",
        "steps": [
            {
                "step_id": "agent_1",
                "step_type": "agent_execution",
                "config": {
                    "agent_name": "Research Agent",
                    "system_prompt": "You ask clarifying questions before answering.",
                    "query": "{current_message}",
                    "multi_turn": True
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
                    "interactive": False
                },
                "input_mapping": {"agent_1": "agent_1"}
            }
        ],
    }

    workflow_id = await create_workflow_via_api(wf)

    # 2) Execute workflow (local backend) with a chat trigger but no user message yet
    body = {
        "trigger": {"kind": "chat", "messages": []},
        "wait": False
    }
    execution_id = await execute_workflow_via_api(workflow_id, body)

    # 3) Poll until engine pauses (we expect status to be running or waiting)
    # Give it a moment to start
    await asyncio.sleep(1)
    status = await get_execution_status(execution_id)
    assert status["status"] in ["running", "waiting"], f"Unexpected status: {status}"

    # 4) Send a user message to agent_1 via API
    msg = await send_message(execution_id, "agent_1", "user", "I want to research AI trends in healthcare.")
    assert msg["role"] == "user"

    # 5) Wait a bit and then send final_turn message to complete step
    await asyncio.sleep(1)
    msg2 = await send_message(
        execution_id,
        "agent_1",
        "user",
        "That's enough, please proceed.",
        {"final_turn": True}
    )

    # 6) Wait for completion
    for _ in range(30):
        status = await get_execution_status(execution_id)
        if status["status"] in ["completed", "failed", "cancelled"]:
            break
        await asyncio.sleep(1)

    assert status["status"] == "completed", f"Execution did not complete: {status}"

    # 7) Verify messages persisted
    msgs = await list_messages(execution_id, "agent_1")
    assert len(msgs) >= 2


if __name__ == "__main__":
    asyncio.run(test_interactive_flow())

