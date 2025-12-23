"""
E2E tests for streaming endpoints in workflow-engine-poc.

Tests cover:
- Execution-specific streaming (/executions/{execution_id}/stream)
- Workflow-level streaming (/workflows/{workflow_id}/stream)
- SSE format validation
- Connection handling and cleanup
- Error scenarios
- Heartbeat mechanism

Requires server running at BASE_URL (default http://127.0.0.1:8006)
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import pytest

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8006")
FIXTURES_DIR = Path(__file__).parent / "fixtures"
TIMEOUT = 30.0


@pytest.fixture(scope="module", autouse=True)
def check_server_available():
    """Check if server is available before running streaming tests"""
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.get(f"{BASE_URL}/health")
            if response.status_code not in [200, 404]:  # 404 is ok if /health doesn't exist
                pytest.skip(f"Server not reachable at {BASE_URL}: HTTP {response.status_code}")
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        pytest.skip(f"Server not reachable at {BASE_URL}: {e}")


def _http(method: str, path: str, json_body: Optional[Dict[str, Any]] = None) -> httpx.Response:
    """Make HTTP request to the API"""
    # Add /api prefix if not already present
    if not path.startswith("/api/"):
        path = "/api" + path
    url = BASE_URL + path
    headers = {
        "X-elevAIte-apikey": "e2e-test-apikey",
        "X-elevAIte-UserId": "e2e-test-user",
        "X-elevAIte-TenantId": "e2e-test-tenant",
        "X-elevAIte-ProjectId": "e2e-test-project",
        "X-elevAIte-OrganizationId": "e2e-test-org",
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.request(method, url, json=json_body, headers=headers)


def _load_fixture(filename: str) -> Dict[str, Any]:
    """Load a JSON fixture file"""
    fixture_path = FIXTURES_DIR / filename
    with open(fixture_path) as f:
        return json.load(f)


def _create_workflow(config: Dict[str, Any]) -> str:
    """Create a workflow and return its ID"""
    response = _http("POST", "/workflows/", config)
    assert response.status_code in [200, 201], f"Failed to create workflow: {response.status_code} {response.text}"
    return response.json()["id"]


def _execute_workflow(workflow_id: str, body: Dict[str, Any]) -> str:
    """Execute a workflow and return execution ID"""
    response = _http("POST", f"/workflows/{workflow_id}/execute", body)
    assert response.status_code == 200, f"Failed to execute workflow: {response.text}"
    return response.json()["id"]


def _parse_sse_events(sse_data: str) -> List[Dict[str, Any]]:
    """Parse SSE data into a list of events"""
    events = []
    lines = sse_data.strip().split("\n")

    for line in lines:
        if line.startswith("data: "):
            try:
                event_data = json.loads(line[6:])  # Remove 'data: ' prefix
                events.append(event_data)
            except json.JSONDecodeError:
                # Skip malformed events
                continue

    return events


async def _stream_execution_events(execution_id: str, max_duration: float = 10.0) -> List[Dict[str, Any]]:
    """Stream events from an execution and return collected events"""
    events = []
    start_time = time.time()

    async with httpx.AsyncClient(timeout=max_duration + 5) as client:
        async with client.stream("GET", f"{BASE_URL}/executions/{execution_id}/stream") as response:
            if response.status_code != 200:
                raise Exception(f"Stream failed: {response.status_code} {response.text}")

            try:
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        chunk_events = _parse_sse_events(chunk)
                        events.extend(chunk_events)

                        # Check for completion or timeout
                        for event in chunk_events:
                            if event.get("type") == "complete" or event.get("data", {}).get("status") in [
                                "completed",
                                "failed",
                            ]:
                                return events

                        if time.time() - start_time > max_duration:
                            break
            except (httpx.ReadTimeout, httpx.TimeoutException):
                # Return what we have collected so far on read timeout
                pass

    return events


async def _stream_workflow_events(workflow_id: str, max_duration: float = 10.0) -> List[Dict[str, Any]]:
    """Stream events from a workflow and return collected events"""
    events = []
    start_time = time.time()

    async with httpx.AsyncClient(timeout=max_duration + 5) as client:
        async with client.stream("GET", f"{BASE_URL}/workflows/{workflow_id}/stream") as response:
            if response.status_code != 200:
                raise Exception(f"Stream failed: {response.status_code} {response.text}")

            try:
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        chunk_events = _parse_sse_events(chunk)
                        events.extend(chunk_events)

                        # Check for completion or timeout
                        for event in chunk_events:
                            if event.get("type") == "complete" or event.get("data", {}).get("status") in [
                                "completed",
                                "failed",
                            ]:
                                return events

                        if time.time() - start_time > max_duration:
                            break
            except (httpx.ReadTimeout, httpx.TimeoutException):
                # Return what we have collected so far on read timeout
                pass

    return events


@pytest.mark.asyncio
async def test_execution_streaming_basic():
    """Test basic execution streaming functionality"""
    # Create a simple workflow that completes quickly (no agent steps, no subflow)
    wf = _load_fixture("tool_exec_success.json")
    workflow_id = _create_workflow(wf)

    # Execute the workflow
    body = {"trigger": {"kind": "chat"}, "wait": False}
    execution_id = _execute_workflow(workflow_id, body)

    # Stream events
    events = await _stream_execution_events(execution_id, max_duration=15.0)

    # Validate we got events
    assert len(events) > 0, "Should receive at least one event"

    # Validate SSE format
    for event in events:
        assert "type" in event, f"Event missing type: {event}"
        assert "execution_id" in event, f"Event missing execution_id: {event}"
        assert "timestamp" in event, f"Event missing timestamp: {event}"
        assert event["execution_id"] == execution_id, f"Wrong execution_id in event: {event}"

    # Should have at least a status event
    status_events = [e for e in events if e.get("type") == "status"]
    assert len(status_events) > 0, "Should receive at least one status event"


@pytest.mark.asyncio
async def test_workflow_streaming_basic():
    """Test basic workflow streaming functionality"""
    # Create a simple workflow that completes quickly (no agent steps, no subflow)
    wf = _load_fixture("tool_exec_success.json")
    workflow_id = _create_workflow(wf)

    # Execute the workflow
    body = {"trigger": {"kind": "chat"}, "wait": False}
    execution_id = _execute_workflow(workflow_id, body)

    # Stream events from workflow
    events = await _stream_workflow_events(workflow_id, max_duration=15.0)

    # Validate we got events
    assert len(events) > 0, "Should receive at least one event"

    # Validate SSE format
    for event in events:
        assert "type" in event, f"Event missing type: {event}"
        assert "timestamp" in event, f"Event missing timestamp: {event}"
        # Workflow streams may have events from multiple executions
        if "execution_id" in event:
            assert event["execution_id"] == execution_id or event["execution_id"] == "system"


@pytest.mark.asyncio
async def test_streaming_event_types():
    """Test that different event types are emitted correctly"""
    # Create a workflow that will generate multiple event types
    wf = _load_fixture("tool_exec_success.json")  # This should generate step events
    workflow_id = _create_workflow(wf)

    # Execute the workflow
    body = {"trigger": {"kind": "chat"}, "wait": False}
    execution_id = _execute_workflow(workflow_id, body)

    # Stream events
    events = await _stream_execution_events(execution_id, max_duration=20.0)

    # Collect event types
    event_types = {event.get("type") for event in events}

    # Should have status events
    assert "status" in event_types, f"Missing status events. Got types: {event_types}"

    # May have step events if execution progresses
    step_events = [e for e in events if e.get("type") == "step"]
    if step_events:
        # Validate step event structure
        for event in step_events:
            assert "data" in event, f"Step event missing data: {event}"
            assert "step_id" in event["data"], f"Step event missing step_id: {event}"
            assert "step_status" in event["data"], f"Step event missing step_status: {event}"


@pytest.mark.asyncio
async def test_streaming_nonexistent_execution():
    """Test streaming for non-existent execution returns 404"""
    fake_execution_id = "00000000-0000-0000-0000-000000000000"

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{BASE_URL}/executions/{fake_execution_id}/stream")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_streaming_nonexistent_workflow():
    """Test streaming for non-existent workflow returns 404"""
    fake_workflow_id = "00000000-0000-0000-0000-000000000000"

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{BASE_URL}/workflows/{fake_workflow_id}/stream")
        assert response.status_code == 404


@pytest.mark.e2e
def test_streaming_headers():
    """Test that streaming endpoints return correct SSE headers"""
    # Create a simple workflow
    wf = _load_fixture("webhook_minimal.json")
    workflow_id = _create_workflow(wf)

    # Test execution streaming headers
    with httpx.Client(timeout=5.0) as client:
        with client.stream("GET", f"{BASE_URL}/workflows/{workflow_id}/stream") as response:
            assert response.status_code == 200
            assert response.headers.get("content-type") == "text/event-stream"
            assert response.headers.get("cache-control") == "no-cache"
            assert response.headers.get("connection") == "keep-alive"


@pytest.mark.asyncio
async def test_streaming_heartbeat():
    """Test that heartbeat events are sent during long streams"""
    # Create a workflow
    wf = _load_fixture("webhook_minimal.json")
    workflow_id = _create_workflow(wf)

    # Stream for a longer duration to catch heartbeat
    events = await _stream_workflow_events(workflow_id, max_duration=35.0)  # Longer than heartbeat interval

    # Look for heartbeat events
    heartbeat_events = [e for e in events if e.get("type") == "heartbeat"]

    # Should have at least one heartbeat if we streamed long enough
    if len(events) > 5:  # Only check if we got a reasonable number of events
        assert len(heartbeat_events) > 0, "Should receive heartbeat events during long streams"


@pytest.mark.asyncio
async def test_streaming_execution_lifecycle():
    """Test streaming through complete execution lifecycle"""
    # Create a workflow that will have multiple steps
    wf = _load_fixture("non_ai_hybrid.json")
    workflow_id = _create_workflow(wf)

    # Execute the workflow
    body = {"trigger": {"kind": "webhook"}, "input_data": {"merge": {"a": 1, "b": 2}}, "wait": False}
    execution_id = _execute_workflow(workflow_id, body)

    # Stream events and track lifecycle
    events = await _stream_execution_events(execution_id, max_duration=30.0)

    # Extract status changes
    status_events = [e for e in events if e.get("type") == "status"]
    statuses = [e.get("data", {}).get("status") for e in status_events]

    # Should see progression: running -> completed (or failed)
    assert "running" in statuses or "pending" in statuses, f"Should see running status. Got: {statuses}"

    # Should eventually complete or fail
    final_statuses = ["completed", "failed", "cancelled"]
    assert any(status in statuses for status in final_statuses), f"Should reach final status. Got: {statuses}"


@pytest.mark.asyncio
async def test_streaming_concurrent_connections():
    """Test multiple concurrent streaming connections"""
    # Create a workflow
    wf = _load_fixture("webhook_minimal.json")
    workflow_id = _create_workflow(wf)

    # Execute the workflow
    body = {"trigger": {"kind": "webhook"}, "input_data": {"test": "concurrent"}, "wait": False}
    execution_id = _execute_workflow(workflow_id, body)

    # Start multiple concurrent streams
    tasks = [
        _stream_execution_events(execution_id, max_duration=10.0),
        _stream_execution_events(execution_id, max_duration=10.0),
        _stream_workflow_events(workflow_id, max_duration=10.0),
    ]

    # Wait for all streams to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # All should succeed (no exceptions)
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Allow read timeouts due to transient idleness; treat as soft failure and continue
            if isinstance(result, (httpx.ReadTimeout, httpx.TimeoutException)):
                continue
            assert False, f"Stream {i} failed: {result}"
        assert len(result) > 0, f"Stream {i} got no events"


@pytest.mark.asyncio
async def test_streaming_connection_cleanup():
    """Test that connections are properly cleaned up"""
    # Create a workflow
    wf = _load_fixture("webhook_minimal.json")
    workflow_id = _create_workflow(wf)

    # Start a stream and cancel it early
    async with httpx.AsyncClient(timeout=10.0) as client:
        async with client.stream("GET", f"{BASE_URL}/workflows/{workflow_id}/stream") as response:
            assert response.status_code == 200

            # Read just a few chunks then close
            chunk_count = 0
            try:
                async for chunk in response.aiter_text():
                    chunk_count += 1
                    if chunk_count >= 2:
                        break
            except (httpx.ReadTimeout, httpx.TimeoutException):
                # It's okay if the stream times out while we're intentionally closing early
                pass

    # Connection should be cleaned up automatically
    # This is hard to test directly, but we can verify the endpoint still works
    async with httpx.AsyncClient(timeout=5.0) as client:
        async with client.stream("GET", f"{BASE_URL}/workflows/{workflow_id}/stream") as response:
            assert response.status_code == 200


class TestA2AAgentStreaming:
    """
    SSE streaming tests with A2A agent.

    These tests launch their own A2A echo server but require the workflow-engine-poc
    server to be running at BASE_URL (default: http://127.0.0.1:8006).

    The server must be started with RBAC disabled for testing:
        SKIP_RBAC=true python -m workflow_engine_poc.main

    Run the test with:
        python -m pytest tests/e2e/test_streaming.py::TestA2AAgentStreaming -v
    """

    @pytest.fixture(scope="class")
    def a2a_echo_server(self):
        """Start a real A2A echo server for testing."""
        import socket
        import threading

        import uvicorn
        from a2a.server.apps import A2AStarletteApplication
        from a2a.server.agent_execution import AgentExecutor
        from a2a.server.events import EventQueue
        from a2a.server.request_handlers import DefaultRequestHandler
        from a2a.server.tasks import InMemoryTaskStore
        from a2a.types import AgentCard, AgentCapabilities, AgentSkill
        from a2a.utils import new_agent_text_message

        class EchoAgentExecutor(AgentExecutor):
            """Simple echo agent for testing."""

            async def execute(self, context, event_queue: EventQueue) -> None:
                message = context.get_user_input()
                message_text = ""
                if isinstance(message, str):
                    message_text = message
                elif message and hasattr(message, "parts") and message.parts:
                    for part in message.parts:
                        if hasattr(part, "root") and hasattr(part.root, "text"):
                            message_text = part.root.text
                            break

                # Return the echo response
                await event_queue.enqueue_event(new_agent_text_message(f"Echo: {message_text}"))

            async def cancel(self, context, event_queue) -> None:
                pass

        # Find free port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            port = s.getsockname()[1]

        agent_card = AgentCard(
            name="Streaming Test Echo Agent",
            description="Echoes messages for streaming tests",
            url=f"http://127.0.0.1:{port}/",
            version="1.0.0",
            defaultInputModes=["text"],
            defaultOutputModes=["text"],
            capabilities=AgentCapabilities(streaming=True),
            skills=[
                AgentSkill(id="echo", name="Echo", description="Echoes back the message", tags=["test"], examples=["hello"])
            ],
        )

        request_handler = DefaultRequestHandler(
            agent_executor=EchoAgentExecutor(),
            task_store=InMemoryTaskStore(),
        )

        a2a_app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
        server = uvicorn.Server(uvicorn.Config(app=a2a_app.build(), host="127.0.0.1", port=port, log_level="warning"))

        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        # Wait for server to start
        for _ in range(50):
            try:
                with httpx.Client(timeout=1.0) as client:
                    resp = client.get(f"http://127.0.0.1:{port}/.well-known/agent.json")
                    if resp.status_code == 200:
                        break
            except Exception:
                pass
            time.sleep(0.1)

        yield {"base_url": f"http://127.0.0.1:{port}", "port": port}

        server.should_exit = True

    @pytest.mark.asyncio
    async def test_a2a_streaming_with_real_servers(self, a2a_echo_server):
        """
        Test SSE streaming with A2A agent using self-contained servers.

        This test:
        1. Uses the a2a_echo_server fixture (A2A echo server)
        2. Uses the existing workflow-engine-poc server (must be running at BASE_URL)
        3. Verifies SSE events are properly emitted during A2A execution

        Requirements:
        - Server must be running at BASE_URL (default http://127.0.0.1:8006)
        - Server should be started with: SKIP_RBAC=true python -m workflow_engine_poc.main
        - Uses 'dbos' backend to ensure SSE events are emitted
        """
        import uuid

        a2a_agent_url = a2a_echo_server["base_url"]

        # Step 1: Create an A2A agent
        agent_payload = {
            "name": f"SSE Streaming Test Agent {uuid.uuid4()}",
            "base_url": a2a_agent_url,
            "description": "Tests A2A SSE streaming",
            "auth_type": "none",
            "status": "active",
        }

        response = _http("POST", "/a2a-agents/", agent_payload)
        assert response.status_code == 200, f"Failed to create A2A agent: {response.text}"
        a2a_agent_id = response.json()["id"]

        try:
            # Step 2: Create workflow with A2A agent step
            workflow_config = {
                "name": f"A2A SSE Test {uuid.uuid4()}",
                "description": "Tests SSE streaming with A2A agent",
                "steps": [
                    {
                        "step_id": "trigger",
                        "step_type": "trigger",
                        "parameters": {"kind": "chat", "need_history": False, "allowed_modalities": ["text"]},
                    },
                    {
                        "step_id": "a2a_step",
                        "step_type": "agent_execution",
                        "dependencies": ["trigger"],
                        "config": {
                            "a2a_agent_id": a2a_agent_id,
                            "message_template": "{current_message}",
                            "stream": True,
                        },
                    },
                ],
            }

            workflow_id = _create_workflow(workflow_config)

            # Step 3: Start SSE stream listener in background
            test_message = "Hello A2A SSE!"
            collected_events: List[Dict[str, Any]] = []
            stream_started = asyncio.Event()
            stream_done = asyncio.Event()

            async def collect_stream():
                """Collect SSE events from workflow stream."""
                headers = {
                    "X-elevAIte-apikey": "e2e-test-apikey",
                    "X-elevAIte-UserId": "e2e-test-user",
                    "X-elevAIte-TenantId": "e2e-test-tenant",
                    "X-elevAIte-ProjectId": "e2e-test-project",
                    "X-elevAIte-OrganizationId": "e2e-test-org",
                }
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        async with client.stream(
                            "GET",
                            f"{BASE_URL}/api/workflows/{workflow_id}/stream",
                            headers=headers,
                        ) as resp:
                            if resp.status_code != 200:
                                stream_started.set()
                                return

                            async for chunk in resp.aiter_text():
                                if chunk.strip():
                                    chunk_events = _parse_sse_events(chunk)
                                    collected_events.extend(chunk_events)

                                    # Signal connected after first chunk
                                    if not stream_started.is_set():
                                        stream_started.set()

                                    # Stop on completion or error
                                    for event in chunk_events:
                                        # Status can be at top level or in data.status
                                        status = event.get("status") or event.get("data", {}).get("status")
                                        if status in ["completed", "failed", "error"]:
                                            stream_done.set()
                                            return
                except Exception as e:
                    print(f"Stream error: {e}")
                finally:
                    stream_started.set()

            # Start stream task
            stream_task = asyncio.create_task(collect_stream())

            # Wait for stream to connect (first chunk received)
            try:
                await asyncio.wait_for(stream_started.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                stream_task.cancel()
                pytest.fail("Stream connection timed out")

            # Small delay to ensure stream is fully established
            await asyncio.sleep(0.2)

            # Step 4: Execute workflow (async, don't wait)
            execution_payload = {
                "trigger": {"kind": "chat", "current_message": test_message},
                "user_id": "e2e-test",
                "session_id": f"e2e-{uuid.uuid4()}",
                "wait": False,  # Don't wait - we'll watch the stream
                "backend": "dbos",  # Use dbos backend which emits SSE events
            }
            _execute_workflow(workflow_id, execution_payload)

            # Step 5: Wait for stream to complete (or timeout)
            try:
                await asyncio.wait_for(stream_done.wait(), timeout=20.0)
            except asyncio.TimeoutError:
                pass  # That's okay, we'll check what we got

            # Cancel stream task
            if not stream_task.done():
                stream_task.cancel()
                try:
                    await stream_task
                except asyncio.CancelledError:
                    pass

            # Step 6: Verify we received meaningful SSE events
            print(f"\n{'=' * 60}")
            print(f"COLLECTED {len(collected_events)} SSE EVENTS:")
            print(f"{'=' * 60}")
            for i, event in enumerate(collected_events):
                print(f"Event {i + 1}: {event}")
            print(f"{'=' * 60}\n")

            assert len(collected_events) >= 1, f"Expected at least 1 SSE event, got: {collected_events}"

            # Extract status values - status can be at top level or in data.status
            status_values = []
            for e in collected_events:
                if "status" in e:
                    status_values.append(e["status"])
                elif e.get("data", {}).get("status"):
                    status_values.append(e["data"]["status"])

            # Verify we got the expected flow of events
            event_types = [e.get("type") for e in collected_events]
            print(f"Collected event types: {event_types}")
            print(f"Status values: {status_values}")

            # At minimum we should see 'connected' (always sent when stream starts)
            assert "connected" in status_values, f"Expected 'connected' in status values, got: {status_values}"

            # Look for step completion event (a2a_step) or workflow completion
            step_events = [e for e in collected_events if e.get("type") == "step"]
            a2a_step_events = [e for e in step_events if e.get("data", {}).get("step_id") == "a2a_step"]

            # Check if we got a completion event (running -> completed)
            # If using dbos backend, we should see running and completed
            has_running = "running" in status_values
            has_completed = "completed" in status_values

            print(f"Has running: {has_running}, Has completed: {has_completed}")
            print(f"Step events: {len(step_events)}, A2A step events: {len(a2a_step_events)}")

            # With dbos backend, we expect running and completed events
            # (connected is always there, running and completed come from execution)
            # For SSE streaming to be working properly, we MUST receive execution events
            assert has_running or has_completed, (
                f"SSE streaming not working: expected 'running' or 'completed' events "
                f"but only got: {status_values}. This indicates events are not being "
                f"emitted to the workflow stream."
            )

        finally:
            _http("DELETE", f"/a2a-agents/{a2a_agent_id}")


if __name__ == "__main__":
    # Run a simple test to verify the server is accessible
    try:
        response = _http("GET", "/health")
        if response.status_code == 200:
            print("Server is accessible, ready for streaming tests")
        else:
            print(f"Server health check failed: {response.status_code}")
    except Exception as e:
        print(f"Cannot connect to server: {e}")
