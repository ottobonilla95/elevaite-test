"""
E2E tests for human_approval step (local + DBOS)

Uses TestClient for testing without requiring a live server.
"""

from __future__ import annotations

import time
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient

try:
    import dbos  # type: ignore

    HAS_DBOS = True
except Exception:
    HAS_DBOS = False

POLL_INTERVAL = 0.5  # Faster polling for tests


def _now_suffix() -> str:
    return str(int(time.time()))


@pytest.mark.integration
def test_local_human_approval_flow(authenticated_client: TestClient):
    suffix = _now_suffix()

    # Create workflow: trigger -> human_approval -> data_input
    steps = [
        {
            "step_id": "trigger",
            "step_type": "trigger",
            "name": "Trigger",
            "parameters": {"kind": "chat"},
        },
        {
            "step_id": "approval",
            "step_type": "human_approval",
            "name": "Approval",
            "parameters": {"prompt": "Proceed?"},
            "dependencies": ["trigger"],
        },
        {
            "step_id": "store_on_approved",
            "step_type": "data_input",
            "name": "Store",
            "parameters": {"input_type": "static", "data": {"stored": True}},
            "dependencies": ["approval"],
            "conditions": "approval.output.decision == 'approved'",
        },
        {
            "step_id": "archive_on_denied",
            "step_type": "data_input",
            "name": "Archive",
            "parameters": {"input_type": "static", "data": {"archived": True}},
            "dependencies": ["approval"],
            "conditions": "approval.output.decision == 'denied'",
        },
    ]

    payload = {
        "name": f"E2E Local Approval {suffix}",
        "description": "Approval E2E",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "steps": steps,
        "global_config": {},
        "tags": ["e2e", "approvals"],
        "status": "active",
        "created_by": "tests",
    }
    r = authenticated_client.post("/workflows/", json=payload)
    assert r.status_code == 200, r.text
    wf = r.json()
    workflow_id = wf["id"]

    # Execute with local backend
    exec_req = {
        "backend": "local",
        "user_id": "e2e",
        "session_id": f"sess-{suffix}",
        "organization_id": "tests",
        "trigger": {"kind": "chat", "current_message": "start"},
    }
    r = authenticated_client.post(f"/workflows/{workflow_id}/execute", json=exec_req)
    assert r.status_code == 200, r.text
    exe = r.json()
    execution_id = str(exe["id"]) if isinstance(exe["id"], str) else exe["id"]

    # Poll approvals list until one appears
    approval_id = None
    for _ in range(40):
        time.sleep(POLL_INTERVAL)
        lr = authenticated_client.get(f"/approvals?execution_id={execution_id}")
        assert lr.status_code == 200
        items = lr.json()
        if items:
            approval_id = items[0]["id"]
            break
    assert approval_id, "Approval request not created"

    # Approve it
    ar = authenticated_client.post(
        f"/approvals/{approval_id}/approve", json={"payload": {"note": "ok"}, "decided_by": "tester"}
    )
    assert ar.status_code == 200, ar.text

    # Poll execution to completion
    for _ in range(60):
        time.sleep(POLL_INTERVAL)
        sr = authenticated_client.get(f"/executions/{execution_id}")
        assert sr.status_code == 200
        status = sr.json().get("status")
        if status in {"completed", "failed", "cancelled"}:
            break
    assert status == "completed", f"Unexpected final status: {status}"


@pytest.mark.integration
@pytest.mark.skipif(not HAS_DBOS, reason="DBOS package not available")
def test_dbos_human_approval_flow(authenticated_client: TestClient):
    suffix = _now_suffix()

    # Same workflow but will run under DBOS backend
    steps = [
        {
            "step_id": "trigger",
            "step_type": "trigger",
            "name": "Trigger",
            "parameters": {"kind": "chat"},
        },
        {
            "step_id": "approval",
            "step_type": "human_approval",
            "name": "Approval",
            "parameters": {"prompt": "Proceed?", "timeout_seconds": 2},
            "dependencies": ["trigger"],
        },
        {
            "step_id": "store_on_approved",
            "step_type": "data_input",
            "name": "Store",
            "parameters": {"input_type": "static", "data": {"stored": True}},
            "dependencies": ["approval"],
            "conditions": "approval.output.decision == 'approved'",
        },
        {
            "step_id": "archive_on_denied",
            "step_type": "data_input",
            "name": "Archive",
            "parameters": {"input_type": "static", "data": {"archived": True}},
            "dependencies": ["approval"],
            "conditions": "approval.output.decision == 'denied'",
        },
    ]
    payload = {
        "name": f"E2E DBOS Approval {suffix}",
        "description": "Approval E2E DBOS",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "steps": steps,
        "global_config": {},
        "tags": ["e2e", "approvals", "dbos"],
        "status": "active",
        "created_by": "tests",
    }
    r = authenticated_client.post("/workflows/", json=payload)
    assert r.status_code == 200, r.text
    wf = r.json()
    workflow_id = wf["id"]

    exec_req = {
        "backend": "dbos",
        "user_id": "e2e",
        "session_id": f"sess-{suffix}",
        "organization_id": "tests",
        "trigger": {"kind": "chat", "current_message": "start"},
    }
    r = authenticated_client.post(f"/workflows/{workflow_id}/execute", json=exec_req)
    assert r.status_code == 200, r.text
    # In DBOS path, the endpoint currently waits to completion; with timeout, the step may return WAITING
    # Sleep briefly, then approve

    # Poll approvals list until one appears
    execution_id = r.json()["id"] if "id" in r.json() else r.json()["execution_id"]
    assert execution_id, r.json()
    approval_id = None
    for _ in range(40):
        time.sleep(POLL_INTERVAL)
        lr = authenticated_client.get(f"/approvals?execution_id={execution_id}")
        assert lr.status_code == 200
        items = lr.json()
        if items:
            approval_id = items[0]["id"]
            break
    assert approval_id, "Approval request not created (dbos)"

    # Approve it (this will call DBOS.set_event)
    ar = authenticated_client.post(
        f"/approvals/{approval_id}/approve", json={"payload": {"note": "ok"}, "decided_by": "tester"}
    )
    assert ar.status_code == 200, ar.text
