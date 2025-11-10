"""
Integration tests for Agents API endpoints.

Tests all CRUD operations for agents including:
- Create agent
- List agents with filters
- Get agent by ID
- Update agent
- Delete agent
- Attach/detach tools (functions)
- Error cases and validation
"""

import pytest
import uuid
from fastapi.testclient import TestClient


class TestAgentsAPI:
    """Test suite for Agents API endpoints."""

    @pytest.fixture
    def sample_prompt(self, test_client: TestClient):
        """Create a sample prompt for agent testing."""
        prompt_data = {
            "prompt_label": "Test Agent Prompt",
            "prompt": "You are a helpful test agent.",
            "unique_label": f"AgentPrompt_{uuid.uuid4().hex[:8]}",
            "app_name": "test_app",
            "version": "1.0.0",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4o-mini",
        }
        response = test_client.post("/api/prompts/", json=prompt_data)
        assert response.status_code == 200
        return response.json()

    def test_create_agent_success(self, test_client: TestClient, sample_prompt):
        """Test creating an agent with all fields."""
        agent_data = {
            "name": f"Test Agent {uuid.uuid4().hex[:8]}",
            "agent_type": "router",
            "description": "A test agent for integration testing",
            "system_prompt_id": sample_prompt["pid"],
            "persona": "Helpful assistant",
            "routing_options": {"respond": "Respond directly"},
            "functions": [],
            "short_term_memory": True,
            "long_term_memory": False,
            "reasoning": False,
            "input_type": ["text"],
            "output_type": ["text"],
            "response_type": "json",
            "max_retries": 3,
            "timeout": None,
            "deployed": False,
            "status": "active",
            "priority": None,
            "failure_strategies": ["retry"],
            "collaboration_mode": "single",
            "deployment_code": "test",
            "available_for_deployment": True,
        }

        response = test_client.post("/api/agents/", json=agent_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == agent_data["name"]
        assert data["agent_type"] == agent_data["agent_type"]
        assert data["description"] == agent_data["description"]
        assert "agent_id" in data  # UUID
        assert "id" in data  # Integer ID for backwards compatibility

    def test_create_agent_minimal_fields(self, test_client: TestClient, sample_prompt):
        """Test creating an agent with only required fields."""
        agent_data = {
            "name": f"Minimal Agent {uuid.uuid4().hex[:8]}",
            "system_prompt_id": sample_prompt["pid"],
            "routing_options": {},
            "functions": [],
        }

        response = test_client.post("/api/agents/", json=agent_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == agent_data["name"]
        assert data["status"] == "active"  # Default value

    def test_create_agent_with_gemini_and_tools(self, test_client: TestClient, sample_prompt):
        """Test creating an agent with Gemini model and tools (as UI would send)."""
        # This mimics what the UI sends when creating an agent with:
        # - Gemini 2.5 Flash model
        # - Tools attached
        # - Provider config with model_name
        agent_data = {
            "name": f"Gemini Agent {uuid.uuid4().hex[:8]}",
            "agent_type": "router",
            "description": "Test agent with Gemini model and tools",
            "system_prompt_id": sample_prompt["pid"],
            "persona": "Helpful assistant",
            "routing_options": {"respond": "Respond directly"},
            "functions": [
                {
                    "function": {
                        "name": "web_search",
                        "description": "Search the web for information",
                        "parameters": {
                            "type": "object",
                            "properties": {"query": {"type": "string", "description": "The search query"}},
                            "required": ["query"],
                        },
                    }
                },
                {
                    "function": {
                        "name": "get_current_time",
                        "description": "Get the current time",
                        "parameters": {
                            "type": "object",
                            "properties": {"timezone": {"type": "string", "description": "The timezone"}},
                            "required": [],
                        },
                    }
                },
            ],
            "provider_type": "gemini_textgen",
            "provider_config": {
                "model_name": "gemini-2.5-flash",
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            "short_term_memory": False,
            "long_term_memory": False,
            "reasoning": False,
            "input_type": ["text"],
            "output_type": ["text"],
            "response_type": "markdown",
            "max_retries": 3,
            "status": "active",
            "collaboration_mode": "single",
        }

        response = test_client.post("/api/agents/", json=agent_data)

        assert response.status_code == 200
        data = response.json()

        # Debug: print the response to see what we're getting
        import json

        print("\n=== AGENT RESPONSE ===")
        print(json.dumps(data, indent=2, default=str))
        print("======================\n")

        # Verify basic fields
        assert data["name"] == agent_data["name"]
        assert data["agent_type"] == agent_data["agent_type"]
        assert data["description"] == agent_data["description"]
        assert "agent_id" in data

        # Verify provider configuration
        assert data["provider_type"] == "gemini_textgen"
        assert data["provider_config"]["model_name"] == "gemini-2.5-flash"
        assert data["provider_config"]["temperature"] == 0.7
        assert data["provider_config"]["max_tokens"] == 4096

        # Verify AS-specific fields are stored under legacy_fields
        assert "legacy_fields" in data["provider_config"]
        assert data["provider_config"]["legacy_fields"]["response_type"] == "markdown"
        assert data["provider_config"]["legacy_fields"]["short_term_memory"] is False

        # Verify tools/functions are persisted
        assert len(data["functions"]) == 2
        function_names = [f["function"]["name"] for f in data["functions"]]
        assert "web_search" in function_names
        assert "get_current_time" in function_names

        # Cleanup
        test_client.delete(f"/api/agents/{data['agent_id']}")

    def test_list_agents_empty(self, test_client: TestClient):
        """Test listing agents when none exist."""
        response = test_client.get("/api/agents/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_agents_with_pagination(self, test_client: TestClient, sample_prompt):
        """Test listing agents with pagination."""
        # Create multiple agents
        created_ids = []
        for i in range(3):
            agent_data = {
                "name": f"Agent {i} {uuid.uuid4().hex[:8]}",
                "system_prompt_id": sample_prompt["pid"],
                "routing_options": {},
                "functions": [],
            }
            response = test_client.post("/api/agents/", json=agent_data)
            assert response.status_code == 200
            created_ids.append(response.json()["agent_id"])

        # Test pagination
        response = test_client.get("/api/agents/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2  # At least our 2 agents

        # Cleanup
        for agent_id in created_ids:
            test_client.delete(f"/api/agents/{agent_id}")

    def test_get_agent_by_id_success(self, test_client: TestClient, sample_prompt):
        """Test getting a specific agent by ID."""
        # Create an agent
        agent_data = {
            "name": f"Get Test Agent {uuid.uuid4().hex[:8]}",
            "system_prompt_id": sample_prompt["pid"],
            "routing_options": {},
            "functions": [],
        }
        create_response = test_client.post("/api/agents/", json=agent_data)
        assert create_response.status_code == 200
        agent_id = create_response.json()["agent_id"]

        # Get the agent
        response = test_client.get(f"/api/agents/{agent_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == agent_data["name"]
        assert str(data["agent_id"]) == str(agent_id)

        # Cleanup
        test_client.delete(f"/api/agents/{agent_id}")

    def test_get_agent_not_found(self, test_client: TestClient):
        """Test getting a non-existent agent."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/agents/{fake_id}")

        assert response.status_code == 404

    def test_update_agent_success(self, test_client: TestClient, sample_prompt):
        """Test updating an agent."""
        # Create an agent
        agent_data = {
            "name": f"Original Agent {uuid.uuid4().hex[:8]}",
            "system_prompt_id": sample_prompt["pid"],
            "routing_options": {},
            "functions": [],
        }
        create_response = test_client.post("/api/agents/", json=agent_data)
        assert create_response.status_code == 200
        agent_id = create_response.json()["agent_id"]

        # Update the agent
        update_data = {
            "name": "Updated Agent",
            "description": "Updated description",
        }
        response = test_client.put(f"/api/agents/{agent_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]

        # Cleanup
        test_client.delete(f"/api/agents/{agent_id}")

    def test_update_agent_not_found(self, test_client: TestClient):
        """Test updating a non-existent agent."""
        fake_id = str(uuid.uuid4())
        update_data = {"name": "Updated"}

        response = test_client.put(f"/api/agents/{fake_id}", json=update_data)

        assert response.status_code == 404

    def test_delete_agent_success(self, test_client: TestClient, sample_prompt):
        """Test deleting an agent."""
        # Create an agent
        agent_data = {
            "name": f"Delete Test Agent {uuid.uuid4().hex[:8]}",
            "system_prompt_id": sample_prompt["pid"],
            "routing_options": {},
            "functions": [],
        }
        create_response = test_client.post("/api/agents/", json=agent_data)
        assert create_response.status_code == 200
        agent_id = create_response.json()["agent_id"]

        # Delete the agent
        response = test_client.delete(f"/api/agents/{agent_id}")

        assert response.status_code == 200

        # Verify it's deleted
        get_response = test_client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 404

    def test_delete_agent_not_found(self, test_client: TestClient):
        """Test deleting a non-existent agent."""
        fake_id = str(uuid.uuid4())
        response = test_client.delete(f"/api/agents/{fake_id}")

        assert response.status_code == 404

    def test_agent_with_different_types(self, test_client: TestClient, sample_prompt):
        """Test creating agents with different agent types."""
        agent_types = ["router", "web_search", "data", "api"]

        created_ids = []
        for agent_type in agent_types:
            agent_data = {
                "name": f"{agent_type.title()} Agent",
                "agent_type": agent_type,
                "system_prompt_id": sample_prompt["pid"],
                "routing_options": {},
                "functions": [],
            }
            response = test_client.post("/api/agents/", json=agent_data)
            assert response.status_code == 200
            data = response.json()
            assert data["agent_type"] == agent_type
            created_ids.append(data["agent_id"])

        # Cleanup
        for agent_id in created_ids:
            test_client.delete(f"/api/agents/{agent_id}")

    def test_agent_lifecycle(self, test_client: TestClient, sample_prompt):
        """Test complete agent lifecycle: create -> read -> update -> delete."""
        # Create
        agent_data = {
            "name": f"Lifecycle Agent {uuid.uuid4().hex[:8]}",
            "system_prompt_id": sample_prompt["pid"],
            "routing_options": {},
            "functions": [],
        }
        create_response = test_client.post("/api/agents/", json=agent_data)
        assert create_response.status_code == 200
        agent_id = create_response.json()["agent_id"]

        # Read
        get_response = test_client.get(f"/api/agents/{agent_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == agent_data["name"]

        # Update
        update_data = {"name": "Updated Lifecycle Agent"}
        update_response = test_client.put(f"/api/agents/{agent_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["name"] == update_data["name"]

        # Delete
        delete_response = test_client.delete(f"/api/agents/{agent_id}")
        assert delete_response.status_code == 200

        # Verify deleted
        final_get = test_client.get(f"/api/agents/{agent_id}")
        assert final_get.status_code == 404
