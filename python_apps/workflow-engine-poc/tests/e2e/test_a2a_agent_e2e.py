"""
End-to-end tests for A2A agent execution through the full stack.

Tests the complete flow:
1. Start a real A2A echo server
2. Create an A2A agent record via API
3. Create a workflow with an agent_execution step using a2a_agent_id
4. Execute the workflow via POST /workflows/{id}/execute
5. Verify the response contains the echo from the A2A server
"""

import socket
import time
import uuid
from threading import Thread

import pytest
import uvicorn


def get_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


class EchoAgentExecutor:
    """Simple echo agent for testing - echoes back the message."""

    async def execute(self, context, event_queue) -> None:
        from a2a.utils import new_agent_text_message

        # Extract message text from context
        message_text = "No message"
        if context.message and context.message.parts:
            for part in context.message.parts:
                if hasattr(part, "root") and hasattr(part.root, "text"):
                    message_text = part.root.text
                    break
                elif hasattr(part, "text"):
                    message_text = part.text
                    break

        # Echo it back with prefix
        await event_queue.enqueue_event(new_agent_text_message(f"Echo: {message_text}"))

    async def cancel(self, context, event_queue) -> None:
        pass


@pytest.fixture(scope="module")
def a2a_echo_server():
    """Start a real A2A echo server for testing."""
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    from a2a.types import AgentCapabilities, AgentCard, AgentSkill

    port = get_free_port()

    agent_card = AgentCard(
        name="E2E Test Echo Agent",
        description="Echoes messages for E2E testing",
        url=f"http://127.0.0.1:{port}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[
            AgentSkill(
                id="echo",
                name="Echo",
                description="Echoes back the message",
                tags=["test"],
                examples=["hello"],
            )
        ],
    )

    request_handler = DefaultRequestHandler(
        agent_executor=EchoAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    config = uvicorn.Config(
        app.build(), host="127.0.0.1", port=port, log_level="warning"
    )
    server = uvicorn.Server(config)

    # Run server in a background thread
    thread = Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to be ready
    import time

    for _ in range(50):  # 5 seconds max
        try:
            import httpx

            httpx.get(f"http://127.0.0.1:{port}/.well-known/agent.json", timeout=0.1)
            break
        except Exception:
            time.sleep(0.1)

    yield {
        "base_url": f"http://127.0.0.1:{port}",
        "agent_name": "E2E Test Echo Agent",
        "port": port,
    }


class TestA2AAgentE2E:
    """End-to-end tests for A2A agent execution through the full workflow stack."""

    @pytest.mark.asyncio
    async def test_full_workflow_with_a2a_agent(self, async_client, a2a_echo_server):
        """
        Full E2E test: API -> Workflow Engine -> A2A Agent -> Echo Server -> Response

        This test:
        1. Creates an A2A agent record via the API
        2. Creates a workflow with an agent_execution step that uses a2a_agent_id
        3. Executes the workflow via POST /workflows/{id}/execute
        4. Verifies the response contains the echo from the A2A server
        """
        client = async_client

        # Step 1: Create A2A agent via API
        a2a_agent_payload = {
            "name": a2a_echo_server["agent_name"],
            "base_url": a2a_echo_server["base_url"],
            "description": "E2E test echo agent",
            "auth_type": "none",
            "status": "active",
        }

        response = await client.post("/a2a-agents/", json=a2a_agent_payload)
        assert response.status_code in [200, 201], (
            f"Failed to create A2A agent: {response.text}"
        )
        a2a_agent = response.json()
        a2a_agent_id = a2a_agent["id"]

        # Step 2: Create workflow with A2A agent step
        workflow_id = str(uuid.uuid4())
        test_message = "Hello from E2E test!"

        workflow_payload = {
            "workflow_id": workflow_id,
            "name": "E2E A2A Test Workflow",
            "description": "Tests A2A agent execution end-to-end",
            "execution_pattern": "sequential",
            "steps": [
                {
                    "step_id": "trigger",
                    "step_type": "trigger",
                    "step_order": 1,
                    "parameters": {"kind": "chat"},
                },
                {
                    "step_id": "a2a_agent_step",
                    "step_name": "A2A Echo Agent",
                    "step_type": "agent_execution",
                    "step_order": 2,
                    "dependencies": ["trigger"],
                    "config": {
                        "a2a_agent_id": a2a_agent_id,
                        "query": "{current_message}",
                        "stream": False,
                    },
                },
            ],
        }

        response = await client.post("/workflows/", json=workflow_payload)
        assert response.status_code in [200, 201], (
            f"Failed to create workflow: {response.text}"
        )
        created_workflow = response.json()
        created_workflow_id = created_workflow["id"]

        # Step 3: Execute the workflow (don't wait - poll instead for better test isolation)
        execution_payload = {
            "trigger": {
                "kind": "chat",
                "current_message": test_message,
            },
            "user_id": "e2e-test-user",
            "session_id": f"e2e-a2a-test-{uuid.uuid4()}",
            "wait": False,  # Don't wait - poll for completion
        }

        response = await client.post(
            f"/workflows/{created_workflow_id}/execute", json=execution_payload
        )
        assert response.status_code == 200, (
            f"Failed to execute workflow: {response.text}"
        )
        execution_result = response.json()
        execution_id = execution_result["id"]

        # Step 4: Poll for execution completion
        execution_status = None
        for _ in range(30):  # Poll for up to 15 seconds
            time.sleep(0.5)
            response = await client.get(f"/executions/{execution_id}")
            assert response.status_code == 200, (
                f"Failed to get execution: {response.text}"
            )
            execution_status = response.json()
            if execution_status.get("status") in [
                "completed",
                "COMPLETED",
                "failed",
                "FAILED",
            ]:
                break

        assert execution_status is not None
        assert execution_status.get("status") in [
            "completed",
            "COMPLETED",
        ], f"Execution did not complete: {execution_status}"

        # Step 5: Get the full execution results (includes step_results and step_io_data)
        response = await client.get(f"/executions/{execution_id}/results")
        assert response.status_code == 200, (
            f"Failed to get execution results: {response.text}"
        )
        execution_details = response.json()

        # The API returns step_results from memory (with output_data nested), or step_io_data from db_record
        step_results = execution_details.get("step_results", {})
        a2a_step_result = {}

        if step_results and "a2a_agent_step" in step_results:
            # From memory: step_results["a2a_agent_step"]["output_data"] contains the actual result
            a2a_step_result = step_results["a2a_agent_step"].get("output_data", {})
        else:
            # Fallback to step_io_data (from memory or db_record)
            step_io_data = execution_details.get("step_io_data", {})
            if not step_io_data:
                db_record = execution_details.get("db_record", {})
                step_io_data = db_record.get("step_io_data", {})
            a2a_step_result = step_io_data.get("a2a_agent_step", {})

        # The echo server should have echoed back our message
        assert a2a_step_result.get("success") is True, (
            f"A2A step failed: {a2a_step_result}"
        )
        assert a2a_step_result.get("mode") == "a2a", (
            f"Expected A2A mode: {a2a_step_result}"
        )
        assert f"Echo: {test_message}" in a2a_step_result.get("response", ""), (
            f"Echo not found in response: {a2a_step_result}"
        )

        # Cleanup: Delete the A2A agent
        await client.delete(f"/a2a-agents/{a2a_agent_id}")

    @pytest.mark.asyncio
    async def test_a2a_agent_with_template_interpolation(
        self, async_client, a2a_echo_server
    ):
        """
        E2E test for template interpolation in A2A agent queries.

        Tests that {variable} placeholders in the query are correctly
        interpolated from input_data before being sent to the A2A agent.
        """
        client = async_client

        # Create A2A agent
        a2a_agent_payload = {
            "name": f"Template Test Agent {uuid.uuid4()}",
            "base_url": a2a_echo_server["base_url"],
            "description": "Template interpolation test",
            "auth_type": "none",
            "status": "active",
        }

        response = await client.post("/a2a-agents/", json=a2a_agent_payload)
        assert response.status_code in [200, 201]
        a2a_agent_id = response.json()["id"]

        # Create workflow with template query
        workflow_payload = {
            "workflow_id": str(uuid.uuid4()),
            "name": "Template Interpolation Test",
            "steps": [
                {
                    "step_id": "trigger",
                    "step_type": "trigger",
                    "step_order": 1,
                    "parameters": {"kind": "webhook"},
                },
                {
                    "step_id": "a2a_step",
                    "step_type": "agent_execution",
                    "step_order": 2,
                    "dependencies": ["trigger"],
                    "config": {
                        "a2a_agent_id": a2a_agent_id,
                        "query": "Hello {name}, your order {order_id} is ready!",
                        "stream": False,
                    },
                },
            ],
        }

        response = await client.post("/workflows/", json=workflow_payload)
        assert response.status_code in [200, 201]
        workflow_id = response.json()["id"]

        # Execute with input_data containing template variables (don't wait - poll instead)
        execution_payload = {
            "trigger": {"kind": "webhook"},
            "input_data": {
                "name": "Alice",
                "order_id": "ORD-12345",
            },
            "user_id": "e2e-test",
            "session_id": f"e2e-template-{uuid.uuid4()}",
            "wait": False,  # Don't wait - poll for completion
        }

        response = await client.post(
            f"/workflows/{workflow_id}/execute", json=execution_payload
        )
        assert response.status_code == 200
        execution_result = response.json()
        execution_id = execution_result["id"]

        # Poll for execution completion
        execution_status = None
        for _ in range(30):  # Poll for up to 15 seconds
            time.sleep(0.5)
            response = await client.get(f"/executions/{execution_id}")
            assert response.status_code == 200
            execution_status = response.json()
            if execution_status.get("status") in [
                "completed",
                "COMPLETED",
                "failed",
                "FAILED",
            ]:
                break

        assert execution_status is not None
        assert execution_status.get("status") in ["completed", "COMPLETED"]

        # Get the full execution results (includes step_results and step_io_data)
        response = await client.get(f"/executions/{execution_id}/results")
        assert response.status_code == 200, (
            f"Failed to get execution results: {response.text}"
        )
        execution_details = response.json()

        # The API returns step_results from memory (with output_data nested), or step_io_data from db_record
        step_results = execution_details.get("step_results", {})
        a2a_result = {}

        if step_results and "a2a_step" in step_results:
            # From memory: step_results["a2a_step"]["output_data"] contains the actual result
            a2a_result = step_results["a2a_step"].get("output_data", {})
        else:
            # Fallback to step_io_data (from memory or db_record)
            step_io_data = execution_details.get("step_io_data", {})
            if not step_io_data:
                db_record = execution_details.get("db_record", {})
                step_io_data = db_record.get("step_io_data", {})
            a2a_result = step_io_data.get("a2a_step", {})

        # Verify template was interpolated correctly
        assert a2a_result.get("success") is True, f"A2A step failed: {a2a_result}"
        expected_echo = "Echo: Hello Alice, your order ORD-12345 is ready!"
        assert expected_echo in a2a_result.get("response", ""), (
            f"Template not interpolated: {a2a_result}"
        )

        # Cleanup
        await client.delete(f"/a2a-agents/{a2a_agent_id}")

    @pytest.mark.asyncio
    async def test_a2a_agent_streaming(self, async_client, a2a_echo_server):
        """
        E2E test for A2A agent with streaming configuration.

        Verifies that the A2A agent step works correctly when configured for streaming,
        producing a valid response that can be streamed to clients.
        """
        client = async_client

        # Step 1: Create A2A agent
        unique_id = str(uuid.uuid4())
        agent_payload = {
            "name": f"Streaming Test Agent {unique_id}",
            "base_url": a2a_echo_server["base_url"],
            "description": "Tests A2A streaming",
            "auth_type": "none",
            "status": "active",
        }

        response = await client.post("/a2a-agents/", json=agent_payload)
        assert response.status_code in [200, 201], (
            f"Failed to create A2A agent: {response.text}"
        )
        a2a_agent_id = response.json()["id"]

        # Step 2: Create workflow with streaming enabled
        workflow_payload = {
            "workflow_id": str(uuid.uuid4()),
            "name": "Streaming A2A Test",
            "steps": [
                {
                    "step_id": "trigger",
                    "step_type": "trigger",
                    "step_order": 1,
                    "parameters": {"kind": "chat"},
                },
                {
                    "step_id": "a2a_streaming_step",
                    "step_type": "agent_execution",
                    "step_order": 2,
                    "dependencies": ["trigger"],
                    "config": {
                        "a2a_agent_id": a2a_agent_id,
                        "query": "{current_message}",
                        "stream": True,  # Enable streaming
                    },
                },
            ],
        }

        response = await client.post("/workflows/", json=workflow_payload)
        assert response.status_code in [200, 201]
        workflow_id = response.json()["id"]

        # Step 3: Execute the workflow
        test_message = "Hello streaming world!"
        execution_payload = {
            "trigger": {
                "kind": "chat",
                "current_message": test_message,
            },
            "user_id": "e2e-streaming-test",
            "session_id": f"e2e-streaming-{uuid.uuid4()}",
            "wait": False,
        }

        response = await client.post(
            f"/workflows/{workflow_id}/execute", json=execution_payload
        )
        assert response.status_code == 200
        execution_id = response.json()["id"]

        # Step 4: Poll for completion
        execution_status = None
        for _ in range(30):
            time.sleep(0.5)
            response = await client.get(f"/executions/{execution_id}")
            assert response.status_code == 200
            execution_status = response.json()
            if execution_status.get("status") in [
                "completed",
                "COMPLETED",
                "failed",
                "FAILED",
            ]:
                break

        assert execution_status is not None
        assert execution_status.get("status") in ["completed", "COMPLETED"]

        # Step 6: Get the full results and verify
        response = await client.get(f"/executions/{execution_id}/results")
        assert response.status_code == 200
        execution_details = response.json()

        step_results = execution_details.get("step_results", {})
        a2a_result = {}

        if step_results and "a2a_streaming_step" in step_results:
            a2a_result = step_results["a2a_streaming_step"].get("output_data", {})
        else:
            step_io_data = execution_details.get("step_io_data", {})
            if not step_io_data:
                db_record = execution_details.get("db_record", {})
                step_io_data = db_record.get("step_io_data", {})
            a2a_result = step_io_data.get("a2a_streaming_step", {})

        # Verify the A2A step completed successfully
        assert a2a_result.get("success") is True, (
            f"A2A streaming step failed: {a2a_result}"
        )
        assert f"Echo: {test_message}" in a2a_result.get("response", ""), (
            f"Echo not found: {a2a_result}"
        )

        # Verify the response structure is streaming-compatible (has response text)
        assert "response" in a2a_result, (
            f"Missing response field in A2A result: {a2a_result}"
        )
        assert isinstance(a2a_result["response"], str), (
            f"Response should be string: {a2a_result}"
        )
        assert len(a2a_result["response"]) > 0, (
            f"Response should not be empty: {a2a_result}"
        )

        # Cleanup
        await client.delete(f"/a2a-agents/{a2a_agent_id}")
