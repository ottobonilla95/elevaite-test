#!/usr/bin/env python3
"""
E2E: Scheduler + LLM Agent with current time tool

Creates:
- Prompt (for agent)
- Agent bound to local tool `get_current_time`
- Workflow with scheduled Trigger (cron every 10 seconds) and one Agent Execution step

Then:
- Waits for the scheduler to fire multiple times
- Verifies at least N completed executions for the workflow
- Prints a compact summary of the latest execution outputs

Prereqs:
- Server running (default http://127.0.0.1:8006)
- llm-gateway configured with a model that supports function/tool calling
- Recommended: start server with SCHEDULER_POLL_SECONDS=2 to improve timing

Run:
  python scripts/e2e_scheduler_time_agent.py

Environment overrides:
  BASE_URL=http://localhost:8006 SCHED_MIN_EXEC=2 python scripts/e2e_scheduler_time_agent.py
"""

from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any, Dict, Optional, List

import requests

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8006")
HEADERS = {"Content-Type": "application/json"}
SUFFIX = str(uuid.uuid4())[:8]

WORKFLOW_NAME = f"E2E Scheduled Time Agent {SUFFIX}"
AGENT_NAME = f"TimeAgent_{SUFFIX}"
PROMPT_LABEL = f"TimeAgentPrompt_{SUFFIX}"

MIN_EXPECTED_EXEC = int(os.environ.get("SCHED_MIN_EXEC", "2"))
WAIT_SECONDS = int(os.environ.get("SCHED_WAIT_SECONDS", "45"))  # total time to wait for scheduled runs


def http_post(path: str, data: Dict[str, Any], files=None) -> requests.Response:
    url = f"{BASE_URL}{path}"
    if files:
        return requests.post(url, data=data, files=files)
    return requests.post(url, headers=HEADERS, data=json.dumps(data))


def http_get(path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
    url = f"{BASE_URL}{path}"
    return requests.get(url, params=params)


def require_server():
    try:
        r = http_get("/health")
        r.raise_for_status()
    except Exception as e:
        raise SystemExit(f"Server not reachable at {BASE_URL}: {e}")


def create_prompt() -> Dict[str, Any]:
    payload = {
        "prompt_label": PROMPT_LABEL,
        "prompt": (
            "You are a reliable time reporting assistant. When asked for the current time, "
            "you MUST call the function get_current_time with timezone 'UTC' and return its value only."
        ),
        "unique_label": PROMPT_LABEL,
        "app_name": "workflow-engine-poc",
        "ai_model_provider": "OpenAI",
        "ai_model_name": "gpt-4o-mini",
        "tags": ["e2e", "scheduler"],
        "hyper_parameters": {"temperature": 0.0},
        "variables": {},
    }
    r = http_post("/prompts/", payload)
    r.raise_for_status()
    return r.json()


def create_agent(prompt_id: str) -> Dict[str, Any]:
    payload = {
        "name": AGENT_NAME,
        "description": "Agent that reports the current time by calling a tool",
        "system_prompt_id": prompt_id,
        "provider_type": "openai_textgen",
        "provider_config": {"model_name": "gpt-4o-mini"},
        "tags": ["e2e", "scheduler"],
        "status": "active",
        "organization_id": "e2e",
        "created_by": "e2e",
    }
    r = http_post("/agents/", payload)
    r.raise_for_status()
    return r.json()


def bind_current_time_tool(agent_id: str):
    # Ensure local tools are synced into DB (idempotent)
    sync = http_post("/tools/sync", {"source": "local"})
    if sync.status_code not in (200, 201):
        print("Warning: tool sync returned status", sync.status_code, sync.text)

    payload = {"local_tool_name": "get_current_time"}
    r = http_post(f"/agents/{agent_id}/tools", payload)
    r.raise_for_status()
    return r.json()


def create_scheduled_workflow() -> Dict[str, Any]:
    # Trigger with cron every 10 seconds (six-field cron). Use UTC by default.
    steps = [
        {
            "step_id": "trigger",
            "step_type": "trigger",
            "name": "Trigger",
            # IMPORTANT: scheduler reads from 'parameters', not 'config'
            "parameters": {
                "kind": "chat",
                "need_history": False,
                "allowed_modalities": ["text"],
                "max_files": 0,
                "schedule": {
                    "enabled": True,
                    "mode": "cron",
                    "cron": "* * * * * */10",  # every 10 seconds (croniter uses seconds as 6th field)
                    "timezone": "UTC",
                    "backend": "dbos",
                    "jitter_seconds": 0,
                },
            },
        },
        {
            "step_id": "agent",
            "step_type": "agent_execution",
            "name": "Ask Time",
            "dependencies": ["trigger"],
            "input_mapping": {"current_message": "trigger.current_message", "messages": "trigger.messages"},
            "config": {
                "agent_name": AGENT_NAME,
                "system_prompt": (
                    "When asked for the current time, call the function get_current_time with timezone 'UTC'. "
                    "Return only the function's return string."
                ),
                "query": "What time is it now?",
                "force_real_llm": True,
            },
        },
    ]

    payload = {
        "name": WORKFLOW_NAME,
        "description": "Scheduled every 10 seconds to ask for the current time via tool",
        "version": "1.0.0",
        "execution_pattern": "sequential",
        "steps": steps,
        "global_config": {},
        "tags": ["e2e", "scheduler", "time"],
        "timeout_seconds": 30,
        "status": "active",
        "created_by": "e2e",
    }
    r = http_post("/workflows/", payload)
    r.raise_for_status()
    return r.json()


def fetch_latest_executions(workflow_id: str, limit: int = 10) -> List[Dict[str, Any]]:
    r = http_get(
        "/executions/sqlmodel/",
        params={"workflow_id": workflow_id, "limit": str(limit), "offset": "0"},
    )
    r.raise_for_status()
    return r.json()


def fetch_execution_details(execution_id: str) -> Dict[str, Any]:
    r = http_get(f"/executions/sqlmodel/{execution_id}")
    r.raise_for_status()
    return r.json()


def main():
    print(f"BASE_URL = {BASE_URL}")
    require_server()

    print("Creating prompt...")
    pr = create_prompt()
    prompt_id = pr.get("id")

    print("Creating agent and binding current_time tool...")
    ag = create_agent(prompt_id)
    agent_id = ag.get("id")
    bind_current_time_tool(str(agent_id))

    print("Creating scheduled workflow (cron every 10s)...")
    wf = create_scheduled_workflow()
    workflow_id = wf.get("id") or wf.get("workflow_id")
    print("Workflow:", workflow_id)

    # Wait for scheduled runs
    print(f"Waiting up to {WAIT_SECONDS}s for scheduled executions...")
    deadline = time.time() + WAIT_SECONDS
    seen: set[str] = set()
    completed = 0
    last_exec: Optional[Dict[str, Any]] = None

    while time.time() < deadline and completed < MIN_EXPECTED_EXEC:
        time.sleep(2)
        items = fetch_latest_executions(str(workflow_id), limit=10)
        for exe in items:
            eid = exe.get("execution_id") or exe.get("id")
            if not eid or eid in seen:
                continue
            seen.add(eid)
            if exe.get("status") in ("completed", "failed", "cancelled", "timeout"):
                if exe.get("status") == "completed":
                    completed += 1
                last_exec = exe
        # compact log
        print(f"Observed {len(seen)} executions so far; completed={completed}")

    if completed < MIN_EXPECTED_EXEC:
        raise SystemExit(
            f"Expected at least {MIN_EXPECTED_EXEC} completed executions, observed {completed}. "
            "Ensure SCHEDULER_POLL_SECONDS is small (e.g., 2) and cron is '*/10 * * * * *'."
        )

    # Fetch and print details of the most recent execution
    if last_exec:
        eid = last_exec.get("execution_id") or last_exec.get("id")
        details = fetch_execution_details(str(eid))
        step_io = details.get("step_io_data") or {}
        agent_out = step_io.get("agent") or {}
        print("\nLatest execution details (compact):")
        print(
            json.dumps(
                {
                    "execution_id": eid,
                    "status": details.get("status"),
                    "response": agent_out.get("response"),
                    "tool_calls": agent_out.get("tool_calls"),
                    "started_at": details.get("started_at"),
                    "completed_at": details.get("completed_at"),
                },
                indent=2,
                default=str,
            )
        )
    else:
        print("No execution details captured.")

    print("\nE2E scheduler time agent test: SUCCESS")


if __name__ == "__main__":
    main()
