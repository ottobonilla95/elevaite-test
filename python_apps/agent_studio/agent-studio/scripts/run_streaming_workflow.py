#!/usr/bin/env python3
"""
Create a minimal prompt, agent, and workflow via Agent Studio API, then run the
workflow through the streaming endpoint and print SSE events.

Usage examples:
  python scripts/run_streaming_workflow.py \
    --base-url http://localhost:8000 \
    --query "Hello from streaming!"

To reuse an existing workflow (skip creation):
  python scripts/run_streaming_workflow.py --workflow-id <UUID> --query "Hi"

Environment variables:
  BASE_URL (default: http://localhost:8000)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from typing import Any, Dict, Optional

import requests

DEFAULT_BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
HEADERS_JSON = {"Content-Type": "application/json"}


def _post_json(base_url: str, path: str, payload: Dict[str, Any]) -> requests.Response:
    url = base_url.rstrip("/") + path
    resp = requests.post(url, headers=HEADERS_JSON, data=json.dumps(payload), timeout=30)
    resp.raise_for_status()
    return resp


def _create_prompt(base_url: str) -> Dict[str, Any]:
    suffix = str(uuid.uuid4())[:8]
    payload = {
        "prompt_label": f"Streaming Test Prompt {suffix}",
        "prompt": "You are a helpful agent. Respond concisely.",
        "unique_label": f"stream_test_{suffix}",
        "app_name": "agent-studio",
        "version": "1.0",
        "ai_model_provider": "OpenAI",
        "ai_model_name": "gpt-4o-mini",
        "tags": ["streaming", "test"],
        "hyper_parameters": {"temperature": "0.2"},
        "variables": {},
    }
    r = _post_json(base_url, "/api/prompts/", payload)
    return r.json()


def _create_agent(base_url: str, prompt_pid: str) -> Dict[str, Any]:
    suffix = str(uuid.uuid4())[:8]
    payload = {
        "name": f"StreamingTestAgent-{suffix}",
        "system_prompt_id": prompt_pid,
        "routing_options": {"respond": "Respond directly"},
        "functions": [],
        # Optional fields rely on defaults in the schema
    }
    r = _post_json(base_url, "/api/agents/", payload)
    return r.json()


def _create_workflow(base_url: str, agent_id: str) -> Dict[str, Any]:
    suffix = str(uuid.uuid4())[:8]
    payload = {
        "name": f"StreamingWorkflow-{suffix}",
        "description": "Minimal single-agent workflow for streaming demo",
        "version": "1.0.0",
        "configuration": {
            "agents": [
                {
                    # Provide an explicit agent reference so builder uses our agent
                    "agent_id": agent_id,
                    # Optional: node position/config can be omitted for minimal case
                }
            ]
        },
        "is_active": True,
        "is_editable": True,
        "tags": ["streaming", "demo"],
    }
    r = _post_json(base_url, "/api/workflows/", payload)
    return r.json()


def _stream_workflow(base_url: str, workflow_id: str, query: str, session_id: Optional[str] = None, user_id: Optional[str] = None) -> str:
    url = f"{base_url.rstrip('/')}/api/workflows/{workflow_id}/stream"
    body = {
        "query": query,
        "chat_history": [],
        "runtime_overrides": None,
        "session_id": session_id,
        "user_id": user_id,
    }

    # Use stream=True to iterate lines as SSE
    with requests.post(url, json=body, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        execution_id = None
        print("--- Streaming started (SSE) ---")
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw:
                continue
            # Expect lines like: "data: {json}"
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")
            if raw.startswith("data: "):
                try:
                    data = json.loads(raw[len("data: "):])
                except Exception:
                    print(raw)
                    continue
                # Pretty-print a compact view
                print(json.dumps(data, ensure_ascii=False))
                if not execution_id and isinstance(data, dict) and data.get("execution_id"):
                    execution_id = data["execution_id"]
        print("--- Streaming ended ---")
        return execution_id or ""


def main():
    parser = argparse.ArgumentParser(description="Create and stream a workflow via API")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL (default: %(default)s)")
    parser.add_argument("--query", default="Hello! Please introduce yourself.", help="Query to send to the agent")
    parser.add_argument("--workflow-id", default=None, help="Optional existing workflow_id to stream (skip creation)")
    parser.add_argument("--session-id", default=None, help="Optional session id to attach")
    parser.add_argument("--user-id", default=None, help="Optional user id to attach")
    args = parser.parse_args()

    base_url = args.base_url

    try:
        if args.workflow_id:
            workflow_id = args.workflow_id
            print(f"Using existing workflow_id={workflow_id}")
        else:
            print("Creating prompt...")
            prompt = _create_prompt(base_url)
            print(f"Created prompt pid={prompt['pid']}")

            print("Creating agent...")
            agent = _create_agent(base_url, prompt_pid=prompt["pid"])
            print(f"Created agent agent_id={agent['agent_id']}")

            print("Creating workflow...")
            workflow = _create_workflow(base_url, agent_id=agent["agent_id"])
            workflow_id = workflow["workflow_id"]
            print(f"Created workflow workflow_id={workflow_id}")

        print("Starting streaming...")
        execution_id = _stream_workflow(
            base_url,
            workflow_id,
            query=args.query,
            session_id=args.session_id,
            user_id=args.user_id,
        )
        if execution_id:
            print(f"Execution ID: {execution_id}")
        else:
            print("No execution_id received from stream (check server logs)")

    except requests.HTTPError as http_err:
        print(f"HTTP error: {http_err}")
        if http_err.response is not None:
            try:
                print(http_err.response.json())
            except Exception:
                print(http_err.response.text)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

