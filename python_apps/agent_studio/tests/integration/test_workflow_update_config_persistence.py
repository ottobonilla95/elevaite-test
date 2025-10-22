import uuid
from typing import Any, Dict, List, Optional

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_workflow_update_persists_tool_step_config(test_client: TestClient) -> None:
    """
    Verify that sending a frontend-style update payload (with configuration.agents/connections)
    persists per-step config under configuration.steps[].config after the PUT /api/workflows/{id}.
    """
    # 1) Create a minimal workflow first to obtain an ID
    create_payload: Dict[str, Any] = {
        "name": f"Initial Workflow {uuid.uuid4().hex[:8]}",
        "configuration": {"steps": []},
    }
    create_resp = test_client.post("/api/workflows/", json=create_payload)
    assert create_resp.status_code == 200, create_resp.text
    workflow_id = create_resp.json()["workflow_id"]

    # 2) Create a real prompt and agent so ResponseAdapter can populate workflow_agents without schema errors
    prompt_payload = {
        "prompt_label": "Test Agent Prompt",
        "prompt": "You are a helpful test agent.",
        "unique_label": f"AgentPrompt_{uuid.uuid4().hex[:8]}",
        "app_name": "test_app",
        "version": "1.0.0",
        "ai_model_provider": "openai",
        "ai_model_name": "gpt-4o-mini",
    }
    prompt_resp = test_client.post("/api/prompts/", json=prompt_payload)
    assert prompt_resp.status_code == 200, prompt_resp.text
    prompt_pid = prompt_resp.json()["pid"]

    agent_payload = {
        "name": f"Router Agent {uuid.uuid4().hex[:8]}",
        "agent_type": "router",
        "description": "Router agent for update test",
        "system_prompt_id": prompt_pid,
        "routing_options": {},
        "functions": [],
    }
    agent_resp = test_client.post("/api/agents/", json=agent_payload)
    assert agent_resp.status_code == 200, agent_resp.text
    created_agent_id = agent_resp.json()["agent_id"]

    # Create a second agent to satisfy schema for the tool node in workflow_agents
    tool_agent_payload = {
        "name": f"Tool Surrogate {uuid.uuid4().hex[:8]}",
        "agent_type": "router",
        "description": "Tool surrogate agent",
        "system_prompt_id": prompt_pid,
        "routing_options": {},
        "functions": [],
    }
    tool_agent_resp = test_client.post("/api/agents/", json=tool_agent_payload)
    assert tool_agent_resp.status_code == 200, tool_agent_resp.text
    tool_agent_id = tool_agent_resp.json()["agent_id"]

    # 3) Update with the real frontend-captured payload, substituting the real agent IDs
    update_payload: Dict[str, Any] = {
        "name": "Numbers Test",
        "description": "Numbers Test",
        "tags": ["test"],
        "configuration": {
            "agents": [
                {
                    "node_type": "agent",
                    "agent_id": created_agent_id,
                    "agent_type": "router",
                    "prompt": 'Give me two random numbers between 1 and 100. Respond in the format {"number_a": <FIRST NUMBER>, "number_b":<SECOND_NUMBER>}',
                    "tools": [],
                    "tags": ["router"],
                    "position": {"x": 2415, "y": 90},
                },
                {
                    "node_type": "tool",
                    "agent_id": tool_agent_id,
                    "agent_type": "local",
                    "position": {"x": 2415, "y": 375},
                    "config": {
                        "step_label": "T1",
                        "step_description": "TD",
                        "a": "123",
                        "b": "456",
                    },
                },
            ],
            "connections": [
                {
                    "source_agent_id": created_agent_id,
                    "target_agent_id": tool_agent_id,
                    "connection_type": "default",
                },
                {
                    "source_agent_id": created_agent_id,
                    "target_agent_id": tool_agent_id,
                    "connection_type": "default",
                },
            ],
        },
    }

    update_resp = test_client.put(f"/api/workflows/{workflow_id}", json=update_payload)
    assert update_resp.status_code == 200, update_resp.text
    updated = update_resp.json()

    # 3) Validate top-level fields updated
    assert updated["name"] == "Numbers Test"
    assert updated["description"] == "Numbers Test"
    assert "test" in (updated.get("tags") or [])

    # 4) Validate configuration.agents contains the tool node and that config persisted
    agents: List[Dict[str, Any]] = updated["configuration"]["agents"]
    assert any(a.get("node_type") == "tool" for a in agents)

    # Find the tool node by its agent_id
    tool_node: Optional[Dict[str, Any]] = next(
        (a for a in agents if a.get("node_type") == "tool" and a.get("agent_id") == tool_agent_id),
        None,
    )
    assert tool_node is not None, f"tool node not found in agents: {agents}"

    cfg = tool_node.get("config", {})
    # Core assertion: the custom keys from the frontend request are persisted
    assert cfg.get("a") == "123"
    assert cfg.get("b") == "456"
    # And the optional metadata we preserve inside config
    assert cfg.get("step_label") == "T1"
    assert cfg.get("step_description") == "TD"

    # 5) GET again to ensure the values were actually persisted in the DB
    get_resp = test_client.get(f"/api/workflows/{workflow_id}")
    assert get_resp.status_code == 200, get_resp.text
    got = get_resp.json()

    agents2: List[Dict[str, Any]] = got["configuration"]["agents"]
    tool_node2: Optional[Dict[str, Any]] = next(
        (a for a in agents2 if a.get("node_type") == "tool" and a.get("agent_id") == tool_agent_id),
        None,
    )
    assert tool_node2 is not None
    cfg2 = tool_node2.get("config", {})
    assert cfg2.get("a") == "123"
    assert cfg2.get("b") == "456"
    assert cfg2.get("step_label") == "T1"
    assert cfg2.get("step_description") == "TD"
