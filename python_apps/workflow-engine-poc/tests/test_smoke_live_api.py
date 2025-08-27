"""
Live API smoke test for workflow-engine-poc

This test exercises the running FastAPI server via HTTP:
- Create a Prompt
- Create an Agent linked to that Prompt
- Create a Workflow (trigger + agent_execution)
- Execute the Workflow
- Poll execution status until completion
- Clean up created resources

Configuration:
- Set BASE_URL env var to override the default (http://127.0.0.1:8006)
- Set SMOKE_API=0 to skip this test (useful in CI without a running server)
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8006")
SMOKE_API = os.environ.get("SMOKE_API", "1")
TIMEOUT = float(os.environ.get("SMOKE_TIMEOUT", "25"))
POLL_INTERVAL = float(os.environ.get("SMOKE_POLL_INTERVAL", "0.5"))


def _now_suffix() -> str:
    return str(int(time.time()))


def _http(method: str, path: str, json_body: Optional[Dict[str, Any]] = None) -> httpx.Response:
    url = BASE_URL + path
    with httpx.Client(timeout=TIMEOUT) as client:
        resp = client.request(method, url, json=json_body)
        return resp


@pytest.mark.skipif(SMOKE_API != "1", reason="SMOKE_API disabled")
def test_smoke_live_api_end_to_end():
    # Quick reachability check
    try:
        resp = _http("GET", "/health")
    except Exception as e:  # pragma: no cover - only for live env issues
        pytest.skip(f"Server not reachable at {BASE_URL}: {e}")
    if resp.status_code >= 500:  # pragma: no cover
        pytest.skip(f"Server unhealthy at {BASE_URL}/health: {resp.status_code}")

    suffix = _now_suffix()

    # 1) Create Prompt
    prompt_payload = {
        "prompt_label": f"Smoke Prompt {suffix}",
        "prompt": "You are a helpful assistant.",
        "unique_label": f"smoke_prompt_{suffix}",
        "app_name": "workflow-engine-poc",
        "ai_model_provider": "openai",
        "ai_model_name": "gpt-4o",
        "tags": ["smoke"],
        "hyper_parameters": {},
        "variables": {},
        "organization_id": "smoke",
        "created_by": "smoke",
    }
    r = _http("POST", "/prompts/", prompt_payload)
    assert r.status_code == 200, r.text
    prompt = r.json()
    prompt_id = prompt["id"]

    # 2) Create Agent
    agent_payload = {
        "name": f"Smoke Agent {suffix}",
        "description": "Smoke test agent",
        "system_prompt_id": prompt_id,
        "provider_type": "openai_textgen",
        "provider_config": {"model_name": "gpt-4o", "temperature": 0.2, "max_tokens": 64},
        "tags": ["smoke"],
        "status": "active",
        "organization_id": "smoke",
        "created_by": "smoke",
    }
    r = _http("POST", "/agents/", agent_payload)
    assert r.status_code == 200, r.text
    agent = r.json()
    agent_id = agent["id"]

    # 3) Create Workflow (trigger + agent_execution)
    steps = [
        {
            "step_id": "trigger",
            "step_type": "trigger",
            "name": "Trigger",
            "config": {"kind": "chat", "need_history": False, "allowed_modalities": ["text"], "max_files": 0},
        },
        {
            "step_id": "agent",
            "step_type": "agent_execution",
            "name": "Agent Exec",
            "dependencies": ["trigger"],
            "config": {
                "agent_name": agent.get("name", "Agent"),
                "system_prompt": prompt.get("prompt", "You are a helpful assistant."),
                "query": "Say hello to the world.",
                "tools": [],
                "force_real_llm": False,
            },
        },
    ]
    workflow_payload = {
        "name": f"Smoke Workflow {suffix}",
        "description": "Smoke test workflow",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "steps": steps,
        "global_config": {},
        "tags": ["smoke"],
        "timeout_seconds": 30,
        "status": "active",
        "created_by": "smoke",
    }
    r = _http("POST", "/workflows/", workflow_payload)
    assert r.status_code == 200, r.text
    workflow = r.json()
    workflow_id = workflow["id"]

    # 4) Execute Workflow
    exec_req = {
        "user_id": "smoke",
        "session_id": f"smoke-{suffix}",
        "organization_id": "smoke",
        "input_data": {"foo": "bar"},
        "metadata": {"source": "smoke-test"},
        "trigger": {"kind": "chat", "current_message": "hello"},
    }
    r = _http("POST", f"/workflows/{workflow_id}/execute", exec_req)
    assert r.status_code == 200, r.text
    execution = r.json()
    execution_id = execution.get("id") or execution.get("execution_id")
    assert execution_id, execution

    # 5) Poll status until completion
    deadline = time.time() + TIMEOUT
    last = None
    while time.time() < deadline:
        r = _http("GET", f"/executions/{execution_id}")
        assert r.status_code == 200, r.text
        last = r.json()
        st = last.get("status")
        if st and st.lower() in ("completed", "failed", "cancelled"):
            break
        time.sleep(POLL_INTERVAL)

    assert isinstance(last, dict), last
    assert last.get("status") == "completed", json.dumps(last, indent=2)
    print(last)

    # Cleanup: best-effort deletes (don't fail test if they error)
    try:
        _http("DELETE", f"/agents/{agent_id}")
    except Exception:
        pass
    try:
        _http("DELETE", f"/prompts/{prompt_id}")
    except Exception:
        pass
    try:
        _http("DELETE", f"/workflows/{workflow_id}")
    except Exception:
        pass
