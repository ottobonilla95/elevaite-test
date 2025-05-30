#!/usr/bin/env python3
"""
Script to create demo workflows via the API endpoints.
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"


def create_demo_workflow_via_api():
    """Create a demo workflow using the API endpoints."""

    print("Creating demo workflow via API...")

    try:
        # First, get available agents
        print("Fetching available agents...")
        agents_response = requests.get(f"{API_BASE_URL}/api/agents/deployment/available")

        if agents_response.status_code != 200:
            print(f"Failed to fetch agents: {agents_response.status_code}")
            print(agents_response.text)
            return

        agents = agents_response.json()
        print(f"Found {len(agents)} available agents")

        if len(agents) < 2:
            print("Not enough agents available. Need at least 2 agents.")
            return

        # Create workflow using the proper workflow API
        import time

        timestamp = str(int(time.time()))

        workflow_data = {
            "name": f"Customer Support Demo Workflow {timestamp}",
            "description": "A demo workflow that handles customer inquiries using web search and data analysis",
            "version": f"1.0.{timestamp}",
            "created_by": "demo_script",
            "is_active": True,
            "tags": ["demo", "customer_support"],
            "configuration": {"demo": True, "created_by_script": True, "purpose": "testing_frontend", "timestamp": timestamp},
        }

        print("Creating workflow...")
        print(f"Workflow data: {json.dumps(workflow_data, indent=2)}")

        # Create the workflow first
        workflow_response = requests.post(
            f"{API_BASE_URL}/api/workflows/", json=workflow_data, headers={"Content-Type": "application/json"}
        )

        if workflow_response.status_code == 200:
            workflow_result = workflow_response.json()
            print("✅ Workflow created successfully!")
            print(f"Response: {json.dumps(workflow_result, indent=2)}")

            workflow_id = workflow_result["workflow_id"]

            # Now add agents to the workflow
            print("\nAdding agents to workflow...")
            agent_positions = [
                {"agent_id": agents[0]["agent_id"], "position": {"x": 100, "y": 100}},
                {"agent_id": agents[1]["agent_id"], "position": {"x": 400, "y": 100}},
            ]

            for i, agent_data in enumerate(agent_positions):
                agent_payload = {
                    "workflow_id": workflow_id,
                    "agent_id": agent_data["agent_id"],
                    "position_x": agent_data["position"]["x"],
                    "position_y": agent_data["position"]["y"],
                    "node_id": f"node-{agent_data['agent_id']}",
                    "agent_config": {"demo": True},
                }

                agent_response = requests.post(
                    f"{API_BASE_URL}/api/workflows/{workflow_id}/agents",
                    json=agent_payload,
                    headers={"Content-Type": "application/json"},
                )

                if agent_response.status_code == 200:
                    print(f"  ✅ Added agent {i + 1} to workflow")
                else:
                    print(f"  ❌ Failed to add agent {i + 1}: {agent_response.status_code}")
                    print(f"     {agent_response.text}")

            # Add connection between agents
            print("\nAdding connection...")
            connection_payload = {
                "workflow_id": workflow_id,
                "source_agent_id": agents[0]["agent_id"],
                "target_agent_id": agents[1]["agent_id"],
                "connection_type": "default",
                "priority": 1,
            }

            connection_response = requests.post(
                f"{API_BASE_URL}/api/workflows/{workflow_id}/connections",
                json=connection_payload,
                headers={"Content-Type": "application/json"},
            )

            if connection_response.status_code == 200:
                print("  ✅ Added connection between agents")
            else:
                print(f"  ❌ Failed to add connection: {connection_response.status_code}")
                print(f"     {connection_response.text}")

            # Now try to fetch workflows to see if it appears
            print("\nFetching workflows...")
            workflows_response = requests.get(f"{API_BASE_URL}/api/workflows/")

            if workflows_response.status_code == 200:
                workflows = workflows_response.json()
                print(f"Found {len(workflows)} workflows:")
                for workflow in workflows:
                    print(f"  - {workflow['name']} (ID: {workflow['workflow_id']})")
            else:
                print(f"Failed to fetch workflows: {workflows_response.status_code}")
                print(workflows_response.text)

        else:
            print(f"❌ Failed to create workflow: {workflow_response.status_code}")
            print(workflow_response.text)

    except Exception as e:
        print(f"❌ Error: {e}")


def create_second_demo_workflow():
    """Create a second demo workflow."""

    print("\nCreating second demo workflow...")

    try:
        # Get available agents
        agents_response = requests.get(f"{API_BASE_URL}/api/agents/deployment/available")
        agents = agents_response.json()

        if len(agents) >= 2:
            # Create a different workflow
            import time

            timestamp = str(int(time.time()))

            workflow_data = {
                "name": f"Data Processing Pipeline {timestamp}",
                "description": "A workflow for processing and analyzing large datasets",
                "version": f"1.0.{timestamp}",
                "created_by": "demo_script",
                "is_active": True,
                "tags": ["demo", "data_processing", "analytics"],
                "configuration": {"demo": True, "pipeline_type": "data_processing", "timestamp": timestamp},
            }

            workflow_response = requests.post(
                f"{API_BASE_URL}/api/workflows/", json=workflow_data, headers={"Content-Type": "application/json"}
            )

            if workflow_response.status_code == 200:
                workflow_result = workflow_response.json()
                print("✅ Second workflow created successfully!")
                print(f"Response: {json.dumps(workflow_result, indent=2)}")

                # Add agents to the second workflow
                workflow_id = workflow_result["workflow_id"]
                agent_data = {
                    "workflow_id": workflow_id,
                    "agent_id": agents[0]["agent_id"],
                    "position_x": 150,
                    "position_y": 200,
                    "node_id": f"node-{agents[0]['agent_id']}-v2",
                    "agent_config": {"demo": True, "version": 2},
                }

                requests.post(
                    f"{API_BASE_URL}/api/workflows/{workflow_id}/agents",
                    json=agent_data,
                    headers={"Content-Type": "application/json"},
                )
                print("  ✅ Added agent to second workflow")

            else:
                print(f"❌ Failed to create second workflow: {workflow_response.status_code}")
                print(workflow_response.text)
        else:
            print("Not enough agents for second workflow")

    except Exception as e:
        print(f"❌ Error creating second workflow: {e}")


if __name__ == "__main__":
    print("Creating demo workflows via API...")

    # Check if API is running
    try:
        health_response = requests.get(f"{API_BASE_URL}/hc")
        if health_response.status_code != 200:
            print(f"❌ API is not running or not healthy. Status: {health_response.status_code}")
            exit(1)
        print("✅ API is running and healthy")
    except Exception as e:
        print(f"❌ Cannot connect to API at {API_BASE_URL}: {e}")
        print("Make sure the API is running on localhost:8000")
        exit(1)

    # Create demo workflows
    create_demo_workflow_via_api()
    create_second_demo_workflow()

    print(f"\n🎉 Demo workflows creation completed!")
    print("\nYou can now test the frontend workflow management features:")
    print("1. Open the frontend and go to the Workflows tab")
    print("2. You should see the demo workflows listed")
    print("3. Try loading, editing, and saving workflows")
