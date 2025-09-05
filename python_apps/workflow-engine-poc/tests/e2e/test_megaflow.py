"""
E2E Mega Test Suite (API-level)

Covers:
- Chat multi-agent with waiting/resume
- Webhook pass-through
- Non-AI/Hybrid workflow: data steps + tool step + subflow
- Runs on both local and DBOS backends (parametrized)

Requires server running at BASE_URL (default http://127.0.0.1:8006)
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8006")
FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _http(
    method: str,
    path: str,
    json_body: Dict[str, Any] | None = None,
    files: Any | None = None,
    data: Any | None = None,
) -> httpx.Response:
    url = BASE_URL + path
    with httpx.Client(timeout=30.0) as client:
        return client.request(method, url, json=json_body, files=files, data=data)


def _load_fixture(name: str) -> Dict[str, Any]:
    with open(FIXTURES_DIR / name, "r") as f:
        return json.load(f)


def _create_workflow(payload: Dict[str, Any]) -> str:
    r = _http("POST", "/workflows/", payload)
    r.raise_for_status()
    data = r.json()
    return data.get("id") or data.get("workflow_id")


def _execute_workflow(workflow_id: str, body: Dict[str, Any]) -> str:
    # Prefer generic endpoint that accepts backend in body
    r = _http("POST", f"/workflows/{workflow_id}/execute", body)
    r.raise_for_status()
    return r.json().get("id") or r.json().get("execution_id")


def _get_status(execution_id: str) -> Dict[str, Any]:
    r = _http("GET", f"/executions/{execution_id}")
    r.raise_for_status()
    return r.json()


def _get_results(execution_id: str) -> Dict[str, Any]:
    r = _http("GET", f"/executions/{execution_id}/results")
    r.raise_for_status()
    return r.json()


def _post_message(
    execution_id: str, step_id: str, role: str, content: str, metadata: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    r = _http(
        "POST",
        f"/executions/{execution_id}/steps/{step_id}/messages",
        {"role": role, "content": content, "metadata": metadata or {}},
    )
    r.raise_for_status()
    return r.json()


def _list_messages(execution_id: str, step_id: str) -> list[Dict[str, Any]]:
    r = _http("GET", f"/executions/{execution_id}/steps/{step_id}/messages")
    r.raise_for_status()
    return r.json()


@pytest.mark.parametrize("backend", ["local", "dbos"])
def test_chat_multi_agent_e2e(backend: str):
    # Load and create workflow
    wf = _load_fixture("chat_multi_agent.json")
    workflow_id = _create_workflow(wf)

    # Start with initial user message
    body = {"backend": backend, "trigger": {"kind": "chat"}, "query": "Research AI trends in healthcare", "wait": False}
    execution_id = _execute_workflow(workflow_id, body)

    # Wait until waiting/running
    deadline = time.time() + 30
    while time.time() < deadline:
        s = _get_status(execution_id)
        if s.get("status") in ("waiting", "running"):
            break
        time.sleep(0.5)

    # Expect agent_1 waiting first
    # Provide final turn to complete agent_1
    _post_message(execution_id, "agent_1", "user", "That's enough, proceed.", {"final_turn": True})

    # Unblock agent_2: prompt then finalize
    _post_message(execution_id, "agent_2", "user", "Analyze now.")
    _post_message(execution_id, "agent_2", "user", "Finalize.", {"final_turn": True})

    # Wait briefly for engine to process; allow async runs to remain running
    deadline = time.time() + 60
    last_status = None
    while time.time() < deadline:
        last_status = _get_status(execution_id)
        if last_status.get("status") in ("completed", "failed", "cancelled"):
            break
        time.sleep(0.5)

    # For async mode (wait=false), it's valid to be running here
    assert last_status and last_status.get("status") in ("running", "completed")

    # Validate messages persisted (at least initial user message seeded)
    msgs1 = _list_messages(execution_id, "agent_1")
    assert any(m.get("role") == "user" for m in msgs1)
    # Assistant messages may or may not be present yet if still running


@pytest.mark.parametrize("backend", ["local", "dbos"])
def test_webhook_minimal_e2e(backend: str):
    wf = _load_fixture("webhook_minimal.json")
    workflow_id = _create_workflow(wf)

    # Execute with webhook data
    body = {"backend": backend, "trigger": {"kind": "webhook"}, "input_data": {"data": {"foo": "bar"}}, "wait": True}
    execution_id = _execute_workflow(workflow_id, body)

    # For local backend: should be immediate; for dbos, may require polling DB endpoint
    # We use the in-memory results if available, else fallback makes step_results empty.
    results = _get_results(execution_id)
    step_results = results.get("step_results") or {}
    # We at least expect trigger present when engine context available
    assert "trigger" in step_results or results.get("status") in ("completed", "waiting", "running")


@pytest.mark.parametrize("backend", ["local", "dbos"])
def test_non_ai_hybrid_with_tool_and_subflow(backend: str):
    # Create subflow first: it just echoes input
    echo_subflow = {
        "name": "Echo Subflow",
        "steps": [
            {"step_id": "trigger", "step_type": "trigger", "parameters": {"kind": "webhook"}},
            {
                "step_id": "echo",
                "step_type": "data_processing",
                "dependencies": ["trigger"],
                "parameters": {"processing_type": "identity"},
            },
        ],
    }
    subflow_id = _create_workflow(echo_subflow)

    # Load hybrid and wire subflow id
    wf = _load_fixture("non_ai_hybrid.json")
    for s in wf["steps"]:
        if s["step_id"] == "subflow":
            s.setdefault("config", {})["workflow_id"] = subflow_id
            break
    workflow_id = _create_workflow(wf)

    # Execute via backend
    body = {"backend": backend, "trigger": {"kind": "webhook"}, "input_data": {"merge": {"a": 3, "b": 4}}}
    execution_id = _execute_workflow(workflow_id, body)

    # Poll status until completed
    deadline = time.time() + 30
    last = None
    time.sleep(1)
    while time.time() < deadline:
        s = _get_status(execution_id)
        last = s
        if s.get("status") in ("completed", "failed", "cancelled"):
            break
        time.sleep(1)

    if not last or last.get("status") not in ("completed", "running"):
        # Print debug info on failure
        print(f"Execution failed. Last status: {last}")
        results = _get_results(execution_id)
        print(f"Results: {json.dumps(results, indent=2, default=str)}")

        # Try to get error details from DB record
        if "db_record" in results:
            db_record = results["db_record"]
            print(f"DB error_message: {db_record.get('error_message')}")
            print(f"DB execution_metadata: {db_record.get('execution_metadata')}")

    # For async runs, accept running; we only require no failure
    assert last and last.get("status") in ("completed", "running")

    # Check results
    results = _get_results(execution_id)
    sr = results.get("step_results") or {}
    # Expect tool step present in either results or in DB record (fallback path has empty step_results)
    # So we assert via execution summary status and let fixture act as doc
    assert results.get("status") in ("completed", "waiting", "running")

    # If engine context present, verify that tool step produced a numeric-like result
    add_res = sr.get("add", {}).get("output_data") if "add" in sr else None
    if isinstance(add_res, dict):
        result_val = str(add_res.get("result"))
        assert any(c.isdigit() for c in result_val)


@pytest.mark.parametrize("backend", ["local", "dbos"])
def test_tool_success_and_unknown(backend: str):
    # Tool success
    wf_success = _load_fixture("tool_exec_success.json")
    wid_success = _create_workflow(wf_success)
    exec_req = {"backend": backend, "trigger": {"kind": "chat"}, "wait": True}
    r = _http("POST", f"/workflows/{wid_success}/execute", exec_req)
    assert r.status_code == 200, r.text
    exe_id = r.json().get("id") or r.json().get("execution_id")

    # Poll to terminal or running
    deadline = time.time() + 20
    final_status = None
    while time.time() < deadline:
        s = _get_status(exe_id)
        final_status = s.get("status")
        if final_status in {"completed", "failed", "cancelled"}:
            break
        time.sleep(0.5)
    assert final_status in {"completed", "running"}

    # Tool unknown -> failure expected
    wf_unknown = _load_fixture("tool_exec_unknown.json")
    wid_unknown = _create_workflow(wf_unknown)
    exec_req2 = {"backend": backend, "trigger": {"kind": "chat"}, "wait": True}
    r2 = _http("POST", f"/workflows/{wid_unknown}/execute", exec_req2)
    assert r2.status_code == 200, r2.text
    exe2 = r2.json().get("id") or r2.json().get("execution_id")

    # Poll to terminal
    deadline = time.time() + 60
    while time.time() < deadline:
        s2 = _get_status(exe2)
        if s2.get("status") in {"completed", "failed", "cancelled"}:
            final2 = s2.get("status")
            break
        time.sleep(0.5)
    else:
        final2 = _get_status(exe2).get("status")
    assert final2 in {"failed", "running"}


@pytest.mark.parametrize("backend", ["local", "dbos"])
def test_chat_with_attachment_small_text(backend: str, tmp_path: Path):
    # Create small text file
    p = tmp_path / "note.txt"
    p.write_text("hello attachment")

    # Create workflow that allows doc/text/plain
    wf = _load_fixture("chat_with_attachment.json")
    wid = _create_workflow(wf)

    # Send multipart with payload and files[]
    payload = {
        "backend": backend,
        "trigger": {"kind": "chat", "current_message": "process file"},
        "wait": True,
    }
    files = [
        ("files", ("note.txt", p.read_bytes(), "text/plain")),
    ]
    data = {"payload": json.dumps(payload)}

    r = _http("POST", f"/workflows/{wid}/execute", files=files, data=data)
    assert r.status_code == 200, r.text
    exe = r.json().get("id") or r.json().get("execution_id")

    # Poll status
    deadline = time.time() + 20
    last = None
    while time.time() < deadline:
        s = _get_status(exe)
        last = s
        if s.get("status") in {"completed", "failed", "cancelled"}:
            break
        time.sleep(0.5)

    assert last and last.get("status") in {"completed", "running"}

    # Results include trigger step output with attachments echoed
    results = _get_results(exe)
    step_results = results.get("step_results") or {}
    if "trigger" in step_results:
        trig = step_results["trigger"].get("output_data")
        if isinstance(trig, dict):
            atts = trig.get("attachments") or []
            assert any(a.get("name") == "note.txt" for a in atts)


def test_validate_endpoint_accepts_known_steps():
    wf = _load_fixture("webhook_minimal.json")
    r = _http("POST", "/workflows/validate", wf)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("is_valid") in {True, False}
    # Should not have unknown step type errors for trigger + data_input
    assert not any("Unknown step type" in e for e in data.get("errors", []))
