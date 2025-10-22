"""
Interactive multi-agent E2E via API only.
Requires the workflow-engine-poc FastAPI app running on port 8006.
"""

import asyncio
import httpx

API_BASE_URL = "http://localhost:8006"


async def check_api_health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{API_BASE_URL}/api/health")
            return resp.status_code == 200
    except Exception:
        return False


async def create_workflow(config: dict) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{API_BASE_URL}/api/workflows/", json=config, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()["id"]


async def execute_workflow(workflow_id: str, body: dict) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(f"{API_BASE_URL}/api/workflows/{workflow_id}/execute/local", json=body, follow_redirects=True)
        resp.raise_for_status()
        return resp.json()["id"]


async def get_status(execution_id: str) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{API_BASE_URL}/api/executions/{execution_id}")
        resp.raise_for_status()
        return resp.json()


async def post_message(execution_id: str, step_id: str, role: str, content: str, metadata: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{API_BASE_URL}/api/executions/{execution_id}/steps/{step_id}/messages",
            json={"role": role, "content": content, "metadata": metadata or {}},
        )
        resp.raise_for_status()
        return resp.json()


async def list_messages(execution_id: str, step_id: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{API_BASE_URL}/api/executions/{execution_id}/steps/{step_id}/messages", follow_redirects=True)
        resp.raise_for_status()
        return resp.json()


async def _run_interactive_multi_agent_api():
    ok = await check_api_health()
    assert ok, "API must be running at http://localhost:8006"

    # Build workflow with a trigger and two agent steps
    wf = {
        "name": "Interactive Multi-Agent (API)",
        "description": "Agent 1 pauses for user input, Agent 2 depends on Agent 1",
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

    workflow_id = await create_workflow(wf)

    # Execute with chat trigger and wait=false
    body = {
        "trigger": {"kind": "chat", "messages": []},
        "wait": False,
    }
    execution_id = await execute_workflow(workflow_id, body)

    # Give engine time to reach WAITING
    for _ in range(10):
        s = await get_status(execution_id)
        if s.get("status") in ("waiting", "running"):
            break
        await asyncio.sleep(0.5)

    # Send user message to agent_1
    await post_message(execution_id, "agent_1", "user", "Research AI trends in healthcare")
    await asyncio.sleep(1)

    # Send final turn to complete agent_1
    await post_message(execution_id, "agent_1", "user", "That's enough, proceed.", {"final_turn": True})

    # Now agent_2 should pause as well; send a final message to let it complete
    await post_message(execution_id, "agent_2", "user", "Analyze now.")
    await asyncio.sleep(1)
    await post_message(execution_id, "agent_2", "user", "Finalize.", {"final_turn": True})

    # Wait for completion
    last_status = None
    for _ in range(60):
        last_status = await get_status(execution_id)
        if last_status.get("status") in ("completed", "failed", "cancelled"):
            break
        await asyncio.sleep(1)

    assert last_status and last_status.get("status") == "completed", f"Execution did not complete: {last_status}"

    msgs = await list_messages(execution_id, "agent_1")
    assert len(msgs) >= 2


def test_interactive_multi_agent_api():
    # Run the async scenario using asyncio.run; no pytest-asyncio needed
    asyncio.run(_run_interactive_multi_agent_api())


if __name__ == "__main__":
    asyncio.run(_run_interactive_multi_agent_api())
