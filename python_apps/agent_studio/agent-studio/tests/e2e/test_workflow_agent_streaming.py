"""
E2E test for agent-to-agent streaming in workflows.

This test verifies the complete workflow execution flow including:
- Creating agents via API
- Creating workflows with connections via API
- Executing workflows with agent-to-agent calls
- Streaming responses with proper JSON serialization

Note: This test uses real OpenAI API calls and requires OPENAI_API_KEY to be set.
This test hits the real deployed API server (default: http://localhost:8000).
"""

import json
import os

import pytest
import requests


@pytest.mark.e2e
def test_workflow_agent_to_agent_streaming_e2e():
    """
    E2E test for agent-to-agent streaming workflow execution.

    This test:
    1. Creates two agents via API (MainAgent and HelperAgent)
    2. Creates a workflow with connections via API
    3. Executes the workflow via streaming endpoint
    4. Verifies agent-to-agent calls work and all chunks are valid JSON
    """

    # Get base URL from environment or use default
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    print(f"\n🌐 Using API at: {base_url}")

    # ===== Step 1: Create Prompts via API =====
    helper_prompt_payload = {
        "prompt_label": "Helper Agent Prompt E2E",
        "prompt": "You are a helpful assistant. When asked about the weather, respond with: 'The weather is sunny and 72 degrees.'",
        "unique_label": "HelperAgentPrompt_E2E",
        "app_name": "agent_studio_tests",
        "version": "1.0.0",
        "ai_model_provider": "openai",
        "ai_model_name": "gpt-4o-mini",
        "tags": ["test", "e2e"],
        "hyper_parameters": {"temperature": "0.2"},
        "variables": {},
    }

    response = requests.post(f"{base_url}/api/prompts/", json=helper_prompt_payload)
    assert response.status_code == 200, f"Failed to create helper prompt: {response.text}"
    helper_prompt = response.json()
    helper_prompt_id = helper_prompt["pid"]  # Note: prompt response uses 'pid' not 'prompt_id'
    print(f"✅ Created Helper Prompt: {helper_prompt_id}")

    main_prompt_payload = {
        "prompt_label": "Main Agent Prompt E2E",
        "prompt": "You are an orchestrator agent. When asked about the weather, call the HelperAgent_E2E tool to get the information.",
        "unique_label": "MainAgentPrompt_E2E",
        "app_name": "agent_studio_tests",
        "version": "1.0.0",
        "ai_model_provider": "openai",
        "ai_model_name": "gpt-4o-mini",
        "tags": ["test", "e2e"],
        "hyper_parameters": {"temperature": "0.2"},
        "variables": {},
    }

    response = requests.post(f"{base_url}/api/prompts/", json=main_prompt_payload)
    assert response.status_code == 200, f"Failed to create main prompt: {response.text}"
    main_prompt = response.json()
    main_prompt_id = main_prompt["pid"]  # Note: prompt response uses 'pid' not 'prompt_id'
    print(f"✅ Created Main Prompt: {main_prompt_id}")

    # ===== Step 2: Create Helper Agent via API =====
    # Note: Helper agent should respond with plain text, not JSON with routing
    helper_agent_payload = {
        "name": "HelperAgent_E2E",
        "agent_type": "api",
        "description": "Helper agent that provides information",
        "system_prompt_id": helper_prompt_id,
        "routing_options": {},
        "functions": [],
        "response_type": "markdown",  # Use markdown instead of json to avoid routing responses
        "deployment_code": "helper_e2e",
    }

    response = requests.post(f"{base_url}/api/agents/", json=helper_agent_payload)
    assert response.status_code == 200, f"Failed to create helper agent: {response.text}"
    helper_agent = response.json()
    helper_agent_id = helper_agent["agent_id"]
    print(f"✅ Created HelperAgent: {helper_agent_id}")

    # ===== Step 3: Create Main Agent via API =====
    main_agent_payload = {
        "name": "MainAgent_E2E",
        "agent_type": "api",
        "description": "Main agent that orchestrates the workflow",
        "system_prompt_id": main_prompt_id,
        "routing_options": {},
        "functions": [],
        "deployment_code": "main_e2e",
    }

    response = requests.post(f"{base_url}/api/agents/", json=main_agent_payload)
    assert response.status_code == 200, f"Failed to create main agent: {response.text}"
    main_agent = response.json()
    main_agent_id = main_agent["agent_id"]
    print(f"✅ Created MainAgent: {main_agent_id}")

    # ===== Step 4: Create Workflow with Connections via API =====
    workflow_payload = {
        "name": "AgentToAgentWorkflow_E2E",
        "description": "E2E test workflow for agent-to-agent streaming",
        "version": "1.0.0",
        "configuration": {
            "agents": [
                {
                    "agent_type": "MainAgent_E2E",
                    "agent_id": main_agent_id,
                    "position": {"x": 100, "y": 100},
                },
                {
                    "agent_type": "HelperAgent_E2E",
                    "agent_id": helper_agent_id,
                    "position": {"x": 300, "y": 100},
                },
            ],
            "connections": [
                {
                    "source_agent_id": main_agent_id,
                    "target_agent_id": helper_agent_id,
                    "connection_type": "default",
                }
            ],
        },
        "created_by": "test_e2e",
        "is_active": True,
        "is_editable": True,
        "tags": ["test", "e2e", "streaming"],
    }

    response = requests.post(f"{base_url}/api/workflows/", json=workflow_payload)
    assert response.status_code == 200, f"Failed to create workflow: {response.text}"
    workflow = response.json()
    workflow_id = workflow["workflow_id"]
    print(f"✅ Created Workflow: {workflow_id}")

    # ===== Step 5: Execute Workflow via Streaming Endpoint =====
    stream_payload = {
        "query": "Ask the Helper Agent to say Hello World.",
        "session_id": "test_e2e_session",
        "user_id": "test_e2e_user",
    }

    print(f"\n🚀 Streaming workflow execution...")
    response = requests.post(
        f"{base_url}/api/workflows/{workflow_id}/stream",
        json=stream_payload,
        headers={"Accept": "text/event-stream"},
        stream=True,
    )

    assert response.status_code == 200, f"Failed to stream workflow: {response.text}"

    # ===== Step 6: Parse and Validate Streaming Response =====
    chunks_received = []
    content_chunks = []
    agent_call_chunks = []

    # Stream the response line by line
    for line in response.iter_lines(decode_unicode=True):
        if line and line.startswith("data: "):
            data_str = line[6:]  # Remove "data: " prefix
            try:
                chunk = json.loads(data_str)
                chunks_received.append(chunk)

                # Print full JSON object for debugging
                print(f"  📦 Full chunk: {json.dumps(chunk, indent=2)}")

                # Track content chunks
                if chunk.get("type") == "content":
                    content_chunks.append(chunk)

                # Track agent call info (now comes as "info" type, not "content")
                if chunk.get("type") == "info":
                    data = chunk.get("data", "")
                    if "Agent Called:" in str(data):
                        agent_call_chunks.append(chunk)

            except json.JSONDecodeError as e:
                pytest.fail(f"Failed to parse chunk as JSON: {data_str}\nError: {e}")

    # ===== Step 7: Verify Results =====
    print(f"\n✅ Test passed! Received {len(chunks_received)} chunks without JSON serialization errors")
    print(f"Content chunks: {len(content_chunks)}")
    print(f"Agent call chunks: {len(agent_call_chunks)}")

    # Verify we got chunks
    assert len(chunks_received) > 0, "No chunks received from streaming endpoint"
    assert len(content_chunks) > 0, "No content chunks received"

    # Verify workflow started and completed
    status_chunks = [c for c in chunks_received if "status" in c]
    assert any(c.get("status") == "started" for c in status_chunks), "No 'started' status chunk"
    assert any(c.get("status") == "completed" for c in status_chunks), "No 'completed' status chunk"

    # Verify agent-to-agent call happened
    assert len(agent_call_chunks) > 0, "No agent-to-agent calls detected in streaming response"

    print(f"\n📦 All chunks received:")
    for i, chunk in enumerate(chunks_received, 1):
        print(f"  {i}. {chunk}")

    print("\n🎉 E2E test completed successfully!")
    print("✅ Agents created via API")
    print("✅ Workflow created with connections via API")
    print("✅ Workflow executed with streaming")
    print("✅ Agent-to-agent calls detected")
    print("✅ All chunks properly serialized to JSON")

    # ===== Cleanup =====
    # Delete workflow
    response = requests.delete(f"{base_url}/api/workflows/{workflow_id}")
    assert response.status_code == 200, f"Failed to delete workflow: {response.text}"
    print(f"\n🧹 Cleaned up workflow: {workflow_id}")

    # Delete agents
    response = requests.delete(f"{base_url}/api/agents/{main_agent_id}")
    assert response.status_code == 200, f"Failed to delete main agent: {response.text}"
    print(f"🧹 Cleaned up MainAgent: {main_agent_id}")

    response = requests.delete(f"{base_url}/api/agents/{helper_agent_id}")
    assert response.status_code == 200, f"Failed to delete helper agent: {response.text}"
    print(f"🧹 Cleaned up HelperAgent: {helper_agent_id}")

    # Delete prompts
    response = requests.delete(f"{base_url}/api/prompts/{main_prompt_id}")
    assert response.status_code == 200, f"Failed to delete main prompt: {response.text}"
    print(f"🧹 Cleaned up Main Prompt: {main_prompt_id}")

    response = requests.delete(f"{base_url}/api/prompts/{helper_prompt_id}")
    assert response.status_code == 200, f"Failed to delete helper prompt: {response.text}"
    print(f"🧹 Cleaned up Helper Prompt: {helper_prompt_id}")
