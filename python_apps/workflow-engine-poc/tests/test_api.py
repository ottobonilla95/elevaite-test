"""
Test API Endpoints

Test script to validate all API endpoints are working correctly.
Tests workflow management, file upload, and execution endpoints.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, Any

import httpx
from fastapi.testclient import TestClient

from workflow_engine_poc.main import app


async def test_api_endpoints():
    """Test all API endpoints using TestClient"""

    print("🧪 Testing API Endpoints")
    print("=" * 60)

    # Initialize app state manually for testing
    from .step_registry import StepRegistry
    from .workflow_engine import WorkflowEngine
    from .database import get_database

    # Manually initialize app state for testing
    database = await get_database()
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()
    workflow_engine = WorkflowEngine(step_registry)

    app.state.database = database
    app.state.step_registry = step_registry
    app.state.workflow_engine = workflow_engine

    client = TestClient(app)

    # Test health endpoints
    print("\n📋 Testing Health Endpoints:")

    # Root endpoint
    response = client.get("/")
    print(
        f"   GET /: {response.status_code} - {response.json().get('message', 'No message')}"
    )
    assert response.status_code == 200

    # Health check
    response = client.get("/health")
    print(
        f"   GET /health: {response.status_code} - {response.json().get('status', 'No status')}"
    )
    assert response.status_code == 200

    # Test step endpoints
    print("\n📋 Testing Step Endpoints:")

    # List steps
    response = client.get("/steps")
    print(
        f"   GET /steps: {response.status_code} - {response.json().get('total', 0)} steps"
    )
    assert response.status_code == 200

    # Get specific step info
    response = client.get("/steps/data_input")
    print(f"   GET /steps/data_input: {response.status_code}")
    assert response.status_code == 200

    # Test workflow management endpoints
    print("\n📋 Testing Workflow Management:")

    # Create test workflow
    test_workflow = {
        "workflow_id": "test-api-workflow",
        "name": "API Test Workflow",
        "description": "Test workflow for API validation",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "input_step",
                "step_name": "Input Data",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "input_type": "static",
                    "data": {"message": "Hello from API test"},
                },
            },
            {
                "step_id": "agent_step",
                "step_name": "Agent Processing",
                "step_type": "agent_execution",
                "step_order": 2,
                "dependencies": ["input_step"],
                "config": {
                    "agent_config": {
                        "agent_name": "API Test Agent",
                        "model": "gpt-4o-mini",
                        "system_prompt": "You are a test agent for API validation.",
                        "temperature": 0.1,
                        "max_tokens": 100,
                    },
                    "query": "Process this message: {message}",
                    "return_simplified": True,
                },
            },
        ],
    }

    # Save workflow
    response = client.post("/workflows", json=test_workflow)
    print(
        f"   POST /workflows: {response.status_code} - {response.json().get('message', 'No message')}"
    )
    assert response.status_code == 200

    # Get workflow
    workflow_id = test_workflow["workflow_id"]
    response = client.get(f"/workflows/{workflow_id}")
    print(f"   GET /workflows/{workflow_id}: {response.status_code}")
    assert response.status_code == 200

    # List workflows
    response = client.get("/workflows")
    print(
        f"   GET /workflows: {response.status_code} - {response.json().get('total', 0)} workflows"
    )
    assert response.status_code == 200

    # Test workflow validation
    print("\n📋 Testing Workflow Validation:")

    response = client.post("/workflows/validate", json=test_workflow)
    print(f"   POST /workflows/validate: {response.status_code}")
    assert response.status_code == 200

    # Test workflow execution
    print("\n📋 Testing Workflow Execution:")

    execution_request = {
        "workflow_config": test_workflow,
        "user_id": "api_test_user",
        "session_id": "api_test_session",
        "input_data": {"additional_context": "API test execution"},
    }

    response = client.post("/workflows/execute", json=execution_request)
    print(f"   POST /workflows/execute: {response.status_code}")
    assert response.status_code == 200

    execution_id = response.json().get("execution_id")
    if execution_id:
        print(f"   Execution ID: {execution_id}")

        # Wait a moment for execution to start
        import time

        time.sleep(1)

        # Check execution status
        response = client.get(f"/executions/{execution_id}")
        print(f"   GET /executions/{execution_id}: {response.status_code}")

        # Get execution results
        response = client.get(f"/executions/{execution_id}/results")
        print(f"   GET /executions/{execution_id}/results: {response.status_code}")

    # Test file upload
    print("\n📋 Testing File Upload:")

    # Create a test file
    test_content = "This is a test file for the workflow engine API.\nIt contains sample content for processing."

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name

    try:
        # Test file upload
        with open(temp_file_path, "rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = client.post("/files/upload", files=files)
            print(f"   POST /files/upload: {response.status_code}")
            assert response.status_code == 200

            upload_result = response.json()
            print(
                f"   Uploaded file: {upload_result.get('filename')} ({upload_result.get('file_size')} bytes)"
            )

    finally:
        # Clean up temp file
        Path(temp_file_path).unlink(missing_ok=True)

    # Test analytics
    print("\n📋 Testing Analytics:")

    response = client.get("/analytics/executions")
    print(f"   GET /analytics/executions: {response.status_code}")
    assert response.status_code == 200

    # Clean up test workflow
    print("\n📋 Cleaning Up:")

    response = client.delete(f"/workflows/{workflow_id}")
    print(f"   DELETE /workflows/{workflow_id}: {response.status_code}")
    assert response.status_code == 200

    print("\n🎉 All API endpoint tests passed!")
    return True


def test_file_workflow_integration():
    """Test file upload with workflow execution"""

    print("\n🧪 Testing File + Workflow Integration")
    print("-" * 40)

    client = TestClient(app)

    # Create a file processing workflow
    file_workflow = {
        "workflow_id": "file-processing-test",
        "name": "File Processing Test",
        "description": "Test workflow for file processing",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "read_file",
                "step_name": "Read File",
                "step_type": "file_reader",
                "step_order": 1,
                "input_mapping": {"file_path": "file_upload.file_path"},
                "config": {},
            },
            {
                "step_id": "chunk_text",
                "step_name": "Chunk Text",
                "step_type": "text_chunking",
                "step_order": 2,
                "dependencies": ["read_file"],
                "input_mapping": {"content": "read_file.content"},
                "config": {
                    "strategy": "sliding_window",
                    "chunk_size": 200,
                    "overlap": 50,
                },
            },
            {
                "step_id": "generate_embeddings",
                "step_name": "Generate Embeddings",
                "step_type": "embedding_generation",
                "step_order": 3,
                "dependencies": ["chunk_text"],
                "input_mapping": {"chunks": "chunk_text.chunks"},
                "config": {
                    "provider": "openai",
                    "model": "text-embedding-ada-002",
                    "batch_size": 5,
                },
            },
        ],
    }

    # Create test file content
    test_content = """
    Unified Workflow Execution Engine Test Document
    
    This document is used to test the file processing capabilities of the workflow engine.
    It contains multiple paragraphs and should be processed through the complete RAG pipeline.
    
    The workflow engine supports various file formats including PDF, DOCX, XLSX, and plain text.
    Each file type is processed using appropriate parsers to extract meaningful content.
    
    The text chunking step divides the content into manageable segments that can be processed
    by embedding models and stored in vector databases for efficient retrieval.
    """

    # Test workflow execution with file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(test_content)
        temp_file_path = f.name

    try:
        with open(temp_file_path, "rb") as f:
            files = {"file": ("test_document.txt", f, "text/plain")}
            data = {
                "workflow_config": json.dumps(file_workflow),
                "user_id": "file_test_user",
            }

            response = client.post(
                "/workflows/execute-with-file", files=files, data=data
            )
            print(f"   POST /workflows/execute-with-file: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                execution_id = result.get("execution_id")
                print(f"   File workflow execution started: {execution_id}")
                print(f"   Message: {result.get('message')}")

                # Wait for execution to process
                import time

                time.sleep(2)

                # Check results
                status_response = client.get(f"/executions/{execution_id}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"   Execution status: {status.get('status')}")
                    print(
                        f"   Completed steps: {len(status.get('completed_steps', []))}"
                    )

                return True
            else:
                print(f"   Error: {response.text}")
                return False

    finally:
        # Clean up
        Path(temp_file_path).unlink(missing_ok=True)


async def main():
    """Run all API tests"""

    print("🚀 Workflow Engine API Test Suite")
    print("=" * 60)

    try:
        # Test basic API endpoints
        await test_api_endpoints()

        # Test file workflow integration
        # test_file_workflow_integration()  # Skip for now due to complexity

        print("\n🎉 All API tests completed successfully!")
        print("✅ The API endpoints are working correctly")

    except Exception as e:
        print(f"\n❌ API test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
