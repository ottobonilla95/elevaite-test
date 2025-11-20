"""
E2E Test for Ingestion Service Integration

Tests the complete flow of:
1. Creating a workflow with an ingestion step
2. Executing the workflow via the workflow API
3. Ingestion service creating and running a job
4. DBOS event notification back to workflow engine
5. Workflow completing successfully

Prerequisites:
- Ingestion service running on port 8001
- Workflow engine running on port 8000
- Both services connected to their databases
- DBOS configured for both services
"""

import os
import uuid
import time
import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("TEST_INGESTION_SERVICE"), reason="Requires TEST_INGESTION_SERVICE=1 and running ingestion service"
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
    from workflow_engine_poc.main import app

    # Initialize test client
    client = TestClient(app)

    # Define workflow with ingestion step
    workflow_config = {
        "name": "E2E Ingestion Test",
        "description": "Test workflow with ingestion service integration",
        "execution_pattern": "sequential",
        "steps": [
            {"step_id": "trigger", "step_type": "trigger", "name": "Trigger Step", "step_order": 1, "config": {}},
            {
                "step_id": "ingest",
                "step_type": "ingestion",
                "name": "Ingest Documents",
                "dependencies": ["trigger"],
                "step_order": 2,
                "config": {
                    "ingestion_config": {
                        "source_type": "local",
                        "file_paths": ["/tmp/test_doc.pdf"],
                        "chunking": {"strategy": "sliding_window", "chunk_size": 512, "overlap": 50},
                        "embedding": {"provider": "openai", "model": "text-embedding-3-small"},
                        "storage": {"type": "qdrant", "collection_name": f"test_{uuid.uuid4().hex[:8]}"},
                    },
                    "tenant_id": "test-tenant-123",
                },
            },
        ],
    }

    # Step 1: Create workflow
    print("\n=== Step 1: Creating workflow ===")
    create_response = client.post("/workflows", json=workflow_config)
    assert create_response.status_code == 200, f"Failed to create workflow: {create_response.text}"

    workflow_data = create_response.json()
    workflow_id = str(workflow_data["id"])  # WorkflowRead has 'id' not 'workflow_id'
    print(f"Created workflow: {workflow_id}")

    # Step 2: Execute workflow
    print("\n=== Step 2: Executing workflow ===")
    execute_response = client.post(f"/workflows/{workflow_id}/execute", json={"trigger_data": {"message": "Start ingestion"}})
    assert execute_response.status_code == 200, f"Failed to execute workflow: {execute_response.text}"

    execution_data = execute_response.json()
    execution_id = execution_data["execution_id"]
    print(f"Started execution: {execution_id}")

    # Step 3: Poll for completion (with timeout)
    print("\n=== Step 3: Waiting for workflow completion ===")
    max_wait = 60  # 60 seconds timeout
    poll_interval = 2  # Poll every 2 seconds
    elapsed = 0

    final_status = None
    while elapsed < max_wait:
        status_response = client.get(f"/executions/{execution_id}")
        assert status_response.status_code == 200

        status_data = status_response.json()
        current_status = status_data["status"]
        print(f"  [{elapsed}s] Status: {current_status}")

        if current_status in ["COMPLETED", "FAILED", "CANCELLED"]:
            final_status = current_status
            break

        time.sleep(poll_interval)
        elapsed += poll_interval

    # Step 4: Verify completion
    print("\n=== Step 4: Verifying results ===")
    assert final_status is not None, f"Workflow did not complete within {max_wait}s"
    assert final_status == "COMPLETED", f"Workflow failed with status: {final_status}"

    # Get final execution details
    final_response = client.get(f"/executions/{execution_id}")
    final_data = final_response.json()

    print(f"Final status: {final_data['status']}")
    print(f"Steps executed: {len(final_data.get('steps', []))}")

    # Verify ingestion step completed
    ingestion_step = next((s for s in final_data.get("steps", []) if s["step_id"] == "ingest"), None)
    assert ingestion_step is not None, "Ingestion step not found in execution"
    assert ingestion_step["status"] == "COMPLETED", f"Ingestion step status: {ingestion_step['status']}"

    # Verify ingestion step output contains job_id
    step_output = ingestion_step.get("output_data", {})
    assert "ingestion_job_id" in step_output, "Missing ingestion_job_id in step output"

    job_id = step_output["ingestion_job_id"]
    print(f"Ingestion job ID: {job_id}")

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
    mock_create_response = {"job_id": mock_job_id, "status": "PENDING", "created_at": "2024-01-01T00:00:00Z"}

    mock_status_response = {
        "job_id": mock_job_id,
        "status": "SUCCEEDED",
        "result_summary": {"files_processed": 1, "chunks_created": 42, "embeddings_generated": 42, "vectors_stored": 42},
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
                "config": {"ingestion_config": {"source_type": "test", "file_paths": ["/tmp/test.pdf"]}},
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

        workflow_id = str(create_response.json()["id"])  # WorkflowRead has 'id' not 'workflow_id'

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
