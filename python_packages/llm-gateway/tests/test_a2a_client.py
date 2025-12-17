"""Tests for the A2A Client Service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm_gateway.a2a import (
    A2AAgentInfo,
    A2AClientService,
    A2AMessageRequest,
    A2AMessageResponse,
    A2ATaskInfo,
)


@pytest.fixture
def a2a_service():
    """Create an A2A client service instance."""
    return A2AClientService(default_timeout=10.0)


@pytest.fixture
def sample_agent_info():
    """Create sample agent connection info."""
    return A2AAgentInfo(
        base_url="https://test-agent.example.com",
        name="Test Agent",
        timeout=5.0,
    )


@pytest.fixture
def sample_message_request():
    """Create a sample message request."""
    return A2AMessageRequest(
        content="Hello, agent!",
        context_id="ctx-123",
    )


class TestA2AClientServiceInit:
    """Tests for A2AClientService initialization."""

    def test_init_default_timeout(self):
        """Test default timeout is set correctly."""
        service = A2AClientService()
        assert service._default_timeout == 30.0

    def test_init_custom_timeout(self):
        """Test custom timeout is set correctly."""
        service = A2AClientService(default_timeout=60.0)
        assert service._default_timeout == 60.0

    def test_init_empty_card_cache(self, a2a_service):
        """Test card cache is initialized empty."""
        assert a2a_service._card_cache == {}


class TestA2AAgentInfo:
    """Tests for A2AAgentInfo dataclass."""

    def test_agent_info_minimal(self):
        """Test creating agent info with minimal parameters."""
        info = A2AAgentInfo(base_url="https://agent.example.com")
        assert info.base_url == "https://agent.example.com"
        assert info.name is None
        assert info.agent_card_url is None
        assert info.auth is None
        assert info.timeout == 30.0

    def test_agent_info_full(self):
        """Test creating agent info with all parameters."""
        from llm_gateway.a2a import A2AAuthConfig

        auth = A2AAuthConfig(auth_type="bearer", credentials={"token": "secret"})
        info = A2AAgentInfo(
            base_url="https://agent.example.com",
            name="My Agent",
            agent_card_url="/.well-known/agent.json",
            auth=auth,
            timeout=60.0,
        )
        assert info.name == "My Agent"
        assert info.auth.auth_type == "bearer"
        assert info.timeout == 60.0


class TestA2AMessageRequest:
    """Tests for A2AMessageRequest dataclass."""

    def test_message_request_minimal(self):
        """Test creating message request with minimal parameters."""
        request = A2AMessageRequest(content="Hello")
        assert request.content == "Hello"
        assert request.context_id is None
        assert request.task_id is None
        assert request.metadata is None

    def test_message_request_full(self):
        """Test creating message request with all parameters."""
        request = A2AMessageRequest(
            content="Hello",
            context_id="ctx-123",
            task_id="task-456",
            metadata={"key": "value"},
            accepted_output_modes=["text", "data"],
        )
        assert request.context_id == "ctx-123"
        assert request.task_id == "task-456"
        assert request.accepted_output_modes == ["text", "data"]


class TestA2AMessageResponse:
    """Tests for A2AMessageResponse dataclass."""

    def test_message_response_defaults(self):
        """Test default values for message response."""
        response = A2AMessageResponse()
        assert response.task is None
        assert response.content is None
        assert response.artifacts == []
        assert response.raw_response is None
        assert response.is_complete is False
        assert response.error is None

    def test_message_response_with_task(self):
        """Test message response with task info."""
        task = A2ATaskInfo(
            task_id="task-123",
            state="completed",
            context_id="ctx-456",
            message="Task done",
        )
        response = A2AMessageResponse(
            task=task,
            content="Result text",
            is_complete=True,
        )
        assert response.task.task_id == "task-123"
        assert response.content == "Result text"
        assert response.is_complete is True


class TestProcessEvent:
    """Tests for _process_event method."""

    def test_process_event_with_text_message(self, a2a_service):
        """Test processing a Message event with text part using real SDK types."""
        from a2a.types import Message, Part, Role, TextPart

        # Create a real Message with a TextPart wrapped in Part (RootModel)
        text_part = Part(root=TextPart(text="Hello from agent", kind="text"))
        message = Message(
            message_id="msg-123",
            role=Role.agent,
            parts=[text_part],
        )

        response = A2AMessageResponse()
        result = a2a_service._process_event(message, response)

        assert result.content == "Hello from agent"
        assert result.raw_response is not None

    def test_process_event_with_data_part(self, a2a_service):
        """Test processing a Message event with data part using real SDK types."""
        from a2a.types import DataPart, Message, Part, Role

        # Create a real Message with a DataPart wrapped in Part (RootModel)
        data_part = Part(root=DataPart(data={"key": "value"}, kind="data"))
        message = Message(
            message_id="msg-124",
            role=Role.agent,
            parts=[data_part],
        )

        response = A2AMessageResponse()
        result = a2a_service._process_event(message, response)

        assert len(result.artifacts) == 1
        assert result.artifacts[0]["type"] == "data"
        assert result.artifacts[0]["data"] == {"key": "value"}

    def test_process_event_with_file_part(self, a2a_service):
        """Test processing a Message event with file part using real SDK types."""
        from a2a.types import FilePart, FileWithUri, Message, Part, Role

        # Create a real Message with a FilePart wrapped in Part (RootModel)
        file = FileWithUri(uri="https://example.com/file.pdf", mime_type="application/pdf")
        file_part = Part(root=FilePart(file=file, kind="file"))
        message = Message(
            message_id="msg-125",
            role=Role.agent,
            parts=[file_part],
        )

        response = A2AMessageResponse()
        result = a2a_service._process_event(message, response)

        assert len(result.artifacts) == 1
        assert result.artifacts[0]["type"] == "file"

    def test_process_event_with_mixed_parts(self, a2a_service):
        """Test processing a Message with multiple part types."""
        from a2a.types import DataPart, Message, Part, Role, TextPart

        text_part = Part(root=TextPart(text="Here is some data:", kind="text"))
        data_part = Part(root=DataPart(data={"result": 42}, kind="data"))

        message = Message(
            message_id="msg-126",
            role=Role.agent,
            parts=[text_part, data_part],
        )

        response = A2AMessageResponse()
        result = a2a_service._process_event(message, response)

        assert result.content == "Here is some data:"
        assert len(result.artifacts) == 1
        assert result.artifacts[0]["data"] == {"result": 42}

    def test_process_event_with_tuple_task(self, a2a_service):
        """Test processing a (Task, UpdateEvent) tuple."""
        from a2a.types import TaskState

        mock_task = MagicMock()
        mock_task.id = "task-123"
        mock_task.context_id = "ctx-456"
        mock_task.status.state = TaskState.completed
        mock_task.status.message = "Done"
        mock_task.artifacts = []

        mock_update = MagicMock()

        response = A2AMessageResponse()
        result = a2a_service._process_event((mock_task, mock_update), response)

        assert result.task is not None
        assert result.task.task_id == "task-123"
        assert result.task.state == TaskState.completed
        assert result.is_complete is True


class TestGetAgentCard:
    """Tests for get_agent_card method."""

    @pytest.mark.asyncio
    async def test_get_agent_card_caching(self, a2a_service, sample_agent_info):
        """Test that agent cards are cached."""
        mock_card = MagicMock()
        mock_card.name = "Test Agent"

        with patch("llm_gateway.a2a.client.A2ACardResolver") as MockResolver:
            mock_resolver = AsyncMock()
            mock_resolver.get_agent_card.return_value = mock_card
            MockResolver.return_value = mock_resolver

            # First call - should fetch
            card1 = await a2a_service.get_agent_card(sample_agent_info)
            assert card1.name == "Test Agent"
            assert mock_resolver.get_agent_card.call_count == 1

            # Second call - should use cache
            card2 = await a2a_service.get_agent_card(sample_agent_info)
            assert card2.name == "Test Agent"
            # Should still be 1 call (cached)
            assert mock_resolver.get_agent_card.call_count == 1

    @pytest.mark.asyncio
    async def test_get_agent_card_force_refresh(self, a2a_service, sample_agent_info):
        """Test force refresh bypasses cache."""
        mock_card = MagicMock()
        mock_card.name = "Test Agent"

        with patch("llm_gateway.a2a.client.A2ACardResolver") as MockResolver:
            mock_resolver = AsyncMock()
            mock_resolver.get_agent_card.return_value = mock_card
            MockResolver.return_value = mock_resolver

            # First call
            await a2a_service.get_agent_card(sample_agent_info)
            # Force refresh
            await a2a_service.get_agent_card(sample_agent_info, force_refresh=True)
            # Should be 2 calls
            assert mock_resolver.get_agent_card.call_count == 2
