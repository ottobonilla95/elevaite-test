#!/usr/bin/env python3
# E2E test script for tool_execution step

import json
import time
import uuid
from typing import Dict, Any

import requests

BASE_URL = "http://localhost:8006"
HEADERS = {"Content-Type": "application/json"}
SUFFIX = str(uuid.uuid4())[:8]

WORKFLOW_NAME = f"E2E Tool Step {SUFFIX}"


def http_post(path: str, data: Dict[str, Any], files=None):
    url = f"{BASE_URL}{path}"
    if files:
        return requests.post(url, data=data, files=files)
    return requests.post(url, headers=HEADERS, data=json.dumps(data))


def http_get(path: str):
    url = f"{BASE_URL}{path}"
    return requests.get(url)


def create_workflow(steps: list) -> Dict[str, Any]:
    payload = {
        "name": WORKFLOW_NAME,
        "description": "E2E: tool as a standalone step",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "steps": steps,
        "global_config": {},
        "tags": ["e2e", "tool"],
        "timeout_seconds": 60,
        "status": "active",
        "created_by": "e2e",
    }
    r = http_post("/workflows/", payload)
    r.raise_for_status()
    return r.json()


def execute_workflow(workflow_id: str, message: str) -> Dict[str, Any]:
    payload = {
        "payload": json.dumps(
            {
                "user_id": "e2e",
                "session_id": f"e2e-tool-{SUFFIX}",
                "organization_id": "e2e",
                "input_data": {},
                "metadata": {"source": "e2e"},
                "trigger": {
                    "kind": "chat",
                    "current_message": message,
                    "history": [{"role": "system", "content": "You are helpful."}],
                },
            }
        )
    }
    r = requests.post(f"{BASE_URL}/workflows/{workflow_id}/execute", data=payload)
    r.raise_for_status()
    exe = r.json()
    execution_id = exe["id"]

    while True:
        time.sleep(1)
        status_resp = http_get(f"/executions/{execution_id}")
        status_resp.raise_for_status()
        summary = status_resp.json()
        status = summary.get("status")
        if status in {"completed", "failed", "cancelled", "timeout"}:
            break

    res_resp = http_get(f"/executions/{execution_id}/results")
    res_resp.raise_for_status()
    results = res_resp.json()

    # Compute a final output similar to other tests
    step_results = results.get("step_results", {})
    final_output = None
    last_completed_output = None
    for _, step in (step_results or {}).items():
        if step.get("status") == "completed":
            od = step.get("output_data", {})
            last_completed_output = od
            if isinstance(od, dict):
                if "response" in od and od["response"] is not None:
                    final_output = od["response"]
    if final_output is None:
        final_output = last_completed_output if last_completed_output is not None else results

    return {"final_output": final_output, "full_results": results}


def main():
    # Workflow: trigger -> tool_execution (calculate)
    steps = [
        {
            "step_id": "trigger",
            "step_type": "trigger",
            "name": "Trigger",
            "config": {"kind": "chat", "need_history": True, "allowed_modalities": ["text"], "max_files": 0},
        },
        {
            "step_id": "tool",
            "step_type": "tool_execution",
            "name": "Calculate Tool",
            "dependencies": ["trigger"],
            "input_mapping": {"messages": "trigger"},
            "config": {
                "tool_name": "calculate",
                "param_mapping": {"expression": "messages.current_message"},
            },
        },
    ]
    wf = create_workflow(steps)

    print("Executing tool step (calculate: '2 + 3 * 7'):")
    res = execute_workflow(wf["id"], "2 + 3 * 7")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()

