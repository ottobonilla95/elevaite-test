"""
Integration tests for Prompts API endpoints.

Tests all CRUD operations for prompts including:
- Create prompt
- List prompts with filters
- Get prompt by ID
- Update prompt
- Delete prompt
- Error cases and validation
"""

import uuid
from fastapi.testclient import TestClient


class TestPromptsAPI:
    """Test suite for Prompts API endpoints."""

    def test_create_prompt_success(self, test_client: TestClient):
        """Test creating a prompt with all fields."""
        prompt_data = {
            "prompt_label": "Test Assistant Prompt",
            "prompt": "You are a helpful test assistant. Always be polite and concise.",
            "unique_label": f"TestPrompt_{uuid.uuid4().hex[:8]}",
            "app_name": "test_app",
            "version": "1.0.0",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4o-mini",
            "tags": ["test", "assistant", "general"],
            "hyper_parameters": {"temperature": "0.7", "max_tokens": "2000"},
            "variables": {"tone": "professional", "domain": "general"},
        }

        response = test_client.post("/api/prompts/", json=prompt_data)

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_label"] == prompt_data["prompt_label"]
        assert data["prompt"] == prompt_data["prompt"]
        assert data["unique_label"] == prompt_data["unique_label"]
        assert data["app_name"] == prompt_data["app_name"]
        assert data["ai_model_provider"] == prompt_data["ai_model_provider"]
        assert data["ai_model_name"] == prompt_data["ai_model_name"]
        assert data["tags"] == prompt_data["tags"]
        assert data["hyper_parameters"] == prompt_data["hyper_parameters"]
        assert data["variables"] == prompt_data["variables"]
        assert "pid" in data  # UUID
        assert "created_time" in data

    def test_create_prompt_minimal_fields(self, test_client: TestClient):
        """Test creating a prompt with only required fields."""
        prompt_data = {
            "prompt_label": "Minimal Prompt",
            "prompt": "You are a minimal assistant.",
            "unique_label": f"MinimalPrompt_{uuid.uuid4().hex[:8]}",
            "app_name": "test_app",
            "version": "1.0.0",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4o-mini",
        }

        response = test_client.post("/api/prompts/", json=prompt_data)

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_label"] == prompt_data["prompt_label"]
        assert data["tags"] == []  # Default empty list
        assert data["hyper_parameters"] == {}  # Default empty dict
        assert data["variables"] == {}  # Default empty dict

    def test_create_prompt_duplicate_unique_label(self, test_client: TestClient):
        """Test that creating a prompt with duplicate unique_label fails."""
        unique_label = f"DuplicatePrompt_{uuid.uuid4().hex[:8]}"
        prompt_data = {
            "prompt_label": "First Prompt",
            "prompt": "First prompt text.",
            "unique_label": unique_label,
            "app_name": "test_app",
            "version": "1.0.0",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4o-mini",
        }

        # Create first prompt
        response1 = test_client.post("/api/prompts/", json=prompt_data)
        assert response1.status_code == 200

        # Try to create duplicate
        prompt_data["prompt_label"] = "Second Prompt"
        response2 = test_client.post("/api/prompts/", json=prompt_data)
        assert response2.status_code == 409  # Conflict

    def test_list_prompts_empty(self, test_client: TestClient):
        """Test listing prompts when none exist."""
        response = test_client.get("/api/prompts/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_prompts_with_pagination(self, test_client: TestClient):
        """Test listing prompts with pagination."""
        # Create multiple prompts
        created_ids = []
        for i in range(5):
            prompt_data = {
                "prompt_label": f"Prompt {i}",
                "prompt": f"Prompt text {i}",
                "unique_label": f"Prompt_{i}_{uuid.uuid4().hex[:8]}",
                "app_name": "test_app",
                "version": "1.0.0",
                "ai_model_provider": "openai",
                "ai_model_name": "gpt-4o-mini",
            }
            response = test_client.post("/api/prompts/", json=prompt_data)
            assert response.status_code == 200
            created_ids.append(response.json()["pid"])

        # Test pagination
        response = test_client.get("/api/prompts/?skip=0&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3  # At least our 3 prompts (may have more from other tests)

        # Cleanup
        for prompt_id in created_ids:
            test_client.delete(f"/api/prompts/{prompt_id}")

    def test_get_prompt_by_id_success(self, test_client: TestClient):
        """Test getting a specific prompt by ID."""
        # Create a prompt
        prompt_data = {
            "prompt_label": "Get Test Prompt",
            "prompt": "Test prompt for retrieval.",
            "unique_label": f"GetPrompt_{uuid.uuid4().hex[:8]}",
            "app_name": "test_app",
            "version": "1.0.0",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4o-mini",
        }
        create_response = test_client.post("/api/prompts/", json=prompt_data)
        assert create_response.status_code == 200
        prompt_id = create_response.json()["pid"]

        # Get the prompt
        response = test_client.get(f"/api/prompts/{prompt_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["pid"] == prompt_id
        assert data["prompt_label"] == prompt_data["prompt_label"]
        assert data["prompt"] == prompt_data["prompt"]

        # Cleanup
        test_client.delete(f"/api/prompts/{prompt_id}")

    def test_get_prompt_not_found(self, test_client: TestClient):
        """Test getting a non-existent prompt."""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/api/prompts/{fake_id}")

        assert response.status_code == 404

    def test_update_prompt_success(self, test_client: TestClient):
        """Test updating a prompt."""
        # Create a prompt
        prompt_data = {
            "prompt_label": "Original Prompt",
            "prompt": "Original prompt text.",
            "unique_label": f"UpdatePrompt_{uuid.uuid4().hex[:8]}",
            "app_name": "test_app",
            "version": "1.0.0",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4o-mini",
            "tags": ["original"],
        }
        create_response = test_client.post("/api/prompts/", json=prompt_data)
        assert create_response.status_code == 200
        prompt_id = create_response.json()["pid"]

        # Update the prompt
        update_data = {
            "prompt_label": "Updated Prompt",
            "prompt": "Updated prompt text with new instructions.",
            "tags": ["updated", "modified"],
            "hyper_parameters": {"temperature": "0.9"},
        }
        response = test_client.put(f"/api/prompts/{prompt_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_label"] == update_data["prompt_label"]
        assert data["prompt"] == update_data["prompt"]
        assert data["tags"] == update_data["tags"]
        assert data["hyper_parameters"] == update_data["hyper_parameters"]
        # Original fields should remain
        assert data["unique_label"] == prompt_data["unique_label"]
        assert data["app_name"] == prompt_data["app_name"]

        # Cleanup
        test_client.delete(f"/api/prompts/{prompt_id}")

    def test_update_prompt_partial(self, test_client: TestClient):
        """Test partial update of a prompt (only some fields)."""
        # Create a prompt
        prompt_data = {
            "prompt_label": "Partial Update Prompt",
            "prompt": "Original text.",
            "unique_label": f"PartialPrompt_{uuid.uuid4().hex[:8]}",
            "app_name": "test_app",
            "version": "1.0.0",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4o-mini",
            "tags": ["original"],
        }
        create_response = test_client.post("/api/prompts/", json=prompt_data)
        assert create_response.status_code == 200
        prompt_id = create_response.json()["pid"]

        # Update only the prompt text
        update_data = {"prompt": "Updated text only."}
        response = test_client.put(f"/api/prompts/{prompt_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["prompt"] == update_data["prompt"]
        # Other fields should remain unchanged
        assert data["prompt_label"] == prompt_data["prompt_label"]
        assert data["tags"] == prompt_data["tags"]

        # Cleanup
        test_client.delete(f"/api/prompts/{prompt_id}")

    def test_update_prompt_not_found(self, test_client: TestClient):
        """Test updating a non-existent prompt."""
        fake_id = str(uuid.uuid4())
        update_data = {"prompt_label": "Updated"}

        response = test_client.put(f"/api/prompts/{fake_id}", json=update_data)

        assert response.status_code == 404

    def test_delete_prompt_success(self, test_client: TestClient):
        """Test deleting a prompt."""
        # Create a prompt
        prompt_data = {
            "prompt_label": "Delete Test Prompt",
            "prompt": "This prompt will be deleted.",
            "unique_label": f"DeletePrompt_{uuid.uuid4().hex[:8]}",
            "app_name": "test_app",
            "version": "1.0.0",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4o-mini",
        }
        create_response = test_client.post("/api/prompts/", json=prompt_data)
        assert create_response.status_code == 200
        prompt_id = create_response.json()["pid"]

        # Delete the prompt
        response = test_client.delete(f"/api/prompts/{prompt_id}")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "prompt_id" in data

        # Verify it's deleted
        get_response = test_client.get(f"/api/prompts/{prompt_id}")
        assert get_response.status_code == 404

    def test_delete_prompt_not_found(self, test_client: TestClient):
        """Test deleting a non-existent prompt."""
        fake_id = str(uuid.uuid4())
        response = test_client.delete(f"/api/prompts/{fake_id}")

        assert response.status_code == 404

    def test_prompt_with_different_providers(self, test_client: TestClient):
        """Test creating prompts with different AI providers."""
        providers = [
            ("openai", "gpt-4o-mini"),
            ("anthropic", "claude-3-5-sonnet-20241022"),
            ("google", "gemini-1.5-flash"),
        ]

        created_ids = []
        for provider, model in providers:
            prompt_data = {
                "prompt_label": f"{provider.title()} Prompt",
                "prompt": f"Prompt for {provider}.",
                "unique_label": f"{provider}Prompt_{uuid.uuid4().hex[:8]}",
                "app_name": "test_app",
                "version": "1.0.0",
                "ai_model_provider": provider,
                "ai_model_name": model,
            }
            response = test_client.post("/api/prompts/", json=prompt_data)
            assert response.status_code == 200
            data = response.json()
            assert data["ai_model_provider"] == provider
            assert data["ai_model_name"] == model
            created_ids.append(data["pid"])

        # Cleanup
        for prompt_id in created_ids:
            test_client.delete(f"/api/prompts/{prompt_id}")

    def test_prompt_lifecycle(self, test_client: TestClient):
        """Test complete prompt lifecycle: create -> read -> update -> delete."""
        # Create
        prompt_data = {
            "prompt_label": "Lifecycle Prompt",
            "prompt": "Initial prompt.",
            "unique_label": f"LifecyclePrompt_{uuid.uuid4().hex[:8]}",
            "app_name": "test_app",
            "version": "1.0.0",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4o-mini",
        }
        create_response = test_client.post("/api/prompts/", json=prompt_data)
        assert create_response.status_code == 200
        prompt_id = create_response.json()["pid"]

        # Read
        get_response = test_client.get(f"/api/prompts/{prompt_id}")
        assert get_response.status_code == 200
        assert get_response.json()["prompt_label"] == prompt_data["prompt_label"]

        # Update
        update_data = {"prompt_label": "Updated Lifecycle Prompt"}
        update_response = test_client.put(f"/api/prompts/{prompt_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["prompt_label"] == update_data["prompt_label"]

        # Delete
        delete_response = test_client.delete(f"/api/prompts/{prompt_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        final_get = test_client.get(f"/api/prompts/{prompt_id}")
        assert final_get.status_code == 404
