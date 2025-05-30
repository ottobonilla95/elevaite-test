#!/usr/bin/env python3
"""
Test script for workflow deployment and undeployment functionality
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
WORKFLOW_API_URL = f"{BASE_URL}/api/workflows"

def create_test_workflow():
    """Create a test workflow for deployment testing"""
    timestamp = int(time.time())
    workflow_data = {
        "name": f"test_undeploy_workflow_{timestamp}",
        "description": "Test workflow for undeploy functionality",
        "version": "1.0.0",
        "configuration": {
            "agents": [
                {
                    "agent_id": "toshiba-test-001",
                    "agent_type": "ToshibaAgent",
                    "position": {"x": 100, "y": 100},
                    "config": {
                        "model": "gpt-4o",
                        "temperature": 0.6,
                        "max_retries": 3
                    }
                }
            ],
            "connections": [],
            "metadata": {
                "workflow_type": "single_agent",
                "test_purpose": "undeploy_testing"
            }
        },
        "created_by": "test_user"
    }
    
    response = requests.post(WORKFLOW_API_URL, json=workflow_data)
    print(f"Workflow creation status: {response.status_code}")
    if response.status_code == 200:
        workflow = response.json()
        print(f"✓ Created test workflow: {workflow['workflow_id']} - {workflow['name']}")
        return workflow
    else:
        print(f"✗ Error creating workflow: {response.text}")
        return None

def deploy_workflow(workflow_id: str):
    """Deploy the test workflow"""
    timestamp = int(time.time())
    deployment_data = {
        "deployment_name": f"test_deployment_{timestamp}",
        "environment": "development",
        "deployed_by": "test_user"
    }
    
    response = requests.post(f"{WORKFLOW_API_URL}/{workflow_id}/deploy", json=deployment_data)
    print(f"Deployment status: {response.status_code}")
    if response.status_code == 200:
        deployment = response.json()
        print(f"✓ Deployed workflow: {deployment['deployment_name']}")
        return deployment
    else:
        print(f"✗ Error deploying workflow: {response.text}")
        return None

def list_active_deployments():
    """List all active deployments"""
    response = requests.get(f"{WORKFLOW_API_URL}/deployments/active")
    print(f"List active deployments status: {response.status_code}")
    if response.status_code == 200:
        deployments = response.json()
        print(f"Active deployments: {len(deployments)}")
        for i, deployment in enumerate(deployments):
            print(f"  {i+1}. {deployment['deployment_name']} (Status: {deployment['status']})")
        return deployments
    else:
        print(f"✗ Error listing deployments: {response.text}")
        return []

def test_workflow_execution(deployment_name: str):
    """Test that the deployed workflow can execute"""
    execution_data = {
        "deployment_name": deployment_name,
        "query": "Test query for deployment verification",
        "chat_history": []
    }
    
    response = requests.post(f"{WORKFLOW_API_URL}/execute", json=execution_data)
    print(f"Execution test status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Workflow execution successful")
        return True
    else:
        print(f"✗ Workflow execution failed: {response.text}")
        return False

def stop_deployment(deployment_name: str):
    """Stop/undeploy a workflow deployment"""
    response = requests.post(f"{WORKFLOW_API_URL}/deployments/{deployment_name}/stop")
    print(f"Stop deployment status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Deployment stopped: {result['message']}")
        print(f"  - Deployment ID: {result['deployment_id']}")
        print(f"  - Status: {result['status']}")
        print(f"  - Stopped at: {result.get('stopped_at', 'N/A')}")
        return True
    else:
        print(f"✗ Error stopping deployment: {response.text}")
        return False

def delete_deployment(deployment_name: str):
    """Completely delete a workflow deployment"""
    response = requests.delete(f"{WORKFLOW_API_URL}/deployments/{deployment_name}")
    print(f"Delete deployment status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Deployment deleted: {result['message']}")
        print(f"  - Deployment ID: {result['deployment_id']}")
        return True
    else:
        print(f"✗ Error deleting deployment: {response.text}")
        return False

def verify_deployment_stopped(deployment_name: str):
    """Verify that a stopped deployment cannot execute"""
    execution_data = {
        "deployment_name": deployment_name,
        "query": "This should fail",
        "chat_history": []
    }
    
    response = requests.post(f"{WORKFLOW_API_URL}/execute", json=execution_data)
    print(f"Verification execution status: {response.status_code}")
    if response.status_code == 404:
        print(f"✓ Deployment correctly unavailable for execution")
        return True
    else:
        print(f"✗ Deployment still available (unexpected): {response.text}")
        return False

def main():
    """Main test function for workflow undeploy functionality"""
    print("=== Testing Workflow Undeploy Functionality ===\n")
    
    # Test 1: Create a test workflow
    print("1. Creating test workflow...")
    workflow = create_test_workflow()
    if not workflow:
        print("Failed to create workflow. Exiting.")
        return
    
    workflow_id = workflow["workflow_id"]
    print(f"✓ Test workflow created: {workflow_id}\n")
    
    # Test 2: Deploy the workflow
    print("2. Deploying workflow...")
    deployment = deploy_workflow(workflow_id)
    if not deployment:
        print("Failed to deploy workflow. Exiting.")
        return
    
    deployment_name = deployment["deployment_name"]
    print(f"✓ Workflow deployed: {deployment_name}\n")
    
    # Test 3: List active deployments
    print("3. Listing active deployments...")
    active_deployments = list_active_deployments()
    print(f"✓ Found {len(active_deployments)} active deployments\n")
    
    # Test 4: Test workflow execution
    print("4. Testing workflow execution...")
    execution_success = test_workflow_execution(deployment_name)
    if execution_success:
        print("✓ Workflow execution test passed\n")
    else:
        print("⚠️  Workflow execution test failed, but continuing...\n")
    
    # Test 5: Stop the deployment
    print("5. Stopping deployment...")
    stop_success = stop_deployment(deployment_name)
    if not stop_success:
        print("Failed to stop deployment. Exiting.")
        return
    print("✓ Deployment stopped successfully\n")
    
    # Test 6: Verify deployment is stopped
    print("6. Verifying deployment is stopped...")
    verify_success = verify_deployment_stopped(deployment_name)
    if verify_success:
        print("✓ Deployment correctly stopped\n")
    else:
        print("⚠️  Deployment stop verification failed\n")
    
    # Test 7: List active deployments again
    print("7. Listing active deployments after stop...")
    active_deployments_after = list_active_deployments()
    print(f"✓ Found {len(active_deployments_after)} active deployments\n")
    
    # Test 8: Delete the deployment completely
    print("8. Deleting deployment completely...")
    delete_success = delete_deployment(deployment_name)
    if delete_success:
        print("✓ Deployment deleted successfully\n")
    else:
        print("⚠️  Deployment deletion failed\n")
    
    # Test 9: Final verification
    print("9. Final verification...")
    final_deployments = list_active_deployments()
    print(f"✓ Final active deployments: {len(final_deployments)}\n")
    
    print("=== Workflow Undeploy Tests Completed ===")
    print("\nSummary:")
    print(f"  ✓ Workflow created: {workflow['name']}")
    print(f"  ✓ Deployment created: {deployment_name}")
    print(f"  ✓ Stop deployment: {'Success' if stop_success else 'Failed'}")
    print(f"  ✓ Delete deployment: {'Success' if delete_success else 'Failed'}")
    print(f"  ✓ Verification: {'Success' if verify_success else 'Failed'}")
    
    print("\nAvailable Undeploy Methods:")
    print("  1. Stop deployment (keeps record, sets status to 'inactive'):")
    print(f"     POST {WORKFLOW_API_URL}/deployments/{{deployment_name}}/stop")
    print("  2. Delete deployment (completely removes from database):")
    print(f"     DELETE {WORKFLOW_API_URL}/deployments/{{deployment_name}}")

if __name__ == "__main__":
    main()
