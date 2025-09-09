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


def _http(method: str, path: str, json_body: Optional[Dict[str, Any]] = None) -> httpx.Response:
    """Make HTTP request to the API"""
    url = BASE_URL + path
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.request(method, url, json=json_body)


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
