#!/usr/bin/env python3
"""
Test script for async workflow execution with streaming responses
"""

import asyncio
import json
import requests
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
WORKFLOW_API_URL = f"{BASE_URL}/api/workflows"


def get_existing_workflow():
    """Get an existing workflow for testing"""
    response = requests.get(f"{WORKFLOW_API_URL}/")
    print(f"Workflow list status: {response.status_code}")
    if response.status_code == 200:
        workflows = response.json()
        if workflows:
            # Use the first available workflow
            workflow = workflows[0]
            print(f"Using existing workflow: {workflow['workflow_id']} - {workflow['name']}")
            return workflow
        else:
            print("No workflows found")
            return None
    else:
        print(f"Error getting workflows: {response.text}")
        return None


def test_workflow_deployment(workflow_id: str):
    """Test deploying a workflow"""
    import time

    timestamp = int(time.time())
    deployment_data = {
        "deployment_name": f"test_async_deployment_{timestamp}",
        "environment": "development",
        "deployed_by": "test_user",
    }

    response = requests.post(f"{WORKFLOW_API_URL}/{workflow_id}/deploy", json=deployment_data)
    print(f"Deployment status: {response.status_code}")
    if response.status_code == 200:
        deployment = response.json()
        print(f"Created deployment: {deployment['deployment_name']}")
        return deployment
    else:
        print(f"Error deploying workflow: {response.text}")
        return None


async def test_streaming_execution(deployment_name: str):
    """Test streaming execution of a workflow"""
    execution_data = {
        "deployment_name": deployment_name,
        "query": "Hello, this is a test query for async streaming execution",
        "chat_history": [
            {"actor": "user", "content": "Previous message"},
            {"actor": "assistant", "content": "Previous response"},
        ],
    }

    print(f"Testing streaming execution for deployment: {deployment_name}")

    # Use requests for streaming
    response = requests.post(
        f"{WORKFLOW_API_URL}/execute/stream", json=execution_data, stream=True, headers={"Accept": "text/event-stream"}
    )

    print(f"Streaming response status: {response.status_code}")

    if response.status_code == 200:
        print("Streaming response chunks:")
        for line in response.iter_lines(decode_unicode=True):
            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix
                try:
                    chunk = json.loads(data)
                    print(f"  Chunk: {chunk}")
                except json.JSONDecodeError:
                    print(f"  Raw chunk: {data}")
    else:
        print(f"Error in streaming execution: {response.text}")


def test_regular_execution(deployment_name: str):
    """Test regular (non-streaming) execution of a workflow"""
    execution_data = {"deployment_name": deployment_name, "query": "Hello, this is a test query for regular execution"}

    response = requests.post(f"{WORKFLOW_API_URL}/execute", json=execution_data)
    print(f"Regular execution status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Execution result: {result}")
        return result
    else:
        print(f"Error in regular execution: {response.text}")
        return None


async def main():
    """Main test function"""
    print("=== Testing Async Workflow Execution with Streaming ===\n")

    # Test 1: Get existing workflow
    print("1. Getting existing workflow...")
    workflow = get_existing_workflow()
    if not workflow:
        print("Failed to get workflow. Exiting.")
        return

    workflow_id = workflow["workflow_id"]
    print(f"✓ Using workflow with ID: {workflow_id}\n")

    # Test 2: Deploy workflow
    print("2. Deploying workflow...")
    deployment = test_workflow_deployment(workflow_id)
    if not deployment:
        print("Failed to deploy workflow. Exiting.")
        return

    deployment_name = deployment["deployment_name"]
    print(f"✓ Workflow deployed with name: {deployment_name}\n")

    # Test 3: Regular execution
    print("3. Testing regular execution...")
    regular_result = test_regular_execution(deployment_name)
    if regular_result:
        print("✓ Regular execution completed\n")
    else:
        print("✗ Regular execution failed\n")

    # Test 4: Streaming execution
    print("4. Testing streaming execution...")
    await test_streaming_execution(deployment_name)
    print("✓ Streaming execution test completed\n")

    print("=== All tests completed ===")


if __name__ == "__main__":
    asyncio.run(main())
