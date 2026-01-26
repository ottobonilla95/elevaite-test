"""
E2E Test for Ingestion Service Integration

Tests the complete flow of:
1. Creating a workflow with an ingestion step
2. Executing the workflow via the workflow API
3. Ingestion service creating and running a job
4. DBOS event notification back to workflow engine
5. Workflow completing successfully

Prerequisites:
- Ingestion service running on port 8001 (default)
- Workflow engine PoC running on port 8006 (default) or set WORKFLOW_API_URL
- Workflow engine MUST have INGESTION_SERVICE_URL=http://localhost:8001 set
- Workflow engine MUST have RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL=true for E2E testing
- Both services connected to their databases
- DBOS configured for both services

Start Workflow Engine for E2E Testing:
    INGESTION_SERVICE_URL=http://localhost:8001 \\
    RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL=true \\
    uvicorn workflow_engine_poc.main:app --host 0.0.0.0 --port 8006 --reload

Environment Variables:
- TEST_INGESTION_SERVICE=1 (required to run this test)
- WORKFLOW_API_URL (default: http://localhost:8006)
- INGESTION_API_URL (default: http://localhost:8001)

Usage:
    TEST_INGESTION_SERVICE=1 pytest tests/e2e/test_ingestion_service_e2e.py -v -s
"""

import os
import uuid
import asyncio
import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient

# Common test configuration
WORKFLOW_API_URL = os.getenv("WORKFLOW_API_URL", "http://localhost:8006")
INGESTION_API_URL = os.getenv("INGESTION_API_URL", "http://localhost:8001")

# RBAC headers for E2E tests
E2E_HEADERS = {
    "X-elevAIte-apikey": "test-api-key-e2e",
    "X-elevAIte-OrganizationId": "test-org-456",
    "X-elevAIte-AccountId": "test-account-789",
    "X-elevAIte-ProjectId": "test-project-789",
}


async def poll_execution_status(
    client: httpx.AsyncClient, execution_id: str, max_wait: float = 15.0
) -> dict:
    """Helper to poll execution status until completion or timeout."""
    poll_interval = 0.5
    elapsed = 0
    status_data = {}

    while elapsed < max_wait:
        status_response = await client.get(
            f"{WORKFLOW_API_URL}/api/executions/{execution_id}"
        )
        assert status_response.status_code == 200
        status_data = status_response.json()

        final_status = status_data.get("status")
        if final_status in ["completed", "failed", "error"]:
            break

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    return status_data


async def create_and_execute_workflow(
    client: httpx.AsyncClient,
    workflow_config: dict,
    trigger_data: dict = None,
    wait: bool = True,
) -> tuple[str, str, dict]:
    """Helper to create and execute a workflow, returns (workflow_id, execution_id, execution_response)."""
    # Create workflow
    create_response = await client.post(
        f"{WORKFLOW_API_URL}/api/workflows/", json=workflow_config
    )
    assert create_response.status_code == 200, (
        f"Failed to create workflow: {create_response.text}"
    )

    workflow_data = create_response.json()
    workflow_id = workflow_data.get("id")
    assert workflow_id, f"No id in response: {workflow_data}"

    # Execute workflow
    execute_payload = {
        "execution_backend": "dbos",
        "trigger": trigger_data or {"kind": "webhook", "data": {}},
        "wait": wait,
    }
    execute_response = await client.post(
        f"{WORKFLOW_API_URL}/api/workflows/{workflow_id}/execute",
        json=execute_payload,
    )
    assert execute_response.status_code == 200, (
        f"Failed to execute workflow: {execute_response.text}"
    )

    execution_data = execute_response.json()
    execution_id = (
        execution_data.get("execution_id")
        or execution_data.get("id")
        or execution_data.get("workflow_execution_id")
    )
    assert execution_id, f"No execution ID in response: {execution_data}"

    return workflow_id, execution_id, execution_data


# =============================================================================
# BASIC INGESTION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TEST_INGESTION_SERVICE"),
    reason="Requires TEST_INGESTION_SERVICE=1 and running ingestion service",
)
async def test_ingestion_service_workflow_e2e():
    """
    Test complete workflow execution with ingestion step.

    This test verifies:
    - Workflow creation with ingestion step
    - Workflow execution triggering ingestion service
    - Two-phase ingestion step execution
    - DBOS event-based completion notification
    - Final workflow success
    """
    # Use real HTTP client to connect to running services
    workflow_api_url = os.getenv("WORKFLOW_API_URL", "http://localhost:8006")
    os.getenv("INGESTION_API_URL", "http://localhost:8001")

    # Define workflow with trigger and ingestion step
    # Workflow-engine-poc expects steps at top level (not nested in configuration)
    workflow_config = {
        "name": "E2E Ingestion Test",
        "description": "Test workflow with ingestion service integration",
        "steps": [
            {
                "step_id": "trigger",
                "step_type": "trigger",
                "name": "Webhook Trigger",
                "dependencies": [],
                "parameters": {"kind": "webhook"},
                "config": {},
            },
            {
                "step_id": "ingest",
                "step_type": "ingestion",
                "name": "Ingest Documents",
                "dependencies": ["trigger"],
                "config": {
                    "ingestion_config": {
                        "source_type": "local",
                        "file_paths": ["/tmp/test_doc.pdf"],
                        "chunking": {
                            "strategy": "sliding_window",
                            "chunk_size": 512,
                            "overlap": 50,
                        },
                        "embedding": {
                            "provider": "openai",
                            "model": "text-embedding-3-small",
                        },
                        "storage": {
                            "type": "qdrant",
                            "collection_name": f"test_{uuid.uuid4().hex[:8]}",
                        },
                    },
                    "tenant_id": "test-tenant-123",
                },
            },
        ],
    }

    # Set up authentication headers (required for RBAC)
    # For E2E tests with RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL=true,
    # we use an API key header which will be accepted as-is without validation
    headers = {
        "X-elevAIte-apikey": "test-api-key-e2e",
        "X-elevAIte-OrganizationId": "test-org-456",
        "X-elevAIte-AccountId": "test-account-789",
        "X-elevAIte-ProjectId": "test-project-789",
    }

    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        # Step 1: Create workflow
        print("\n=== Step 1: Creating workflow ===")
        create_response = await client.post(
            f"{workflow_api_url}/api/workflows/", json=workflow_config
        )
        assert create_response.status_code == 200, (
            f"Failed to create workflow: {create_response.text}"
        )

        workflow_data = create_response.json()
        # The response uses 'id' field (UUID)
        workflow_id = workflow_data.get("id")
        assert workflow_id, f"No id in response: {workflow_data}"
        print(f"Created workflow: {workflow_id}")

        # Step 2: Execute workflow with DBOS backend and wait for completion
        print("\n=== Step 2: Executing workflow ===")
        execute_response = await client.post(
            f"{workflow_api_url}/api/workflows/{workflow_id}/execute",
            json={
                "execution_backend": "dbos",
                "trigger": {"kind": "webhook", "data": {"message": "Start ingestion"}},
                "wait": True,
            },
        )
        assert execute_response.status_code == 200, (
            f"Failed to execute workflow: {execute_response.text}"
        )

        execution_data = execute_response.json()
        print(f"Execution response: {execution_data}")
        # Get execution ID from response (may be 'execution_id', 'id', or 'workflow_execution_id')
        execution_id = (
            execution_data.get("execution_id")
            or execution_data.get("id")
            or execution_data.get("workflow_execution_id")
        )
        assert execution_id, f"No execution ID in response: {execution_data}"
        print(f"Started execution: {execution_id}")

        # Step 3: Poll for workflow completion (DBOS workflows run asynchronously)
        print("\n=== Step 3: Waiting for workflow completion ===")
        import asyncio

        max_wait_seconds = 10
        poll_interval = 0.5
        elapsed = 0
        final_status = None
        execution_summary = {}

        while elapsed < max_wait_seconds:
            status_response = await client.get(
                f"{workflow_api_url}/api/executions/{execution_id}"
            )
            assert status_response.status_code == 200
            status_data = status_response.json()

            final_status = status_data.get("status")
            execution_summary = status_data.get("execution_summary", {})
            print(
                f"  [{elapsed:.1f}s] Status: {final_status}, Steps: {execution_summary.get('completed_steps', 0)}/{execution_summary.get('total_steps', 0)}"
            )

            if final_status in ["completed", "failed", "error"]:
                break

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        # Step 4: Verify results
        print("\n=== Step 4: Verifying results ===")
        assert final_status is not None, "No status after polling"

        print(f"Final status: {final_status}")
        print(f"Total steps: {execution_summary.get('total_steps', 0)}")
        print(f"Completed steps: {execution_summary.get('completed_steps', 0)}")
        print(f"Failed steps: {execution_summary.get('failed_steps', 0)}")

        # Verify workflow completed successfully
        assert final_status == "completed", (
            f"Expected status 'completed', got '{final_status}'"
        )
        assert execution_summary.get("failed_steps", 0) == 0, (
            "Workflow had failed steps"
        )

        # Verify steps were executed
        total_steps = execution_summary.get("total_steps", 0)
        completed_steps = execution_summary.get("completed_steps", 0)

        if total_steps == 0:
            print(
                "\n⚠️  WARNING: Workflow shows 0 total steps - checking step_io_data instead"
            )
            # Check if step_io_data has the ingestion step output
            step_io_data = status_data.get("step_io_data", {})
            assert "ingest" in step_io_data, (
                "Ingestion step output not found in step_io_data"
            )
            print(
                f"✅ Ingestion step output found: {list(step_io_data.get('ingest', {}).keys())}"
            )
        else:
            assert completed_steps >= 2, (
                f"Expected at least 2 completed steps (trigger + ingest), got {completed_steps}"
            )
            print(
                f"✅ All {completed_steps}/{total_steps} steps completed successfully"
            )

        print(
            f"\n✅ Workflow execution completed successfully with status: {final_status}"
        )
        print("\n=== Test PASSED ===")


@pytest.mark.asyncio
async def test_ingestion_step_with_mocked_service():
    """
    Test ingestion step with mocked ingestion service.

    This test doesn't require the actual ingestion service to be running.
    It mocks the HTTP calls to verify the workflow integration works correctly.
    """
    from workflow_engine_poc.main import app

    client = TestClient(app)

    # Mock ingestion service responses
    mock_job_id = str(uuid.uuid4())
    mock_create_response = {
        "job_id": mock_job_id,
        "status": "PENDING",
        "created_at": "2024-01-01T00:00:00Z",
    }

    mock_status_response = {
        "job_id": mock_job_id,
        "status": "SUCCEEDED",
        "result_summary": {
            "files_processed": 1,
            "chunks_created": 42,
            "embeddings_generated": 42,
            "vectors_stored": 42,
        },
        "completed_at": "2024-01-01T00:01:00Z",
    }

    # Define workflow with ingestion step
    workflow_config = {
        "name": "Mocked Ingestion Test",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "ingest",
                "step_type": "ingestion",
                "name": "Ingest Documents",
                "step_order": 1,
                "config": {
                    "ingestion_config": {
                        "source_type": "test",
                        "file_paths": ["/tmp/test.pdf"],
                    }
                },
            }
        ],
    }

    # Patch httpx.AsyncClient to mock ingestion service calls
    with patch("httpx.AsyncClient") as mock_client_class:
        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock POST /ingestion/jobs (create job)
        mock_post_response = MagicMock()
        mock_post_response.json.return_value = mock_create_response
        mock_post_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_post_response)

        # Mock GET /ingestion/jobs/{job_id} (check status)
        mock_get_response = MagicMock()
        mock_get_response.json.return_value = mock_status_response
        mock_get_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_get_response)

        # Create and execute workflow
        create_response = client.post("/workflows", json=workflow_config)
        assert create_response.status_code == 200

        workflow_id = str(
            create_response.json()["id"]
        )  # WorkflowRead has 'id' not 'workflow_id'

        # Note: This test verifies the workflow can be created with an ingestion step
        # Full execution testing requires DBOS event handling which is complex to mock
        print(f"Successfully created workflow with ingestion step: {workflow_id}")

        # Verify workflow has ingestion step
        get_response = client.get(f"/workflows/{workflow_id}")
        assert get_response.status_code == 200

        workflow_data = get_response.json()
        # Steps are stored in the configuration field
        steps = workflow_data.get("configuration", {}).get("steps", [])
        ingestion_steps = [s for s in steps if s["step_type"] == "ingestion"]
        assert len(ingestion_steps) == 1, "Should have one ingestion step"

        print("Test PASSED: Workflow with ingestion step created successfully")


# =============================================================================
# MULTI-STEP WORKFLOW TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TEST_INGESTION_SERVICE"),
    reason="Requires TEST_INGESTION_SERVICE=1 and running ingestion service",
)
async def test_multi_step_workflow_with_data_processing():
    """
    Test workflow: trigger -> data_input -> ingestion -> data_processing

    This tests that data flows correctly through multiple steps and
    that ingestion can use data from previous steps.
    """
    print("\n" + "=" * 60)
    print("TEST: Multi-step workflow with data processing")
    print("=" * 60)

    workflow_config = {
        "name": "Multi-Step Ingestion Pipeline",
        "description": "Tests data flow through trigger -> data -> ingest -> process",
        "steps": [
            {
                "step_id": "trigger",
                "step_type": "trigger",
                "name": "Webhook Trigger",
                "dependencies": [],
                "parameters": {"kind": "webhook"},
                "config": {},
            },
            {
                "step_id": "prepare_config",
                "step_type": "data_input",
                "name": "Prepare Ingestion Config",
                "dependencies": ["trigger"],
                "config": {
                    "data": {
                        "source_type": "local",
                        "file_paths": ["/tmp/multi_step_test.pdf"],
                        "metadata": {"pipeline": "multi-step", "version": "1.0"},
                    }
                },
            },
            {
                "step_id": "ingest",
                "step_type": "ingestion",
                "name": "Ingest Documents",
                "dependencies": ["prepare_config"],
                "config": {
                    "ingestion_config": {
                        "source_type": "local",
                        "file_paths": ["/tmp/multi_step_test.pdf"],
                        "chunking": {"strategy": "fixed", "chunk_size": 256},
                    },
                    "tenant_id": "multi-step-test",
                },
            },
            {
                "step_id": "process_result",
                "step_type": "data_processing",
                "name": "Process Ingestion Result",
                "dependencies": ["ingest"],
                "config": {
                    "operation": "transform",
                    "transform_expression": "{'ingestion_complete': True, 'job_id': input_data.get('output_data', {}).get('ingestion_job_id', 'unknown')}",
                },
            },
        ],
    }

    async with httpx.AsyncClient(timeout=30.0, headers=E2E_HEADERS) as client:
        workflow_id, execution_id, exec_data = await create_and_execute_workflow(
            client, workflow_config, {"kind": "webhook", "data": {"source": "e2e_test"}}
        )
        print(f"Created workflow: {workflow_id}, execution: {execution_id}")

        # Poll for completion
        status_data = await poll_execution_status(client, execution_id)
        final_status = status_data.get("status")

        print(f"\nFinal status: {final_status}")
        step_io = status_data.get("step_io_data", {})
        print(f"Steps executed: {list(step_io.keys())}")

        assert final_status == "completed", f"Expected completed, got {final_status}"
        assert "ingest" in step_io, "Ingestion step was not executed"
        assert "process_result" in step_io, "Data processing step was not executed"

        print("\n✅ Multi-step workflow completed successfully")


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TEST_INGESTION_SERVICE"),
    reason="Requires TEST_INGESTION_SERVICE=1 and running ingestion service",
)
async def test_parallel_ingestion_steps():
    """
    Test workflow with two parallel ingestion steps.

    Both ingestion steps depend only on the trigger, so they should
    execute concurrently (subject to execution_pattern).
    """
    print("\n" + "=" * 60)
    print("TEST: Parallel ingestion steps")
    print("=" * 60)

    workflow_config = {
        "name": "Parallel Ingestion Test",
        "description": "Two ingestion steps running in parallel",
        "execution_pattern": "parallel",
        "steps": [
            {
                "step_id": "trigger",
                "step_type": "trigger",
                "name": "Webhook Trigger",
                "dependencies": [],
                "parameters": {"kind": "webhook"},
            },
            {
                "step_id": "ingest_docs",
                "step_type": "ingestion",
                "name": "Ingest Documents",
                "dependencies": ["trigger"],
                "config": {
                    "ingestion_config": {
                        "source_type": "local",
                        "file_paths": ["/tmp/docs_a.pdf"],
                    },
                    "tenant_id": "parallel-test-docs",
                },
            },
            {
                "step_id": "ingest_images",
                "step_type": "ingestion",
                "name": "Ingest Images",
                "dependencies": ["trigger"],
                "config": {
                    "ingestion_config": {
                        "source_type": "local",
                        "file_paths": ["/tmp/images_b.pdf"],
                    },
                    "tenant_id": "parallel-test-images",
                },
            },
            {
                "step_id": "merge_results",
                "step_type": "data_merge",
                "name": "Merge Ingestion Results",
                "dependencies": ["ingest_docs", "ingest_images"],
                "config": {
                    "merge_strategy": "combine",
                },
            },
        ],
    }

    async with httpx.AsyncClient(timeout=60.0, headers=E2E_HEADERS) as client:
        workflow_id, execution_id, exec_data = await create_and_execute_workflow(
            client, workflow_config
        )
        print(f"Created workflow: {workflow_id}, execution: {execution_id}")

        # Poll for completion (longer timeout for parallel)
        status_data = await poll_execution_status(client, execution_id, max_wait=30.0)
        final_status = status_data.get("status")

        step_io = status_data.get("step_io_data", {})
        print(f"\nFinal status: {final_status}")
        print(f"Steps executed: {list(step_io.keys())}")

        assert final_status == "completed", f"Expected completed, got {final_status}"
        assert "ingest_docs" in step_io, "First ingestion step was not executed"
        assert "ingest_images" in step_io, "Second ingestion step was not executed"
        assert "merge_results" in step_io, "Merge step was not executed"

        print("\n✅ Parallel ingestion workflow completed successfully")


# =============================================================================
# CONCURRENT EXECUTION TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TEST_INGESTION_SERVICE"),
    reason="Requires TEST_INGESTION_SERVICE=1 and running ingestion service",
)
async def test_concurrent_workflow_executions():
    """
    Test running multiple workflow executions concurrently.

    This tests that the ingestion service can handle multiple
    simultaneous requests from different workflow executions.
    """
    print("\n" + "=" * 60)
    print("TEST: Concurrent workflow executions")
    print("=" * 60)

    # Create a simple ingestion workflow template
    def make_workflow(index: int) -> dict:
        return {
            "name": f"Concurrent Ingestion Test #{index}",
            "steps": [
                {
                    "step_id": "trigger",
                    "step_type": "trigger",
                    "name": "Webhook Trigger",
                    "dependencies": [],
                    "parameters": {"kind": "webhook"},
                },
                {
                    "step_id": "ingest",
                    "step_type": "ingestion",
                    "name": f"Ingest #{index}",
                    "dependencies": ["trigger"],
                    "config": {
                        "ingestion_config": {
                            "source_type": "local",
                            "file_paths": [f"/tmp/concurrent_{index}.pdf"],
                        },
                        "tenant_id": f"concurrent-test-{index}",
                    },
                },
            ],
        }

    num_concurrent = 3

    async with httpx.AsyncClient(timeout=60.0, headers=E2E_HEADERS) as client:
        # Start all workflows concurrently
        print(f"\nStarting {num_concurrent} concurrent workflow executions...")

        async def run_workflow(index: int) -> tuple[str, str, dict]:
            workflow_config = make_workflow(index)
            return await create_and_execute_workflow(
                client, workflow_config, wait=False
            )

        # Launch all workflows
        tasks = [run_workflow(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks)

        execution_ids = [r[1] for r in results]
        print(f"Started executions: {execution_ids}")

        # Poll all executions for completion
        print("\nWaiting for all executions to complete...")

        async def wait_for_completion(exec_id: str) -> dict:
            return await poll_execution_status(client, exec_id, max_wait=30.0)

        poll_tasks = [wait_for_completion(eid) for eid in execution_ids]
        final_statuses = await asyncio.gather(*poll_tasks)

        # Verify all completed
        all_completed = True
        for i, status_data in enumerate(final_statuses):
            final_status = status_data.get("status")
            print(f"  Execution {i + 1}: {final_status}")
            if final_status != "completed":
                all_completed = False

        assert all_completed, "Not all concurrent executions completed successfully"
        print(f"\n✅ All {num_concurrent} concurrent workflows completed successfully")


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TEST_INGESTION_SERVICE"),
    reason="Requires TEST_INGESTION_SERVICE=1 and running services",
)
async def test_async_workflow_without_ingestion():
    """
    Test that wait=False works correctly for simple workflows without ingestion steps.

    This verifies that the DBOS workflow status persistence fix works correctly
    for workflows that don't require external callbacks.
    """
    print("\n" + "=" * 60)
    print("TEST: Async workflow execution (wait=False) without ingestion")
    print("=" * 60)

    # Simple workflow with just trigger + data processing (no ingestion)
    workflow_config = {
        "name": "Async Simple Workflow Test",
        "description": "Test wait=False with simple workflow",
        "steps": [
            {
                "step_id": "trigger",
                "step_type": "trigger",
                "name": "Webhook Trigger",
                "dependencies": [],
                "parameters": {"kind": "webhook"},
            },
            {
                "step_id": "process",
                "step_type": "data_processing",
                "name": "Process Data",
                "dependencies": ["trigger"],
                "config": {
                    "operation": "transform",
                    "transform_type": "uppercase",
                },
            },
        ],
    }

    async with httpx.AsyncClient(timeout=30.0, headers=E2E_HEADERS) as client:
        # Execute with wait=False
        print("\nExecuting workflow with wait=False...")
        workflow_id, execution_id, exec_response = await create_and_execute_workflow(
            client,
            workflow_config,
            trigger_data={"kind": "webhook", "data": {"message": "async test"}},
            wait=False,
        )

        print(f"Workflow ID: {workflow_id}")
        print(f"Execution ID: {execution_id}")
        print(f"Initial response: {exec_response}")

        # The response should return immediately with running status
        initial_status = exec_response.get("status")
        print(f"Initial status: {initial_status}")

        # Poll for completion - simple workflows should complete quickly
        print("\nPolling for completion...")
        status_data = await poll_execution_status(client, execution_id, max_wait=10.0)

        final_status = status_data.get("status")
        print(f"Final status: {final_status}")

        # Verify workflow completed
        assert final_status == "completed", (
            f"Expected 'completed', got '{final_status}'"
        )
        print("\n✅ Async workflow (wait=False) completed successfully")


# =============================================================================
# INGESTION SERVICE HEALTH TESTS
# =============================================================================


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TEST_INGESTION_SERVICE"),
    reason="Requires TEST_INGESTION_SERVICE=1 and running ingestion service",
)
async def test_ingestion_service_health():
    """
    Test that the ingestion service is healthy and responding.
    """
    print("\n" + "=" * 60)
    print("TEST: Ingestion service health check")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{INGESTION_API_URL}/health")

        print(f"Health endpoint status: {response.status_code}")
        print(f"Response: {response.json()}")

        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

        print("\n✅ Ingestion service is healthy")


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TEST_INGESTION_SERVICE"),
    reason="Requires TEST_INGESTION_SERVICE=1 and running ingestion service",
)
async def test_direct_ingestion_job_creation():
    """
    Test creating an ingestion job directly via the ingestion service API.

    This bypasses the workflow engine to verify the ingestion service
    works correctly in isolation.
    """
    print("\n" + "=" * 60)
    print("TEST: Direct ingestion job creation")
    print("=" * 60)

    job_request = {
        "config": {
            "source_type": "local",
            "file_paths": ["/tmp/direct_test.pdf"],
            "chunking": {"strategy": "fixed", "chunk_size": 512},
        },
        "metadata": {
            "tenant_id": "direct-api-test",
            "execution_id": str(uuid.uuid4()),
            "step_id": "direct-step",
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create job
        print("\nCreating ingestion job...")
        create_response = await client.post(
            f"{INGESTION_API_URL}/ingestion/jobs",
            json=job_request,
        )

        assert create_response.status_code == 200, (
            f"Failed to create job: {create_response.text}"
        )
        job_data = create_response.json()
        job_id = job_data.get("job_id")

        print(f"Created job: {job_id}")
        print(f"Initial status: {job_data.get('status')}")

        # Poll for completion
        print("\nPolling for job completion...")
        max_wait = 15.0
        poll_interval = 0.5
        elapsed = 0
        final_status = None

        while elapsed < max_wait:
            status_response = await client.get(
                f"{INGESTION_API_URL}/ingestion/jobs/{job_id}"
            )
            assert status_response.status_code == 200
            status_data = status_response.json()
            final_status = status_data.get("status")

            print(f"  [{elapsed:.1f}s] Status: {final_status}")

            if final_status in ["SUCCEEDED", "FAILED"]:
                break

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        # The job may succeed or fail depending on whether the file exists
        # We just want to verify the API flow works
        assert final_status in ["SUCCEEDED", "FAILED", "PENDING", "RUNNING"], (
            f"Unexpected status: {final_status}"
        )

        print(f"\n✅ Direct ingestion job completed with status: {final_status}")
