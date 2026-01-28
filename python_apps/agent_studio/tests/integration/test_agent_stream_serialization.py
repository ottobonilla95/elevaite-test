"""
Test for AgentStreamChunk JSON serialization during agent-to-agent streaming.

This test verifies that when Agent A calls Agent B as a tool during streaming,
the AgentStreamChunk objects are properly serialized to JSON without errors.
"""

import json
from typing import Any

import pytest
from sqlalchemy.orm import Session

from db import crud
from db.schemas import prompts as prompt_schemas
from db.schemas import agents as agent_schemas
from db.schemas import workflows as workflow_schemas


@pytest.mark.integration
def test_agent_to_agent_streaming_serialization(test_client, test_db_session: Session, monkeypatch):
    """
    Test that streaming properly serializes AgentStreamChunk objects to JSON.

    This test verifies the fix for "AgentStreamChunk is not JSON serializable" error
    by creating a simple workflow and streaming its execution.
    """

    # ===== Step 1: Create Two Agents (one will call the other) =====

    # First, create the helper agent that will be called as a tool
    prompt_helper = prompt_schemas.PromptCreate(
        prompt_label="Helper Agent Prompt",
        prompt="You are a helpful assistant. Answer questions concisely.",
        unique_label="HelperAgentPrompt",
        app_name="agent_studio_tests",
        version="1.0.0",
        ai_model_provider="openai",
        ai_model_name="gpt-4o-mini",
        tags=["test"],
        hyper_parameters={"temperature": "0.2"},
        variables={},
    )
    db_prompt_helper = crud.create_prompt(test_db_session, prompt_helper)

    agent_helper = agent_schemas.AgentCreate(
        name="HelperAgent",
        agent_type="api",
        description="Helper agent that will be called as a tool",
        system_prompt_id=db_prompt_helper.pid,
        persona="Helper",
        functions=[],
        routing_options={"respond": "Respond directly"},
        short_term_memory=False,
        long_term_memory=False,
        reasoning=False,
        input_type=["text"],
        output_type=["text"],
        response_type="json",
        max_retries=1,
        timeout=5,
        deployed=True,
        status="active",
        priority=None,
        failure_strategies=["retry"],
        collaboration_mode="single",
        available_for_deployment=True,
        deployment_code="hlp",
    )
    db_agent_helper = crud.create_agent(test_db_session, agent_helper)

    # Now create the main agent with a function to call the helper
    prompt_main = prompt_schemas.PromptCreate(
        prompt_label="Main Agent Prompt",
        prompt="You are an orchestrator. Use the HelperAgent tool to answer questions.",
        unique_label="MainAgentPrompt",
        app_name="agent_studio_tests",
        version="1.0.0",
        ai_model_provider="openai",
        ai_model_name="gpt-4o-mini",
        tags=["test"],
        hyper_parameters={"temperature": "0.2"},
        variables={},
    )
    db_prompt_main = crud.create_prompt(test_db_session, prompt_main)

    # # Create function definition for calling HelperAgent (as dict to avoid serialization issues)
    # helper_function: AgentFunction = {
    #     "type": "function",
    #     "function": {
    #         "name": "HelperAgent",
    #         "description": "Call the helper agent",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {"query": {"type": "string", "description": "The query"}},
    #             "required": ["query"],
    #         },
    #     },
    # }

    agent_main = agent_schemas.AgentCreate(
        name="MainAgent",
        agent_type="router",
        description="Main agent that calls other agents",
        system_prompt_id=db_prompt_main.pid,
        persona="Orchestrator",
        functions=[],
        routing_options={"respond": "Respond directly"},
        short_term_memory=False,
        long_term_memory=False,
        reasoning=False,
        input_type=["text"],
        output_type=["text"],
        response_type="json",
        max_retries=1,
        timeout=10,
        deployed=True,
        status="active",
        priority=None,
        failure_strategies=["retry"],
        collaboration_mode="single",
        available_for_deployment=True,
        deployment_code="main",
    )
    db_agent_main = crud.create_agent(test_db_session, agent_main)

    # ===== Step 2: Create Workflow with Both Agents and Connections =====
    config: dict[str, Any] = {
        "agents": [
            {
                "agent_type": db_agent_main.name,
                "agent_id": str(db_agent_main.agent_id),
                "position": {"x": 100, "y": 100},
            },
            {
                "agent_type": db_agent_helper.name,
                "agent_id": str(db_agent_helper.agent_id),
                "position": {"x": 300, "y": 100},
            },
        ],
        "connections": [
            {
                "source_agent_id": str(db_agent_main.agent_id),
                "target_agent_id": str(db_agent_helper.agent_id),
                "connection_type": "tool_call",
            }
        ],
    }

    wf = workflow_schemas.WorkflowCreate(
        name="StreamingSerializationTest",
        description="Test workflow for AgentStreamChunk serialization with agent-to-agent calls",
        version="1.0.0",
        configuration=config,
        created_by="test",
        is_active=True,
        is_editable=True,
        tags=["test", "streaming", "agent-to-agent"],
    )
    db_workflow = crud.create_workflow(test_db_session, wf)

    # Create the workflow connection in the database
    from db.schemas.workflows import WorkflowConnectionCreate, ConnectionType

    connection_data = WorkflowConnectionCreate(
        workflow_id=db_workflow.workflow_id,
        source_agent_id=db_agent_main.agent_id,
        target_agent_id=db_agent_helper.agent_id,
        connection_type=ConnectionType.DEFAULT,
    )
    crud.create_workflow_connection(test_db_session, connection_data)

    # ===== Step 3: Mock OpenAI Client to Simulate Agent Calling Another Agent =====
    import types
    import utils

    # Create proper mock objects that match OpenAI's streaming response structure
    class ToolCallFunction:
        def __init__(self, name=None, arguments=None):
            self.name = name
            self.arguments = arguments

    class ToolCallDelta:
        def __init__(self, index=0, id=None, type=None, function=None):
            self.index = index
            self.id = id
            self.type = type
            self.function = function

    class Delta:
        def __init__(self, content=None, tool_calls=None):
            self.content = content
            self.tool_calls = tool_calls

    class Choice:
        def __init__(self, delta=None, finish_reason=None):
            self.delta = delta or Delta()
            self.finish_reason = finish_reason

    class Chunk:
        def __init__(self, content=None, tool_calls=None, finish_reason=None):
            self.choices = [Choice(delta=Delta(content, tool_calls), finish_reason=finish_reason)]

    # Track API call count to simulate: 1) tool call decision, 2) tool execution (another agent), 3) final response
    call_count = [0]

    class StreamResp:
        def __iter__(self):
            call_count[0] += 1

            if call_count[0] == 1:
                # First call: Main agent decides to call HelperAgent as a tool
                print(f"\n🔵 Call {call_count[0]}: Agent deciding to call tool")
                # Yield tool call with proper object structure (not dicts)
                yield Chunk(
                    tool_calls=[
                        ToolCallDelta(
                            index=0,
                            id="call_test_123",
                            type="function",
                            function=ToolCallFunction(name="HelperAgent", arguments=""),
                        )
                    ]
                )
                yield Chunk(tool_calls=[ToolCallDelta(index=0, function=ToolCallFunction(arguments='{"query"'))])
                yield Chunk(tool_calls=[ToolCallDelta(index=0, function=ToolCallFunction(arguments=': "test"}'))])
                yield Chunk(finish_reason="tool_calls")
            elif call_count[0] == 2:
                # Second call: TestAgent (called as tool) responds with streaming
                print(f"\n🟢 Call {call_count[0]}: TestAgent (tool) responding")
                yield Chunk(content="Tool ")
                yield Chunk(content="response ")
                yield Chunk(content="from ")
                yield Chunk(content="agent")
                yield Chunk(finish_reason="stop")
            else:
                # Third call: Main agent provides final response after tool execution
                print(f"\n🟡 Call {call_count[0]}: Main agent final response")
                yield Chunk(content="Final ")
                yield Chunk(content="answer")
                yield Chunk(finish_reason="stop")

    mock_client = types.SimpleNamespace(
        chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda **kwargs: StreamResp()))
    )
    monkeypatch.setattr(utils, "client", mock_client, raising=True)

    # ===== Step 4: Execute Streaming Workflow =====
    payload = {
        "query": "Test query",
        "chat_history": [{"role": "user", "content": "Hello"}],  # Use chat_history to trigger streaming
        "session_id": "test_session",
        "user_id": "test_user",
    }

    chunks_received = []
    json_parse_errors = []

    with test_client.stream("POST", f"/api/workflows/{db_workflow.workflow_id}/stream", json=payload) as r:
        assert r.status_code == 200

        for line in r.iter_lines():
            if line.startswith("data: "):
                data_str = line[6:]  # Remove "data: " prefix

                try:
                    # This is where the JSON serialization error would occur
                    # if AgentStreamChunk wasn't properly converted to dict
                    chunk_data = json.loads(data_str)
                    chunks_received.append(chunk_data)
                except json.JSONDecodeError as e:
                    json_parse_errors.append({"error": str(e), "data": data_str})

    # ===== Step 5: Verify Results =====
    # Should have no JSON parsing errors - this is the main test!
    assert len(json_parse_errors) == 0, f"JSON parsing errors occurred: {json_parse_errors}"

    # Should have received multiple chunks
    assert len(chunks_received) > 0, "No chunks received from streaming endpoint"

    # Verify chunk structure - each chunk should be valid JSON
    content_chunks = []
    for chunk in chunks_received:
        # All chunks should be valid dicts (already verified by json.loads above)
        assert isinstance(chunk, dict), f"Chunk is not a dict: {chunk}"

        # Collect content chunks for verification
        if "type" in chunk and chunk["type"] == "content":
            content_chunks.append(chunk)
            # If data field exists and is a dict, verify it has the expected AgentStreamChunk structure
            if "data" in chunk and isinstance(chunk["data"], dict):
                # Should have either 'type' and 'message' (AgentStreamChunk) or be a simple dict
                if "type" in chunk["data"]:
                    assert "message" in chunk["data"], f"AgentStreamChunk data missing 'message': {chunk['data']}"

    print(f"\n✅ Test passed! Received {len(chunks_received)} chunks without JSON serialization errors")
    print(f"Content chunks: {len(content_chunks)}")
    print("\n📦 All chunks received:")
    for i, chunk in enumerate(chunks_received, 1):
        print(f"  {i}. {chunk}")
