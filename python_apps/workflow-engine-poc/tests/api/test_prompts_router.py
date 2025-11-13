"""
Comprehensive tests for Prompts Router

Tests all CRUD endpoints for prompts with various scenarios:
- Create prompt (success, duplicate unique_label)
- List prompts (with various filters, pagination, empty results)
- Get prompt (success, not found)
- Update prompt (success, not found)
- Delete prompt (success, not found)
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from workflow_engine_poc.main import app
from workflow_core_sdk.db.models import Prompt, PromptCreate, PromptUpdate
from workflow_core_sdk.services.prompts_service import PromptsQuery

client = TestClient(app)


@pytest.fixture
def mock_session():
    """Mock database session"""
    return MagicMock()


@pytest.fixture
def sample_prompt():
    """Sample prompt for testing"""
    return Prompt(
        id=uuid.uuid4(),
        prompt_label="Test Prompt",
        prompt="You are a helpful assistant",
        unique_label="test-prompt-v1",
        app_name="test-app",
        ai_model_provider="openai",
        ai_model_name="gpt-4",
        tags=["test", "assistant"],
        hyper_parameters={"temperature": 0.7, "max_tokens": 1000},
        variables={"context": "testing"},
        organization_id="org-123",
        created_by="user-456",
        created_time=datetime.utcnow(),
        updated_time=None,
    )


@pytest.mark.api
class TestCreatePrompt:
    """Tests for POST /prompts/"""

    @patch("workflow_engine_poc.routers.prompts.PromptsService.create_prompt")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_prompt_success(self, mock_guard, mock_get_session, mock_create, mock_session, sample_prompt):
        """Test successful prompt creation"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_create.return_value = sample_prompt

        payload = {
            "prompt_label": "Test Prompt",
            "prompt": "You are a helpful assistant",
            "unique_label": "test-prompt-v1",
            "app_name": "test-app",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4",
            "tags": ["test", "assistant"],
            "hyper_parameters": {"temperature": 0.7},
            "variables": {"context": "testing"},
            "organization_id": "org-123",
        }

        response = client.post("/prompts/", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_label"] == "Test Prompt"
        assert data["unique_label"] == "test-prompt-v1"
        assert data["app_name"] == "test-app"
        assert "id" in data
        mock_create.assert_called_once()

    @patch("workflow_engine_poc.routers.prompts.PromptsService.create_prompt")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_create_prompt_duplicate_unique_label(self, mock_guard, mock_get_session, mock_create, mock_session):
        """Test creating prompt with duplicate unique_label raises 409"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_create.side_effect = ValueError("Prompt with this unique_label already exists")

        payload = {
            "prompt_label": "Test Prompt",
            "prompt": "You are a helpful assistant",
            "unique_label": "existing-prompt",
            "app_name": "test-app",
            "ai_model_provider": "openai",
            "ai_model_name": "gpt-4",
        }

        response = client.post("/prompts/", json=payload)

        assert response.status_code == 409
        assert "unique_label" in response.json()["detail"]


@pytest.mark.api
class TestListPrompts:
    """Tests for GET /prompts/"""

    @patch("workflow_engine_poc.routers.prompts.PromptsService.list_prompts")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_prompts_no_filters(self, mock_guard, mock_get_session, mock_list, mock_session, sample_prompt):
        """Test listing prompts without filters"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_prompt]

        response = client.get("/prompts/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["prompt_label"] == "Test Prompt"

        # Verify PromptsQuery was created with defaults
        call_args = mock_list.call_args
        query = call_args[0][1]
        assert isinstance(query, PromptsQuery)
        assert query.limit == 100
        assert query.offset == 0

    @patch("workflow_engine_poc.routers.prompts.PromptsService.list_prompts")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_prompts_with_filters(self, mock_guard, mock_get_session, mock_list, mock_session, sample_prompt):
        """Test listing prompts with various filters"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_prompt]

        response = client.get(
            "/prompts/",
            params={
                "organization_id": "org-123",
                "app_name": "test-app",
                "provider": "openai",
                "model": "gpt-4",
                "tag": "test",
                "q": "Test",
                "limit": 50,
                "offset": 10,
            },
        )

        assert response.status_code == 200

        # Verify filters were passed to service
        call_args = mock_list.call_args
        query = call_args[0][1]
        assert query.organization_id == "org-123"
        assert query.app_name == "test-app"
        assert query.provider == "openai"
        assert query.model == "gpt-4"
        assert query.tag == "test"
        assert query.q == "Test"
        assert query.limit == 50
        assert query.offset == 10

    @patch("workflow_engine_poc.routers.prompts.PromptsService.list_prompts")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_prompts_empty_results(self, mock_guard, mock_get_session, mock_list, mock_session):
        """Test listing prompts returns empty list when no matches"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = []

        response = client.get("/prompts/", params={"app_name": "nonexistent"})

        assert response.status_code == 200
        assert response.json() == []

    @patch("workflow_engine_poc.routers.prompts.PromptsService.list_prompts")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_list_prompts_pagination(self, mock_guard, mock_get_session, mock_list, mock_session, sample_prompt):
        """Test pagination parameters"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_list.return_value = [sample_prompt]

        response = client.get("/prompts/", params={"limit": 10, "offset": 20})

        assert response.status_code == 200
        call_args = mock_list.call_args
        query = call_args[0][1]
        assert query.limit == 10
        assert query.offset == 20


@pytest.mark.api
class TestGetPrompt:
    """Tests for GET /prompts/{prompt_id}"""

    @patch("workflow_engine_poc.routers.prompts.PromptsService.get_prompt")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_prompt_success(self, mock_guard, mock_get_session, mock_get, mock_session, sample_prompt):
        """Test successfully retrieving a prompt"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = sample_prompt

        prompt_id = str(sample_prompt.id)
        response = client.get(f"/prompts/{prompt_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_label"] == "Test Prompt"
        assert data["unique_label"] == "test-prompt-v1"
        # Verify service was called with correct prompt_id
        assert mock_get.call_count == 1
        assert mock_get.call_args[0][1] == prompt_id

    @patch("workflow_engine_poc.routers.prompts.PromptsService.get_prompt")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_get_prompt_not_found(self, mock_guard, mock_get_session, mock_get, mock_session):
        """Test getting non-existent prompt returns 404"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_get.return_value = None

        prompt_id = str(uuid.uuid4())
        response = client.get(f"/prompts/{prompt_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.api
class TestUpdatePrompt:
    """Tests for PATCH /prompts/{prompt_id}"""

    @patch("workflow_engine_poc.routers.prompts.PromptsService.update_prompt")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_update_prompt_success(self, mock_guard, mock_get_session, mock_update, mock_session, sample_prompt):
        """Test successfully updating a prompt"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session

        updated_prompt = sample_prompt
        updated_prompt.prompt_label = "Updated Prompt"
        mock_update.return_value = updated_prompt

        prompt_id = str(sample_prompt.id)
        payload = {"prompt_label": "Updated Prompt"}
        response = client.patch(f"/prompts/{prompt_id}", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["prompt_label"] == "Updated Prompt"
        mock_update.assert_called_once()

    @patch("workflow_engine_poc.routers.prompts.PromptsService.update_prompt")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_update_prompt_not_found(self, mock_guard, mock_get_session, mock_update, mock_session):
        """Test updating non-existent prompt returns 404"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_update.side_effect = ValueError("Prompt not found")

        prompt_id = str(uuid.uuid4())
        payload = {"prompt_label": "Updated"}
        response = client.patch(f"/prompts/{prompt_id}", json=payload)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.api
class TestDeletePrompt:
    """Tests for DELETE /prompts/{prompt_id}"""

    @patch("workflow_engine_poc.routers.prompts.PromptsService.delete_prompt")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_delete_prompt_success(self, mock_guard, mock_get_session, mock_delete, mock_session, sample_prompt):
        """Test successfully deleting a prompt"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_delete.return_value = True

        prompt_id = str(sample_prompt.id)
        response = client.delete(f"/prompts/{prompt_id}")

        assert response.status_code == 200
        assert response.json()["deleted"] is True
        # Verify service was called with correct prompt_id
        assert mock_delete.call_count == 1
        assert mock_delete.call_args[0][1] == prompt_id

    @patch("workflow_engine_poc.routers.prompts.PromptsService.delete_prompt")
    @patch("workflow_engine_poc.routers.prompts.get_db_session")
    @patch("workflow_engine_poc.routers.prompts.api_key_or_user_guard")
    @pytest.mark.api
    def test_delete_prompt_not_found(self, mock_guard, mock_get_session, mock_delete, mock_session):
        """Test deleting non-existent prompt returns 404"""
        mock_guard.return_value = lambda: "user-123"
        mock_get_session.return_value = mock_session
        mock_delete.return_value = False

        prompt_id = str(uuid.uuid4())
        response = client.delete(f"/prompts/{prompt_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
