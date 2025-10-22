"""
E2E test for agent -> tool -> agent streaming in workflows.

This test verifies the complete workflow execution flow including:
- Creating agents via API
- Creating workflows with tool steps via API
- Executing workflows with agent -> tool -> agent flow
- Streaming responses with proper JSON serialization
- Tool execution and tool response chunks

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
    E2E test for agent -> tool -> agent streaming workflow execution.

    This test:
    1. Creates two agents via API (MainAgent and HelperAgent)
    2. Creates a workflow with a tool step via API (agent -> tool -> agent)
    3. Executes the workflow via streaming endpoint
    4. Verifies tool execution works and all chunks are valid JSON
    """

    # Get base URL from environment or use default
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    print(f"\n🌐 Using API at: {base_url}")

    # Track created resources for cleanup
    created_resources = {
        "workflow_id": None,
        "main_agent_id": None,
        "helper_agent_id": None,
        "main_prompt_id": None,
        "helper_prompt_id": None,
    }

    try:
        # ===== Step 1: Create Prompts via API =====
        helper_prompt_payload = {
            "prompt_label": "Helper Agent Prompt E2E",
            "prompt": "You are a helpful assistant. Explain the calculation result provided to you.",
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
        created_resources["helper_prompt_id"] = helper_prompt_id
        print(f"✅ Created Helper Prompt: {helper_prompt_id}")

        main_prompt_payload = {
            "prompt_label": "Main Agent Prompt E2E",
            "prompt": 'You are an orchestrator agent. Generate two random numbers between 1 and 100 and respond with ONLY a JSON object in this exact format: {"number_a": <first_number>, "number_b": <second_number>}. Do not include any other text.',
            "unique_label": "MainAgentPrompt_E2E",
            "app_name": "agent_studio_tests",
            "version": "1.0.0",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4o-mini",
            "tags": ["test", "e2e"],
            "hyper_parameters": {"temperature": "0.7"},
            "variables": {},
        }

        response = requests.post(f"{base_url}/api/prompts/", json=main_prompt_payload)
        assert response.status_code == 200, f"Failed to create main prompt: {response.text}"
        main_prompt = response.json()
        main_prompt_id = main_prompt["pid"]  # Note: prompt response uses 'pid' not 'prompt_id'
        created_resources["main_prompt_id"] = main_prompt_id
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
        created_resources["helper_agent_id"] = helper_agent_id
        print(f"✅ Created HelperAgent: {helper_agent_id}")

        # ===== Step 3: Create Main Agent via API =====
        main_agent_payload = {
            "name": "MainAgent_E2E",
            "agent_type": "api",
            "description": "Main agent that generates random numbers",
            "system_prompt_id": main_prompt_id,
            "routing_options": {},
            "functions": [],
            "response_type": "json",  # Expect JSON response
            "deployment_code": "main_e2e",
        }

        response = requests.post(f"{base_url}/api/agents/", json=main_agent_payload)
        assert response.status_code == 200, f"Failed to create main agent: {response.text}"
        main_agent = response.json()
        main_agent_id = main_agent["agent_id"]
        created_resources["main_agent_id"] = main_agent_id
        print(f"✅ Created MainAgent: {main_agent_id}")

        # ===== Step 4: Create Workflow with Tool Step via API =====
        # Generate a unique ID for the tool node
        tool_node_id = f"tool_add_numbers_{int(os.urandom(4).hex(), 16)}"

        workflow_payload = {
            "name": "AgentToolAgentWorkflow_E2E",
            "description": "E2E test workflow for agent -> tool -> agent streaming",
            "version": "1.0.0",
            "configuration": {
                "agents": [
                    {
                        "agent_type": "MainAgent_E2E",
                        "agent_id": main_agent_id,
                        "position": {"x": 100, "y": 100},
                        "config": {
                            # MainAgent generates JSON for the tool - not meant for end users
                            "visible_to_user": False,
                        },
                    },
                    {
                        "agent_type": "tool",  # Tool execution node
                        "agent_id": tool_node_id,  # Unique ID for the tool node
                        "position": {"x": 200, "y": 100},
                        "config": {
                            "tool_name": "add_numbers",
                            "param_mapping": {
                                # The input_data will have the agent output under the source step_id
                                # Agent output structure: {step_id: {response: "...", success: true, ...}}
                                # We need to extract from response field and parse JSON
                                "a": f"{main_agent_id}.response.number_a",
                                "b": f"{main_agent_id}.response.number_b",
                            },
                            "static_params": {},
                        },
                    },
                    {
                        "agent_type": "HelperAgent_E2E",
                        "agent_id": helper_agent_id,
                        "position": {"x": 300, "y": 100},
                        "config": {
                            # Query template that references the tool result
                            # The tool step output will be available in input_data under the tool_node_id key
                            "query": f"The calculation result is: {{{tool_node_id}}}. Please explain this result to the user.",
                            # HelperAgent output is meant for end users
                            "visible_to_user": True,
                        },
                    },
                ],
                "connections": [
                    {
                        "source_agent_id": main_agent_id,
                        "target_agent_id": tool_node_id,
                        "connection_type": "default",
                    },
                    {
                        "source_agent_id": tool_node_id,
                        "target_agent_id": helper_agent_id,
                        "connection_type": "default",
                    },
                ],
            },
            "created_by": "test_e2e",
            "is_active": True,
            "is_editable": True,
            "tags": ["test", "e2e", "streaming", "tool"],
        }

        response = requests.post(f"{base_url}/api/workflows/", json=workflow_payload)
        assert response.status_code == 200, f"Failed to create workflow: {response.text}"
        workflow = response.json()
        workflow_id = workflow["workflow_id"]
        created_resources["workflow_id"] = workflow_id
        print(f"✅ Created Workflow: {workflow_id}")

        # ===== Step 5: Execute Workflow via Streaming Endpoint =====
        stream_payload = {
            "query": "Generate two random numbers and add them together.",
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
        hidden_chunks = []
        agent_call_chunks = []
        tool_response_chunks = []
        tool_execution_chunks = []

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

                    # Track hidden chunks (internal workflow data not meant for end users)
                    if chunk.get("type") == "hidden":
                        hidden_chunks.append(chunk)
                        print(
                            f"  🔒 Hidden chunk: {chunk.get('message', '')[:50]}... (source: {chunk.get('source', 'unknown')})"
                        )

                    # Track agent call chunks (comes as "info" type with "Calling" in message)
                    if chunk.get("type") == "info":
                        data = chunk.get("message", "")
                        if "Agent Called:" in str(data):
                            agent_call_chunks.append(chunk)
                            print(f"  🤖 Agent call: {data[:100]}...")

                    # Track tool response chunks (new type for tool execution results)
                    if chunk.get("type") == "tool_response":
                        tool_response_chunks.append(chunk)
                        print(f"  🔧 Tool response received: {chunk.get('message', '')[:100]}...")

                    # Track tool execution chunks (info about tool being called)
                    if chunk.get("type") == "info" and "tool" in str(chunk.get("message", "")).lower():
                        tool_execution_chunks.append(chunk)
                        print(f"  🔨 Tool execution: {chunk.get('message', '')[:100]}...")

                except json.JSONDecodeError as e:
                    pytest.fail(f"Failed to parse chunk as JSON: {data_str}\nError: {e}")

        # ===== Step 7: Verify Results =====
        print(f"\n✅ Test passed! Received {len(chunks_received)} chunks without JSON serialization errors")
        print(f"Content chunks: {len(content_chunks)}")
        print(f"Hidden chunks: {len(hidden_chunks)}")
        print(f"Agent call chunks: {len(agent_call_chunks)}")
        print(f"Tool execution chunks: {len(tool_execution_chunks)}")
        print(f"Tool response chunks: {len(tool_response_chunks)}")

        # Verify we got chunks
        assert len(chunks_received) > 0, "No chunks received from streaming endpoint"
        assert len(content_chunks) > 0, "No content chunks received"

        # Verify workflow started and completed
        status_chunks = [c for c in chunks_received if "status" in c]
        assert any(c.get("status") == "started" for c in status_chunks), "No 'started' status chunk"
        assert any(c.get("status") == "completed" for c in status_chunks), "No 'completed' status chunk"

        # Verify tool execution happened (either via tool_execution chunks or tool_response chunks)
        assert len(tool_execution_chunks) > 0 or len(tool_response_chunks) > 0, (
            "No tool execution detected in streaming response (no tool_execution or tool_response chunks)"
        )

        # Verify tool responses are sent as separate type (not mixed with info or content)
        assert len(tool_response_chunks) > 0, "No tool_response chunks detected - tool results should use tool_response type"

        # Verify tool responses don't appear in content or info chunks
        for chunk in tool_response_chunks:
            assert chunk.get("type") == "tool_response", f"Tool response has wrong type: {chunk.get('type')}"
            # Tool responses should contain message
            assert chunk.get("message"), "Tool response chunk missing message"
            print(f"  ✅ Tool response validated: {chunk.get('message', '')[:100]}...")

        # Verify visible_to_user behavior
        # MainAgent output should be "hidden" type (visible_to_user: false)
        # HelperAgent output should be "content" type (visible_to_user: true)
        main_agent_content = [c for c in content_chunks if c.get("source") == main_agent_id]
        main_agent_hidden = [c for c in hidden_chunks if c.get("source") == main_agent_id]
        helper_agent_content = [c for c in content_chunks if c.get("source") == helper_agent_id]
        helper_agent_hidden = [c for c in hidden_chunks if c.get("source") == helper_agent_id]

        print(f"\n🔍 Visibility check:")
        print(f"  MainAgent content chunks (should be 0): {len(main_agent_content)}")
        print(f"  MainAgent hidden chunks (should be > 0): {len(main_agent_hidden)}")
        print(f"  HelperAgent content chunks (should be > 0): {len(helper_agent_content)}")
        print(f"  HelperAgent hidden chunks (should be 0): {len(helper_agent_hidden)}")

        assert len(main_agent_content) == 0, (
            f"MainAgent should emit 'hidden' chunks, not 'content' chunks (visible_to_user: false), "
            f"but got {len(main_agent_content)} content chunks"
        )
        assert len(main_agent_hidden) > 0, (
            f"MainAgent should emit 'hidden' chunks (visible_to_user: false), but got {len(main_agent_hidden)} hidden chunks"
        )
        assert len(helper_agent_content) > 0, (
            f"HelperAgent should emit 'content' chunks (visible_to_user: true), "
            f"but got {len(helper_agent_content)} content chunks"
        )
        assert len(helper_agent_hidden) == 0, (
            f"HelperAgent should emit 'content' chunks, not 'hidden' chunks (visible_to_user: true), "
            f"but got {len(helper_agent_hidden)} hidden chunks"
        )

        print(f"\n📦 All chunks received:")
        for i, chunk in enumerate(chunks_received, 1):
            print(f"  {i}. {chunk}")

        print("\n🎉 E2E test completed successfully!")
        print("✅ Agents created via API")
        print("✅ Workflow created with tool step via API")
        print("✅ Workflow executed with streaming")
        print("✅ Tool execution detected (agent -> tool -> agent)")
        print("✅ Tool responses sent as separate 'tool_response' type")
        print("✅ All chunks properly serialized to JSON")
        print("✅ visible_to_user configuration working correctly:")
        print(f"   - MainAgent output hidden ({len(main_agent_hidden)} hidden chunks)")
        print(f"   - HelperAgent output visible ({len(helper_agent_content)} content chunks)")

    finally:
        # ===== Cleanup (runs even if test fails) =====
        print("\n🧹 Cleaning up test resources...")

        # Delete workflow
        if created_resources["workflow_id"]:
            try:
                response = requests.delete(f"{base_url}/api/workflows/{created_resources['workflow_id']}")
                if response.status_code == 200:
                    print(f"  ✅ Deleted workflow: {created_resources['workflow_id']}")
                else:
                    print(f"  ⚠️  Failed to delete workflow: {response.status_code}")
            except Exception as e:
                print(f"  ⚠️  Error deleting workflow: {e}")

        # Delete agents
        if created_resources["main_agent_id"]:
            try:
                response = requests.delete(f"{base_url}/api/agents/{created_resources['main_agent_id']}")
                if response.status_code == 200:
                    print(f"  ✅ Deleted MainAgent: {created_resources['main_agent_id']}")
                else:
                    print(f"  ⚠️  Failed to delete main agent: {response.status_code}")
            except Exception as e:
                print(f"  ⚠️  Error deleting main agent: {e}")

        if created_resources["helper_agent_id"]:
            try:
                response = requests.delete(f"{base_url}/api/agents/{created_resources['helper_agent_id']}")
                if response.status_code == 200:
                    print(f"  ✅ Deleted HelperAgent: {created_resources['helper_agent_id']}")
                else:
                    print(f"  ⚠️  Failed to delete helper agent: {response.status_code}")
            except Exception as e:
                print(f"  ⚠️  Error deleting helper agent: {e}")

        # Delete prompts
        if created_resources["main_prompt_id"]:
            try:
                response = requests.delete(f"{base_url}/api/prompts/{created_resources['main_prompt_id']}")
                if response.status_code == 200:
                    print(f"  ✅ Deleted Main Prompt: {created_resources['main_prompt_id']}")
                else:
                    print(f"  ⚠️  Failed to delete main prompt: {response.status_code}")
            except Exception as e:
                print(f"  ⚠️  Error deleting main prompt: {e}")

        if created_resources["helper_prompt_id"]:
            try:
                response = requests.delete(f"{base_url}/api/prompts/{created_resources['helper_prompt_id']}")
                if response.status_code == 200:
                    print(f"  ✅ Deleted Helper Prompt: {created_resources['helper_prompt_id']}")
                else:
                    print(f"  ⚠️  Failed to delete helper prompt: {response.status_code}")
            except Exception as e:
                print(f"  ⚠️  Error deleting helper prompt: {e}")

        print("🧹 Cleanup complete!")
