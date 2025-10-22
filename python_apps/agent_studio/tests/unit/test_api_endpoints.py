import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from db.fixtures import DEFAULT_PROMPTS


class TestPromptEndpoints:
    """Test prompt API endpoints."""

    def test_create_prompt_endpoint(self, test_client: TestClient):
        """Test creating a prompt via API."""
        prompt_data = {
            "prompt_label": "Test Prompt",
            "prompt": "You are a test agent.",
            "unique_label": "TestPrompt",
            "app_name": "test_app",
            "version": "1.0",
            "ai_model_provider": "OpenAI",
            "ai_model_name": "gpt-4",
            "tags": ["test"],
            "hyper_parameters": {"temperature": "0.7"},
            "variables": {"test_var": "test_value"},
        }
        
        response = test_client.post("/prompts/", json=prompt_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["prompt_label"] == "Test Prompt"
        assert data["unique_label"] == "TestPrompt"

    def test_get_prompt_endpoint(self, test_client: TestClient):
        """Test retrieving a prompt via API."""
        # First create a prompt
        prompt_data = {
            "prompt_label": "Test Prompt",
            "prompt": "You are a test agent.",
            "unique_label": "TestPrompt",
            "app_name": "test_app",
            "version": "1.0",
            "ai_model_provider": "OpenAI",
            "ai_model_name": "gpt-4",
            "tags": ["test"],
            "hyper_parameters": {"temperature": "0.7"},
            "variables": {"test_var": "test_value"},
        }
        
        create_response = test_client.post("/prompts/", json=prompt_data)
        assert create_response.status_code == 200
        created_prompt = create_response.json()
        
        # Then retrieve it
        prompt_id = created_prompt["pid"]
        get_response = test_client.get(f"/prompts/{prompt_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["prompt_label"] == "Test Prompt"

    def test_get_prompts_list_endpoint(self, test_client: TestClient):
        """Test retrieving prompts list via API."""
        # Create a few prompts
        for i in range(3):
            prompt_data = {
                "prompt_label": f"Test Prompt {i}",
                "prompt": "You are a test agent.",
                "unique_label": f"TestPrompt{i}",
                "app_name": "test_app",
                "version": "1.0",
                "ai_model_provider": "OpenAI",
                "ai_model_name": "gpt-4",
                "tags": ["test"],
                "hyper_parameters": {"temperature": "0.7"},
                "variables": {"test_var": "test_value"},
            }
            test_client.post("/prompts/", json=prompt_data)
        
        # Get the list
        response = test_client.get("/prompts/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

    def test_update_prompt_endpoint(self, test_client: TestClient):
        """Test updating a prompt via API."""
        # First create a prompt
        prompt_data = {
            "prompt_label": "Test Prompt",
            "prompt": "You are a test agent.",
            "unique_label": "TestPrompt",
            "app_name": "test_app",
            "version": "1.0",
            "ai_model_provider": "OpenAI",
            "ai_model_name": "gpt-4",
            "tags": ["test"],
            "hyper_parameters": {"temperature": "0.7"},
            "variables": {"test_var": "test_value"},
        }
        
        create_response = test_client.post("/prompts/", json=prompt_data)
        assert create_response.status_code == 200
        created_prompt = create_response.json()
        
        # Update it
        prompt_id = created_prompt["pid"]
        update_data = {
            "prompt_label": "Updated Test Prompt",
            "prompt": "You are an updated test agent."
        }
        
        update_response = test_client.put(f"/prompts/{prompt_id}", json=update_data)
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["prompt_label"] == "Updated Test Prompt"

    def test_delete_prompt_endpoint(self, test_client: TestClient):
        """Test deleting a prompt via API."""
        # First create a prompt
        prompt_data = {
            "prompt_label": "Test Prompt",
            "prompt": "You are a test agent.",
            "unique_label": "TestPrompt",
            "app_name": "test_app",
            "version": "1.0",
            "ai_model_provider": "OpenAI",
            "ai_model_name": "gpt-4",
            "tags": ["test"],
            "hyper_parameters": {"temperature": "0.7"},
            "variables": {"test_var": "test_value"},
        }
        
        create_response = test_client.post("/prompts/", json=prompt_data)
        assert create_response.status_code == 200
        created_prompt = create_response.json()
        
        # Delete it
        prompt_id = created_prompt["pid"]
        delete_response = test_client.delete(f"/prompts/{prompt_id}")
        
        assert delete_response.status_code == 200
        
        # Verify it's deleted
        get_response = test_client.get(f"/prompts/{prompt_id}")
        assert get_response.status_code == 404


class TestAgentEndpoints:
    """Test agent API endpoints."""

    def test_create_agent_endpoint(self, test_client: TestClient):
        """Test creating an agent via API."""
        # First create a prompt
        prompt_data = {
            "prompt_label": "Test Prompt",
            "prompt": "You are a test agent.",
            "unique_label": "TestPrompt",
            "app_name": "test_app",
            "version": "1.0",
            "ai_model_provider": "OpenAI",
            "ai_model_name": "gpt-4",
            "tags": ["test"],
            "hyper_parameters": {"temperature": "0.7"},
            "variables": {"test_var": "test_value"},
        }
        
        prompt_response = test_client.post("/prompts/", json=prompt_data)
        assert prompt_response.status_code == 200
        prompt = prompt_response.json()
        
        # Create an agent
        agent_data = {
            "name": "TestAgent",
            "system_prompt_id": prompt["pid"],
            "persona": "Helper",
            "functions": [],
            "routing_options": {"respond": "Respond directly"},
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
            "deployment_code": "t",
            "available_for_deployment": True,
        }
        
        response = test_client.post("/agents/", json=agent_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TestAgent"
        assert data["deployment_code"] == "t"

    def test_get_agent_endpoint(self, test_client: TestClient):
        """Test retrieving an agent via API."""
        # First create a prompt
        prompt_data = {
            "prompt_label": "Test Prompt",
            "prompt": "You are a test agent.",
            "unique_label": "TestPrompt",
            "app_name": "test_app",
            "version": "1.0",
            "ai_model_provider": "OpenAI",
            "ai_model_name": "gpt-4",
            "tags": ["test"],
            "hyper_parameters": {"temperature": "0.7"},
            "variables": {"test_var": "test_value"},
        }
        
        prompt_response = test_client.post("/prompts/", json=prompt_data)
        prompt = prompt_response.json()
        
        # Create an agent
        agent_data = {
            "name": "TestAgent",
            "system_prompt_id": prompt["pid"],
            "persona": "Helper",
            "functions": [],
            "routing_options": {"respond": "Respond directly"},
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
            "deployment_code": "t",
            "available_for_deployment": True,
        }
        
        create_response = test_client.post("/agents/", json=agent_data)
        assert create_response.status_code == 200
        created_agent = create_response.json()
        
        # Retrieve the agent
        agent_id = created_agent["agent_id"]
        get_response = test_client.get(f"/agents/{agent_id}")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["name"] == "TestAgent"

    def test_get_agents_list_endpoint(self, test_client: TestClient):
        """Test retrieving agents list via API."""
        response = test_client.get("/agents/")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_agent_by_deployment_code_endpoint(self, test_client: TestClient):
        """Test retrieving an agent by deployment code via API."""
        # First create a prompt
        prompt_data = {
            "prompt_label": "Test Prompt",
            "prompt": "You are a test agent.",
            "unique_label": "TestPrompt",
            "app_name": "test_app",
            "version": "1.0",
            "ai_model_provider": "OpenAI",
            "ai_model_name": "gpt-4",
            "tags": ["test"],
            "hyper_parameters": {"temperature": "0.7"},
            "variables": {"test_var": "test_value"},
        }
        
        prompt_response = test_client.post("/prompts/", json=prompt_data)
        prompt = prompt_response.json()
        
        # Create an agent with a specific deployment code
        agent_data = {
            "name": "TestAgent",
            "system_prompt_id": prompt["pid"],
            "persona": "Helper",
            "functions": [],
            "routing_options": {"respond": "Respond directly"},
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
            "deployment_code": "z",
            "available_for_deployment": True,
        }
        
        create_response = test_client.post("/agents/", json=agent_data)
        assert create_response.status_code == 200
        
        # Retrieve by deployment code
        get_response = test_client.get("/agents/deployment/z")
        
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["name"] == "TestAgent"
        assert data["deployment_code"] == "z"
