import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from services.demo_service import DemoInitializationService
from db.fixtures import DEFAULT_PROMPTS, DEFAULT_AGENTS


@pytest.mark.unit
class TestDemoInitializationService:
    def test_service_initialization(self):
        mock_db = Mock(spec=Session)
        service = DemoInitializationService(mock_db)

        assert service.db == mock_db

    @patch("services.demo_service.sqlalchemy.inspect")
    @patch("services.demo_service.crud.create_prompt")
    def test_initialize_prompts_success(self, mock_create_prompt, mock_inspect):
        mock_db = Mock(spec=Session)
        mock_inspector = Mock()
        mock_inspector.has_table.return_value = True
        mock_inspect.return_value = mock_inspector

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        service = DemoInitializationService(mock_db)
        success, message, details = service.initialize_prompts()

        assert success is True
        assert "Successfully processed" in message
        assert details["added_count"] == len(DEFAULT_PROMPTS)
        assert details["skipped_count"] == 0
        assert len(details["added_prompts"]) == len(DEFAULT_PROMPTS)

        assert mock_create_prompt.call_count == len(DEFAULT_PROMPTS)

    @patch("services.demo_service.sqlalchemy.inspect")
    def test_initialize_prompts_table_missing(self, mock_inspect):
        mock_db = Mock(spec=Session)
        mock_inspector = Mock()
        mock_inspector.has_table.return_value = False
        mock_inspect.return_value = mock_inspector

        service = DemoInitializationService(mock_db)
        success, message, details = service.initialize_prompts()

        assert success is False
        assert "prompts table does not exist" in message
        assert details == {}

    @patch("services.demo_service.sqlalchemy.inspect")
    @patch("services.demo_service.crud.create_prompt")
    def test_initialize_prompts_with_existing(self, mock_create_prompt, mock_inspect):
        mock_db = Mock(spec=Session)
        mock_inspector = Mock()
        mock_inspector.has_table.return_value = True
        mock_inspect.return_value = mock_inspector

        def mock_query_side_effect(*args):
            mock_query = Mock()
            if hasattr(mock_query_side_effect, "call_count"):
                mock_query_side_effect.call_count += 1
            else:
                mock_query_side_effect.call_count = 1

            if mock_query_side_effect.call_count == 1:
                mock_query.filter.return_value.first.return_value = (
                    Mock()
                )  # Existing prompt
            else:
                mock_query.filter.return_value.first.return_value = (
                    None  # No existing prompt
                )
            return mock_query

        mock_db.query.side_effect = mock_query_side_effect

        service = DemoInitializationService(mock_db)
        success, message, details = service.initialize_prompts()

        assert success is True
        assert details["added_count"] == len(DEFAULT_PROMPTS) - 1
        assert details["skipped_count"] == 1

    @patch("services.demo_service.sqlalchemy.inspect")
    @patch("services.demo_service.crud.create_agent")
    @patch("services.demo_service.uuid.UUID")
    def test_initialize_agents_success(
        self, mock_uuid, mock_create_agent, mock_inspect
    ):
        mock_db = Mock(spec=Session)
        mock_inspector = Mock()
        mock_inspector.has_table.return_value = True
        mock_inspect.return_value = mock_inspector

        mock_uuid.return_value = "test-uuid"

        def mock_query_side_effect(model):
            mock_query = Mock()

            if hasattr(model, "__tablename__") and model.__tablename__ == "agents":
                mock_query.filter.return_value.first.return_value = None
            elif hasattr(model, "__tablename__") and model.__tablename__ == "prompts":
                mock_prompt = Mock()
                mock_prompt.pid = "test-prompt-id"
                mock_query.filter.return_value.first.return_value = mock_prompt
            else:
                mock_prompt = Mock()
                mock_prompt.pid = "test-prompt-id"
                mock_query.filter.return_value.first.return_value = mock_prompt
            return mock_query

        mock_db.query.side_effect = mock_query_side_effect

        service = DemoInitializationService(mock_db)
        success, message, details = service.initialize_agents()

        assert success is True
        assert "Successfully processed" in message
        assert details["added_count"] == len(DEFAULT_AGENTS)
        assert details["updated_count"] == 0
        assert details["skipped_count"] == 0

        assert mock_create_agent.call_count == len(DEFAULT_AGENTS)

    @patch("services.demo_service.sqlalchemy.inspect")
    def test_initialize_agents_missing_prompt(self, mock_inspect):
        mock_db = Mock(spec=Session)
        mock_inspector = Mock()
        mock_inspector.has_table.return_value = True
        mock_inspect.return_value = mock_inspector

        def mock_query_side_effect(model):
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            return mock_query

        mock_db.query.side_effect = mock_query_side_effect

        service = DemoInitializationService(mock_db)
        success, message, details = service.initialize_agents()

        assert success is False
        assert "Required prompt" in message
        assert "not found" in message

    def test_initialize_all_success(self):
        mock_db = Mock(spec=Session)
        service = DemoInitializationService(mock_db)

        service.initialize_prompts = Mock(
            return_value=(True, "Prompts OK", {"prompts": "data"})
        )
        service.initialize_agents = Mock(
            return_value=(True, "Agents OK", {"agents": "data"})
        )

        success, message, details = service.initialize_all()

        assert success is True
        assert message == "Successfully initialized demo data."
        assert "prompts" in details
        assert "agents" in details

    def test_initialize_all_prompts_fail(self):
        mock_db = Mock(spec=Session)
        service = DemoInitializationService(mock_db)

        service.initialize_prompts = Mock(return_value=(False, "Prompts failed", {}))

        success, message, details = service.initialize_all()

        assert success is False
        assert "Failed to initialize prompts" in message

    def test_initialize_all_agents_fail(self):
        mock_db = Mock(spec=Session)
        service = DemoInitializationService(mock_db)

        service.initialize_prompts = Mock(
            return_value=(True, "Prompts OK", {"prompts": "data"})
        )
        service.initialize_agents = Mock(return_value=(False, "Agents failed", {}))

        success, message, details = service.initialize_all()

        assert success is False
        assert "Failed to initialize agents" in message
