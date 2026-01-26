"""
Tests for tenant database seeding functionality.

Tests the SeedDataLoader and seed data JSON files.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from workflow_engine_poc.seeding.loader import SeedDataLoader, SEED_DATA_DIR


@pytest.mark.api
class TestSeedDataFiles:
    """Tests for seed data JSON files."""

    def test_seed_data_directory_exists(self):
        """Verify the seed_data directory exists."""
        assert SEED_DATA_DIR.exists()
        assert SEED_DATA_DIR.is_dir()

    def test_prompts_json_valid(self):
        """Verify prompts.json is valid JSON with expected structure."""
        filepath = SEED_DATA_DIR / "prompts.json"
        assert filepath.exists(), "prompts.json should exist"

        with open(filepath, "r") as f:
            data = json.load(f)

        assert "prompts" in data
        assert isinstance(data["prompts"], list)

        for prompt in data["prompts"]:
            assert "template_id" in prompt
            assert "prompt_label" in prompt
            assert "prompt" in prompt
            assert "unique_label" in prompt

    def test_tools_json_valid(self):
        """Verify tools.json is valid JSON with expected structure."""
        filepath = SEED_DATA_DIR / "tools.json"
        assert filepath.exists(), "tools.json should exist"

        with open(filepath, "r") as f:
            data = json.load(f)

        assert "tools" in data
        assert isinstance(data["tools"], list)

        for tool in data["tools"]:
            assert "template_id" in tool
            assert "name" in tool
            assert "description" in tool
            assert "tool_type" in tool

    def test_agents_json_valid(self):
        """Verify agents.json is valid JSON with expected structure."""
        filepath = SEED_DATA_DIR / "agents.json"
        assert filepath.exists(), "agents.json should exist"

        with open(filepath, "r") as f:
            data = json.load(f)

        assert "agents" in data
        assert isinstance(data["agents"], list)

        for agent in data["agents"]:
            assert "template_id" in agent
            assert "name" in agent
            assert "prompt_template_id" in agent

    def test_workflows_json_valid(self):
        """Verify workflows.json is valid JSON with expected structure."""
        filepath = SEED_DATA_DIR / "workflows.json"
        assert filepath.exists(), "workflows.json should exist"

        with open(filepath, "r") as f:
            data = json.load(f)

        assert "workflows" in data
        assert isinstance(data["workflows"], list)

        for workflow in data["workflows"]:
            assert "template_id" in workflow
            assert "name" in workflow
            assert "steps" in workflow


@pytest.mark.api
class TestSeedDataLoader:
    """Tests for SeedDataLoader class."""

    def test_loader_initialization(self):
        """Test SeedDataLoader initializes with empty mappings."""
        mock_session = MagicMock()
        loader = SeedDataLoader(mock_session)

        assert loader.session == mock_session
        assert loader.prompt_ids == {}
        assert loader.tool_ids == {}
        assert loader.agent_ids == {}
        assert loader.workflow_ids == {}

    def test_load_json_missing_file(self):
        """Test _load_json returns empty dict for missing file."""
        mock_session = MagicMock()
        loader = SeedDataLoader(mock_session)

        result = loader._load_json("nonexistent.json")
        assert result == {}

    def test_load_json_existing_file(self):
        """Test _load_json loads existing file."""
        mock_session = MagicMock()
        loader = SeedDataLoader(mock_session)

        # prompts.json should exist
        result = loader._load_json("prompts.json")
        assert "prompts" in result

    @patch("workflow_engine_poc.seeding.loader.PromptsService")
    def test_load_prompts_creates_prompts(self, mock_prompts_service):
        """Test load_prompts creates prompts and stores IDs."""
        mock_session = MagicMock()
        loader = SeedDataLoader(mock_session)

        # Mock the created prompt
        mock_prompt = MagicMock()
        mock_prompt.id = uuid4()
        mock_prompts_service.create_prompt.return_value = mock_prompt

        count = loader.load_prompts()

        # Should have created prompts
        assert count > 0
        assert mock_prompts_service.create_prompt.called
        # Should have stored the ID mapping
        assert len(loader.prompt_ids) > 0

    @patch("workflow_engine_poc.seeding.loader.ToolsService")
    def test_load_tools_creates_tools(self, mock_tools_service):
        """Test load_tools creates tools and stores IDs."""
        mock_session = MagicMock()
        loader = SeedDataLoader(mock_session)

        # Mock the created tool
        mock_tool = MagicMock()
        mock_tool.id = uuid4()
        mock_tools_service.create_tool.return_value = mock_tool

        count = loader.load_tools()

        assert count > 0
        assert mock_tools_service.create_tool.called
        assert len(loader.tool_ids) > 0

    @patch("workflow_engine_poc.seeding.loader.PromptsService")
    def test_load_prompts_handles_duplicates(self, mock_prompts_service):
        """Test load_prompts handles duplicate errors gracefully."""
        mock_session = MagicMock()
        loader = SeedDataLoader(mock_session)

        # Simulate duplicate error
        mock_prompts_service.create_prompt.side_effect = ValueError(
            "Prompt with this unique_label already exists"
        )

        # Should not raise, just return 0
        count = loader.load_prompts()
        assert count == 0

    @patch("workflow_engine_poc.seeding.loader.WorkflowsService")
    @patch("workflow_engine_poc.seeding.loader.AgentsService")
    @patch("workflow_engine_poc.seeding.loader.ToolsService")
    @patch("workflow_engine_poc.seeding.loader.PromptsService")
    def test_load_all_calls_in_order(
        self, mock_prompts, mock_tools, mock_agents, mock_workflows
    ):
        """Test load_all loads entities in correct order."""
        mock_session = MagicMock()
        loader = SeedDataLoader(mock_session)

        # Mock all services
        mock_prompt = MagicMock()
        mock_prompt.id = uuid4()
        mock_prompts.create_prompt.return_value = mock_prompt

        mock_tool = MagicMock()
        mock_tool.id = uuid4()
        mock_tools.create_tool.return_value = mock_tool

        mock_agent = MagicMock()
        mock_agent.id = uuid4()
        mock_agents.create_agent.return_value = mock_agent

        mock_workflow = MagicMock()
        mock_workflow.id = uuid4()
        mock_workflows.create_workflow.return_value = mock_workflow

        results = loader.load_all()

        assert "prompts" in results
        assert "tools" in results
        assert "agents" in results
        assert "workflows" in results


@pytest.mark.api
class TestSeedTenantDataInitializer:
    """Tests for the seed_tenant_data initializer."""

    def test_initializer_is_registered(self):
        """Verify seed_tenant_data is registered as a tenant initializer."""
        from db_core import get_tenant_initializers

        initializers = get_tenant_initializers()
        initializer_names = [i.__name__ for i in initializers]

        assert "seed_tenant_data" in initializer_names

    def test_initializer_order_after_migrations(self):
        """Verify seed_tenant_data runs after init_workflow_tables."""
        from db_core import get_tenant_initializers

        initializers = get_tenant_initializers()
        initializer_names = [i.__name__ for i in initializers]

        migration_idx = initializer_names.index("init_workflow_tables")
        seeding_idx = initializer_names.index("seed_tenant_data")

        assert seeding_idx > migration_idx, "Seeding should run after migrations"
