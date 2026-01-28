#!/usr/bin/env python3
# E2E test script for subflow steps:
# - Creates a small subflow workflow (uppercase transform)
# - Creates a parent workflow with trigger and a subflow step referencing the subflow
# - Executes the parent workflow and prints full results (including subflow output)

import json
import time
import uuid
from typing import Dict, Any

import requests

BASE_URL = "http://localhost:8006"
HEADERS = {"Content-Type": "application/json"}
SUFFIX = str(uuid.uuid4())[:8]

PARENT_WORKFLOW_NAME = f"E2E Subflow Parent {SUFFIX}"
SUBFLOW_WORKFLOW_NAME = f"E2E Subflow Uppercase {SUFFIX}"


def http_post(path: str, data: Dict[str, Any], files=None):
    url = f"{BASE_URL}{path}"
    if files:
        return requests.post(url, data=data, files=files)
    return requests.post(url, headers=HEADERS, data=json.dumps(data))


def http_get(path: str):
    url = f"{BASE_URL}{path}"
    return requests.get(url)


def create_workflow(workflow_config: Dict[str, Any]) -> Dict[str, Any]:
    r = http_post("/workflows/", workflow_config)
    r.raise_for_status()
    return r.json()


def execute_workflow(workflow_id: str, message: str) -> Dict[str, Any]:
    # Create execution (multipart-style payload as string field)
    payload = {
        "payload": json.dumps(
            {
                "user_id": "e2e",
                "session_id": f"e2e-subflow-{SUFFIX}",
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

    # Poll for completion
    while True:
        time.sleep(1)
        status_resp = http_get(f"/executions/{execution_id}")
        status_resp.raise_for_status()
        summary = status_resp.json()
        status = summary.get("status")
        if status in {"completed", "failed", "cancelled", "timeout"}:
            break

    # Fetch results
    res_resp = http_get(f"/executions/{execution_id}/results")
    res_resp.raise_for_status()
    results = res_resp.json()

    # Analyze step results to extract a human-friendly final output
    step_results = results.get("step_results", {})
    subflow_output = None
    final_output = None
    last_completed_output = None

    for _, step in (step_results or {}).items():
        if step.get("status") == "completed":
            od = step.get("output_data", {})
            last_completed_output = od
            if isinstance(od, dict):
                if "response" in od and od["response"] is not None:
                    final_output = od["response"]
                elif "subflow_output" in od and od["subflow_output"] is not None:
                    # Prefer mapped subflow output if present
                    final_output = od["subflow_output"]
            if step.get("step_id") == "call_subflow":
                subflow_output = step.get("output_data", {})

    if final_output is None:
        # Fall back to the last completed step's entire output
        final_output = (
            last_completed_output if last_completed_output is not None else results
        )

    return {
        "final_output": final_output,
        "subflow_step_output": subflow_output,
        "full_results": results,
    }


def main():
    # 1) Create subflow workflow: one data_processing step that uppercases values
    subflow_steps = [
        {
            "step_id": "sf1",
            "step_type": "data_processing",
            "name": "Uppercase",
            # Map only the 'text' field from subflow_input to the step's input
            "input_mapping": {"text": "subflow_input.text"},
            "config": {
                "processing_type": "transform",
                "options": {"transformation": "uppercase"},
            },
        }
    ]
    subflow_config = {
        "name": SUBFLOW_WORKFLOW_NAME,
        "description": "Subflow that uppercases the provided text",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "steps": subflow_steps,
        "global_config": {},
        "tags": ["e2e", "subflow"],
        "timeout_seconds": 60,
        "status": "active",
        "created_by": "e2e",
    }
    subflow = create_workflow(subflow_config)

    # 2) Create parent workflow with trigger and subflow step
    parent_steps = [
        {
            "step_id": "trigger",
            "step_type": "trigger",
            "name": "Trigger",
            "config": {
                "kind": "chat",
                "need_history": True,
                "allowed_modalities": ["text"],
                "max_files": 0,
            },
        },
        {
            "step_id": "call_subflow",
            "step_type": "subflow",
            "name": "Call Subflow",
            "dependencies": ["trigger"],
            # Provide the trigger.messages array as input_data to the subflow step
            # Make the trigger output available to the subflow step
            "input_mapping": {"messages": "trigger"},
            "config": {
                "workflow_id": str(subflow["id"]),
                # Extract text from the trigger output to pass into subflow_input
                "input_mapping": {"text": "messages.current_message"},
                # Return only the sf1 step output from the subflow
                "output_mapping": {"processed": "sf1"},
                "inherit_context": True,
            },
        },
    ]
    parent_config = {
        "name": PARENT_WORKFLOW_NAME,
        "description": "Parent workflow that calls a subflow",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "steps": parent_steps,
        "global_config": {},
        "tags": ["e2e", "subflow"],
        "timeout_seconds": 60,
        "status": "active",
        "created_by": "e2e",
    }
    parent = create_workflow(parent_config)

    # 3) Execute parent workflow
    print("Executing parent workflow with subflow (message: 'Hello Subflow'):")
    res = execute_workflow(parent["id"], "Hello Subflow")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
