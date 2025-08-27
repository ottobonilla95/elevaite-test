#!/usr/bin/env python3
# E2E test script: creates 3 agents with different tools, connects one agent to the other two,
# creates a workflow with a chat trigger and an agent execution step, and executes it against
# the running API on port 8006.

import json
import time
import uuid
from typing import Dict, Any, List
import requests

# ---------------- Configuration ----------------
BASE_URL = "http://localhost:8006"
HEADERS = {"Content-Type": "application/json"}
SUFFIX = str(uuid.uuid4())[:8]

# Agent names
AGENT_A_NAME = f"RouterAgent_{SUFFIX}"  # This agent will have access to B and C
AGENT_B_NAME = f"MathAgent_{SUFFIX}"
AGENT_C_NAME = f"TimeAgent_{SUFFIX}"

# Prompts
ROUTER_PROMPT = "You are a router agent. Decide which connected agent to call."
MATH_PROMPT = "You are a math assistant. Perform calculations when asked."
TIME_PROMPT = "You provide current time information."

# Tools: we will register DB-backed tool entries for math and time
TOOLS_TO_CREATE = [
    {
        "name": f"calc_{SUFFIX}",
        "display_name": "Calculate",
        "description": "Performs a calculation via expression",
        "version": "1.0.0",
        "tool_type": "local",
        "execution_type": "function",
        "parameters_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Math expression to evaluate"}},
            "required": ["expression"],
        },
    },
    {
        "name": f"time_{SUFFIX}",
        "display_name": "CurrentTime",
        "description": "Returns current time in a timezone",
        "version": "1.0.0",
        "tool_type": "local",
        "execution_type": "function",
        "parameters_schema": {
            "type": "object",
            "properties": {"timezone": {"type": "string", "description": "Timezone label"}},
            "required": [],
        },
    },
]

# Agent connections: RouterAgent can call MathAgent and TimeAgent
CONNECTED_FOR_ROUTER: List[str] = []  # will be filled with created IDs

# Workflow name
WORKFLOW_NAME = f"E2E Agent Connections {SUFFIX}"


# ---------------- HTTP helpers ----------------
def http_post(path: str, data: Dict[str, Any], files=None):
    url = f"{BASE_URL}{path}"
    if files:
        return requests.post(url, data=data, files=files)
    return requests.post(url, headers=HEADERS, data=json.dumps(data))


def http_get(path: str):
    url = f"{BASE_URL}{path}"
    return requests.get(url)


# ---------------- API operations ----------------
def create_prompt(prompt_text: str) -> Dict[str, Any]:
    payload = {
        "prompt_label": f"label_{SUFFIX}",
        "prompt": prompt_text,
        "unique_label": f"unique_{SUFFIX}_{uuid.uuid4().hex[:6]}",
        "app_name": "workflow_engine_poc",
        "ai_model_provider": "openai_textgen",
        "ai_model_name": "gpt-4o-mini",
        "tags": [],
        "hyper_parameters": {},
        "variables": {},
    }
    r = http_post("/agents/prompts", payload)
    r.raise_for_status()
    return r.json()


def create_tool(tool_def: Dict[str, Any]) -> Dict[str, Any]:
    r = http_post("/tools/db", tool_def)
    r.raise_for_status()
    return r.json()


def create_agent(name: str, prompt_id: str) -> Dict[str, Any]:
    payload = {
        "name": name,
        "description": name,
        "system_prompt_id": prompt_id,
        "provider_type": "openai_textgen",
        "provider_config": {"provider_type": "openai_textgen", "model_name": "gpt-4o-mini"},
        "tags": [],
        "status": "active",
    }
    r = http_post("/agents/", payload)
    r.raise_for_status()
    return r.json()


def attach_tool_to_agent(agent_id: str, tool_id: str) -> Dict[str, Any]:
    payload = {"tool_id": tool_id}
    r = http_post(f"/agents/{agent_id}/tools", payload)
    r.raise_for_status()
    return r.json()


def create_workflow(router_agent_name: str, connected_agents: List[Dict[str, Any]], router_prompt: str) -> Dict[str, Any]:
    steps = [
        {
            "step_id": "trigger",
            "step_type": "trigger",
            "name": "Trigger",
            "config": {"kind": "chat", "need_history": True, "allowed_modalities": ["text"], "max_files": 0},
        },
        {
            "step_id": "agent",
            "step_type": "agent_execution",
            "name": "Agent Exec",
            "dependencies": ["trigger"],
            "config": {
                "agent_name": router_agent_name,
                "system_prompt": router_prompt,
                "query": "{current_message}",
                "tools": [],  # pass router's own tools by names here if needed
                "connected_agents": connected_agents,
                "force_real_llm": False,
            },
        },
    ]

    payload = {
        "name": WORKFLOW_NAME,
        "description": "E2E test: agent connections",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "steps": steps,
        "global_config": {},
        "tags": ["e2e"],
        "timeout_seconds": 60,
        "status": "active",
        "created_by": "e2e",
    }
    r = http_post("/workflows/", payload)
    r.raise_for_status()
    return r.json()


def execute_workflow(workflow_id: str, message: str) -> Dict[str, Any]:
    # Create execution
    payload = {
        "payload": json.dumps(
            {
                "user_id": "e2e",
                "session_id": f"e2e-{SUFFIX}",
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

    # Compute final response (agent step output if present)
    step_results = results.get("step_results", {})
    final_response = None
    if isinstance(step_results, dict):
        # Look for the last completed step with a 'response' in output_data
        for _, step in step_results.items():
            if step.get("status") == "completed" and isinstance(step.get("output_data"), dict):
                resp = step.get("output_data", {}).get("response")
                if resp is not None:
                    final_response = resp
    if final_response is None:
        # As a fallback, return the whole results structure
        final_response = {"info": "no final response found", "results": results}

    return final_response


def main():
    # 1) Create prompts
    pr_router = create_prompt(ROUTER_PROMPT)
    pr_math = create_prompt(MATH_PROMPT)
    pr_time = create_prompt(TIME_PROMPT)

    # 2) Create tools
    t_calc = create_tool(TOOLS_TO_CREATE[0])
    t_time = create_tool(TOOLS_TO_CREATE[1])

    # 3) Create agents
    a_router = create_agent(AGENT_A_NAME, pr_router["id"])
    a_math = create_agent(AGENT_B_NAME, pr_math["id"])
    a_time = create_agent(AGENT_C_NAME, pr_time["id"])

    # 4) Attach tools to B and C
    attach_tool_to_agent(a_math["id"], t_calc["id"])
    attach_tool_to_agent(a_time["id"], t_time["id"])

    # 5) Create workflow: Router agent connected to Math and Time agents by name
    connected = [
        {
            "id": str(a_math["id"]),
            "tools": ["calculate"],
            "connected_agents": [{"name": f"HelperAgent_{SUFFIX}", "tools": ["add_numbers"]}],
        },
        {"id": str(a_time["id"]), "tools": ["get_current_time"]},
    ]
    wf = create_workflow(str(a_router["name"]), connected, pr_router["prompt"])

    # 6) Execute workflow a couple of times
    print("Executing workflow (math):")
    res1 = execute_workflow(wf["id"], "What is 25 + 17?")
    print(json.dumps(res1, indent=2))

    print("Executing workflow (time):")
    res2 = execute_workflow(wf["id"], "What's the current time in UTC?")
    print(json.dumps(res2, indent=2))


if __name__ == "__main__":
    main()
