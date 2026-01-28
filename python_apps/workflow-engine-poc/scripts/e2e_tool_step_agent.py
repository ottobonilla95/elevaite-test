#!/usr/bin/env python3
# E2E test: trigger -> agent_execution (generate formula) -> tool_execution (calculate)

import json
import time
import uuid
from typing import Dict, Any

import requests

BASE_URL = "http://localhost:8006"
HEADERS = {"Content-Type": "application/json"}
SUFFIX = str(uuid.uuid4())[:8]

WORKFLOW_NAME = f"E2E Tool Step With Agent {SUFFIX}"


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
        "description": "E2E: agent generates a formula; tool evaluates it",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "steps": steps,
        "global_config": {},
        "tags": ["e2e", "tool", "agent"],
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
                "session_id": f"e2e-tool-agent-{SUFFIX}",
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

    # Extract a human-friendly final output
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
                elif "result" in od and od["result"] is not None and od.get("success"):
                    final_output = od
    if final_output is None:
        final_output = (
            last_completed_output if last_completed_output is not None else results
        )

    return {"final_output": final_output, "full_results": results}


def main():
    # Steps: trigger -> agent -> tool
    formula_agent_name = f"FormulaGen_{SUFFIX}"
    steps = [
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
            "step_id": "agent",
            "step_type": "agent_execution",
            "name": "Generate Formula",
            "dependencies": ["trigger"],
            "input_mapping": {
                "current_message": "trigger.current_message",
                "messages": "trigger.messages",
            },
            "config": {
                "agent_name": formula_agent_name,
                "system_prompt": (
                    "You convert user questions into ONLY a simple arithmetic expression that can be evaluated by a calculator. "
                    "Use integers and operators +, -, *, /. Do not include any words, code fences, or explanation."
                ),
                "query": "{current_message}",
                "force_real_llm": False,
            },
        },
        {
            "step_id": "tool",
            "step_type": "tool_execution",
            "name": "Calculate Tool",
            "dependencies": ["agent"],
            # Bring the entire agent output into this step's input_data under 'agent'
            "input_mapping": {"agent": "agent"},
            "config": {
                "tool_name": "calculate",
                # Map the agent's response (the expression) into the tool's 'expression' parameter
                "param_mapping": {"expression": "agent.response"},
            },
        },
    ]

    wf = create_workflow(steps)

    query = "What is 25 + 17? Respond with only the bare formula."
    print("Executing tool step with agent (formula generation -> calculate):")
    print(f"Query: {query}")
    res = execute_workflow(wf["id"], query)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
