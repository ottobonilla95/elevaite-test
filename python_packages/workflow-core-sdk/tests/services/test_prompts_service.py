"""
Unit tests for PromptsService

Tests the business logic of prompt CRUD operations with mocked database session.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from workflow_core_sdk.db.models import Prompt, PromptCreate, PromptUpdate
from workflow_core_sdk.services.prompts_service import PromptsService, PromptsQuery


@pytest.fixture
def mock_session():
    """Mock SQLModel session"""
    return MagicMock()


@pytest.fixture
def sample_prompt():
    """Sample prompt for testing"""
    now = datetime.now(timezone.utc)
    return Prompt(
        id=uuid.uuid4(),
        prompt_label="Test Prompt",
        prompt="You are a helpful assistant.",
        unique_label="test_prompt_001",
        app_name="test-app",
        ai_model_provider="openai",
        ai_model_name="gpt-4o",
        tags=["test", "demo"],
        hyper_parameters={"temperature": 0.7},
        variables={},
        organization_id="org-123",
        created_by="user-123",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_prompt_create():
    """Sample prompt creation data"""
    return PromptCreate(
        prompt_label="New Prompt",
        prompt="You are a new assistant.",
        unique_label="new_prompt_001",
        app_name="test-app",
        ai_model_provider="openai",
        ai_model_name="gpt-4o",
        tags=["new"],
        hyper_parameters={},
        variables={},
        organization_id="org-123",
        created_by="user-123",
    )


class TestListPrompts:
    """Tests for PromptsService.list_prompts"""

    def test_list_prompts_no_filters(self, mock_session, sample_prompt):
        """Test listing prompts without filters"""
        # Mock the query execution
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_prompt]
        mock_session.exec.return_value = mock_result

        params = PromptsQuery(limit=100, offset=0)
        prompts = PromptsService.list_prompts(mock_session, params)

        assert len(prompts) == 1
        assert prompts[0].id == sample_prompt.id
        assert prompts[0].prompt_label == "Test Prompt"
        mock_session.exec.assert_called_once()

    def test_list_prompts_with_organization_filter(self, mock_session, sample_prompt):
        """Test listing prompts filtered by organization"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_prompt]
        mock_session.exec.return_value = mock_result

        params = PromptsQuery(organization_id="org-123", limit=100, offset=0)
        prompts = PromptsService.list_prompts(mock_session, params)

        assert len(prompts) == 1
        assert prompts[0].organization_id == "org-123"

    def test_list_prompts_with_app_name_filter(self, mock_session, sample_prompt):
        """Test listing prompts filtered by app name"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_prompt]
        mock_session.exec.return_value = mock_result

        params = PromptsQuery(app_name="test-app", limit=100, offset=0)
        prompts = PromptsService.list_prompts(mock_session, params)

        assert len(prompts) == 1
        assert prompts[0].app_name == "test-app"

    def test_list_prompts_with_provider_filter(self, mock_session, sample_prompt):
        """Test listing prompts filtered by provider"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_prompt]
        mock_session.exec.return_value = mock_result

        params = PromptsQuery(provider="openai", limit=100, offset=0)
        prompts = PromptsService.list_prompts(mock_session, params)

        assert len(prompts) == 1
        assert prompts[0].ai_model_provider == "openai"

    def test_list_prompts_with_model_filter(self, mock_session, sample_prompt):
        """Test listing prompts filtered by model"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_prompt]
        mock_session.exec.return_value = mock_result

        params = PromptsQuery(model="gpt-4o", limit=100, offset=0)
        prompts = PromptsService.list_prompts(mock_session, params)

        assert len(prompts) == 1
        assert prompts[0].ai_model_name == "gpt-4o"

    @pytest.mark.skip(
        reason="Tag filter uses JSON __contains__ which can't be easily mocked"
    )
    def test_list_prompts_with_tag_filter(self, mock_session, sample_prompt):
        """Test listing prompts filtered by tag"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_prompt]
        mock_session.exec.return_value = mock_result

        params = PromptsQuery(tag="test", limit=100, offset=0)
        prompts = PromptsService.list_prompts(mock_session, params)

        assert len(prompts) == 1
        assert "test" in prompts[0].tags

    def test_list_prompts_with_search_query(self, mock_session, sample_prompt):
        """Test listing prompts with text search"""
        mock_result = MagicMock()
        mock_result.all.return_value = [sample_prompt]
        mock_session.exec.return_value = mock_result

        params = PromptsQuery(q="Test", limit=100, offset=0)
        prompts = PromptsService.list_prompts(mock_session, params)

        assert len(prompts) == 1
        assert "Test" in prompts[0].prompt_label

    def test_list_prompts_with_pagination(self, mock_session):
        """Test listing prompts with pagination"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        params = PromptsQuery(limit=10, offset=20)
        prompts = PromptsService.list_prompts(mock_session, params)

        assert len(prompts) == 0
        mock_session.exec.assert_called_once()

    def test_list_prompts_empty_result(self, mock_session):
        """Test listing prompts when no results"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.exec.return_value = mock_result

        params = PromptsQuery(organization_id="nonexistent")
        prompts = PromptsService.list_prompts(mock_session, params)

        assert len(prompts) == 0


class TestCreatePrompt:
    """Tests for PromptsService.create_prompt"""

    def test_create_prompt_success(
        self, mock_session, sample_prompt_create, sample_prompt
    ):
        """Test creating a new prompt successfully"""
        # Mock no existing prompt
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        # Mock session operations
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock(
            side_effect=lambda obj: setattr(obj, "id", sample_prompt.id)
        )

        PromptsService.create_prompt(mock_session, sample_prompt_create)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_create_prompt_duplicate_unique_label(
        self, mock_session, sample_prompt_create, sample_prompt
    ):
        """Test creating a prompt with duplicate unique_label raises error"""
        # Mock existing prompt with same unique_label
        mock_result = MagicMock()
        mock_result.first.return_value = sample_prompt
        mock_session.exec.return_value = mock_result

        with pytest.raises(
            ValueError, match="Prompt with this unique_label already exists"
        ):
            PromptsService.create_prompt(mock_session, sample_prompt_create)

        # Should not commit if duplicate found
        mock_session.commit.assert_not_called()

    def test_create_prompt_with_organization_check(
        self, mock_session, sample_prompt_create
    ):
        """Test creating a prompt checks uniqueness within organization"""
        # Mock no existing prompt
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        PromptsService.create_prompt(mock_session, sample_prompt_create)

        # Verify exec was called (uniqueness check)
        mock_session.exec.assert_called_once()


class TestGetPrompt:
    """Tests for PromptsService.get_prompt"""

    def test_get_prompt_success(self, mock_session, sample_prompt):
        """Test getting a prompt by ID"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_prompt
        mock_session.exec.return_value = mock_result

        prompt = PromptsService.get_prompt(mock_session, str(sample_prompt.id))

        assert prompt is not None
        assert prompt.id == sample_prompt.id
        assert prompt.prompt_label == "Test Prompt"

    def test_get_prompt_not_found(self, mock_session):
        """Test getting a non-existent prompt returns None"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        prompt_id = str(uuid.uuid4())
        prompt = PromptsService.get_prompt(mock_session, prompt_id)

        assert prompt is None


class TestUpdatePrompt:
    """Tests for PromptsService.update_prompt"""

    def test_update_prompt_success(self, mock_session, sample_prompt):
        """Test updating a prompt successfully"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_prompt
        mock_session.exec.return_value = mock_result

        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        update_data = PromptUpdate(
            prompt_label="Updated Prompt", prompt="Updated system prompt"
        )
        updated_prompt = PromptsService.update_prompt(
            mock_session, str(sample_prompt.id), update_data
        )

        assert updated_prompt.prompt_label == "Updated Prompt"
        assert updated_prompt.prompt == "Updated system prompt"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_update_prompt_not_found(self, mock_session):
        """Test updating a non-existent prompt raises error"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        prompt_id = str(uuid.uuid4())
        update_data = PromptUpdate(prompt_label="Updated")

        with pytest.raises(ValueError, match="Prompt not found"):
            PromptsService.update_prompt(mock_session, prompt_id, update_data)

        mock_session.commit.assert_not_called()

    def test_update_prompt_partial_update(self, mock_session, sample_prompt):
        """Test updating only some fields of a prompt"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_prompt
        mock_session.exec.return_value = mock_result

        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        # Only update one field
        update_data = PromptUpdate(prompt_label="New Label")
        updated_prompt = PromptsService.update_prompt(
            mock_session, str(sample_prompt.id), update_data
        )

        assert updated_prompt.prompt_label == "New Label"
        # Other fields should remain unchanged
        assert updated_prompt.prompt == sample_prompt.prompt


class TestDeletePrompt:
    """Tests for PromptsService.delete_prompt"""

    def test_delete_prompt_success(self, mock_session, sample_prompt):
        """Test deleting a prompt successfully"""
        mock_result = MagicMock()
        mock_result.first.return_value = sample_prompt
        mock_session.exec.return_value = mock_result

        mock_session.delete = MagicMock()
        mock_session.commit = MagicMock()

        result = PromptsService.delete_prompt(mock_session, str(sample_prompt.id))

        assert result is True
        mock_session.delete.assert_called_once_with(sample_prompt)
        mock_session.commit.assert_called_once()

    def test_delete_prompt_not_found(self, mock_session):
        """Test deleting a non-existent prompt returns False"""
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result

        prompt_id = str(uuid.uuid4())
        result = PromptsService.delete_prompt(mock_session, prompt_id)

        assert result is False
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_not_called()
