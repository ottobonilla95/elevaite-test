#!/usr/bin/env python3
"""
Test script to verify chat history normalization in the streaming workflow endpoint.

This script:
1. Creates a minimal prompt, agent, and workflow
2. Sends a streaming request with chat_history in {actor: "user"|"bot", content: "..."} format
3. Verifies that the agent's response acknowledges the prior conversation context

Usage:
  python scripts/test_chat_history.py --base-url http://localhost:8000
"""

import argparse
import json
import os
import sys
import uuid
from typing import Any, Dict

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
        "prompt_label": f"Chat History Test Prompt {suffix}",
        "prompt": "You are a helpful assistant. Remember information from the conversation history and use it in your responses.",
        "unique_label": f"chat_history_test_{suffix}",
        "app_name": "agent-studio",
        "version": "1.0",
        "ai_model_provider": "OpenAI",
        "ai_model_name": "gpt-4o-mini",
        "tags": ["chat-history", "test"],
        "hyper_parameters": {"temperature": "0.7"},
        "variables": {},
    }
    r = _post_json(base_url, "/api/prompts/", payload)
    return r.json()


def _create_agent(base_url: str, prompt_pid: str) -> Dict[str, Any]:
    suffix = str(uuid.uuid4())[:8]
    payload = {
        "name": f"ChatHistoryTestAgent-{suffix}",
        "system_prompt_id": prompt_pid,
        "routing_options": {"respond": "Respond directly"},
        "functions": [],
    }
    r = _post_json(base_url, "/api/agents/", payload)
    return r.json()


def _create_workflow(base_url: str, agent_id: str) -> Dict[str, Any]:
    suffix = str(uuid.uuid4())[:8]
    payload = {
        "name": f"ChatHistoryWorkflow-{suffix}",
        "description": "Workflow for testing chat history normalization",
        "version": "1.0.0",
        "configuration": {
            "agents": [
                {
                    "agent_id": agent_id,
                }
            ]
        },
        "is_active": True,
        "is_editable": True,
        "tags": ["chat-history", "test"],
    }
    r = _post_json(base_url, "/api/workflows/", payload)
    return r.json()


def _stream_workflow_with_history(
    base_url: str,
    workflow_id: str,
    query: str,
    chat_history: list,
) -> tuple[str, str]:
    """
    Stream a workflow execution with chat history.
    Returns (execution_id, full_response_text)
    """
    url = f"{base_url.rstrip('/')}/api/workflows/{workflow_id}/stream"
    body = {
        "query": query,
        "chat_history": chat_history,
        "runtime_overrides": None,
    }

    print(f"\n📤 Sending request to {url}")
    print(f"📝 Query: {query}")
    print(f"💬 Chat history ({len(chat_history)} messages):")
    for msg in chat_history:
        print(f"   {msg['actor']}: {msg['content']}")

    execution_id = None
    response_chunks = []

    with requests.post(url, json=body, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        print("\n--- Streaming started (SSE) ---")
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw:
                continue
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="ignore")
            if raw.startswith("data: "):
                try:
                    data = json.loads(raw[len("data: "):])
                except Exception:
                    print(raw)
                    continue

                # Print compact view
                print(json.dumps(data, ensure_ascii=False))

                # Extract execution_id
                if not execution_id and isinstance(data, dict) and data.get("execution_id"):
                    execution_id = data["execution_id"]

                # Collect response chunks (Agent Studio uses "type": "content")
                if isinstance(data, dict) and data.get("type") == "content":
                    chunk_text = data.get("message", "")
                    response_chunks.append(chunk_text)

        print("--- Streaming ended ---")

    full_response = "".join(response_chunks)
    return execution_id or "", full_response


def main():
    parser = argparse.ArgumentParser(description="Test chat history normalization")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument("--workflow-id", default=None, help="Optional existing workflow_id (skip creation)")
    args = parser.parse_args()

    base_url = args.base_url

    try:
        # Create workflow if not provided
        if args.workflow_id:
            workflow_id = args.workflow_id
            print(f"Using existing workflow_id={workflow_id}")
        else:
            print("Creating prompt...")
            prompt = _create_prompt(base_url)
            print(f"✅ Created prompt pid={prompt['pid']}")

            print("Creating agent...")
            agent = _create_agent(base_url, prompt_pid=prompt["pid"])
            print(f"✅ Created agent agent_id={agent['agent_id']}")

            print("Creating workflow...")
            workflow = _create_workflow(base_url, agent_id=agent["agent_id"])
            workflow_id = workflow["workflow_id"]
            print(f"✅ Created workflow workflow_id={workflow_id}")

        # Test 1: Simple conversation with name introduction
        print("\n" + "="*80)
        print("TEST 1: Chat history with name introduction")
        print("="*80)

        chat_history = [
            {"actor": "user", "content": "My name is John"},
            {"actor": "bot", "content": "Nice to meet you, John! How can I help you today?"},
        ]

        execution_id, response = _stream_workflow_with_history(
            base_url,
            workflow_id,
            query="What is my name?",
            chat_history=chat_history,
        )

        print(f"\n📊 Execution ID: {execution_id}")
        print(f"🤖 Full Response: {response}")

        # Verify the response mentions "John"
        if "John" in response or "john" in response.lower():
            print("✅ TEST PASSED: Agent correctly referenced the name from chat history!")
        else:
            print("❌ TEST FAILED: Agent did not reference the name from chat history")
            print(f"   Expected response to mention 'John', but got: {response}")

        # Test 2: Multi-turn conversation with context
        print("\n" + "="*80)
        print("TEST 2: Multi-turn conversation with context")
        print("="*80)

        chat_history_2 = [
            {"actor": "user", "content": "I'm planning a trip to Paris"},
            {"actor": "bot", "content": "That sounds exciting! Paris is a beautiful city. When are you planning to go?"},
            {"actor": "user", "content": "In June, for about a week"},
            {"actor": "bot", "content": "June is a great time to visit Paris! The weather is usually pleasant. Are you interested in any specific attractions?"},
        ]

        execution_id_2, response_2 = _stream_workflow_with_history(
            base_url,
            workflow_id,
            query="What city am I visiting?",
            chat_history=chat_history_2,
        )

        print(f"\n📊 Execution ID: {execution_id_2}")
        print(f"🤖 Full Response: {response_2}")

        # Verify the response mentions "Paris"
        if "Paris" in response_2 or "paris" in response_2.lower():
            print("✅ TEST PASSED: Agent correctly referenced Paris from chat history!")
        else:
            print("❌ TEST FAILED: Agent did not reference Paris from chat history")
            print(f"   Expected response to mention 'Paris', but got: {response_2}")

    except requests.HTTPError as http_err:
        print(f"❌ HTTP error: {http_err}")
        if http_err.response is not None:
            try:
                print(http_err.response.json())
            except Exception:
                print(http_err.response.text)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

