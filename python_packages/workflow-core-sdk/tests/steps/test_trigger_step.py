"""
Unit tests for trigger_step

Tests the trigger step that normalizes various trigger types (chat, webhook, etc.)
into a standard structure for workflow execution.
"""

import pytest
from unittest.mock import MagicMock

from workflow_core_sdk.steps.trigger_steps import trigger_step
from workflow_core_sdk.execution_context import ExecutionContext


@pytest.fixture
def execution_context():
    """Create a mock execution context"""
    context = MagicMock(spec=ExecutionContext)
    context.execution_id = "test-execution-id"
    context.workflow_id = "test-workflow-id"
    context.step_io_data = {}
    return context


@pytest.fixture
def step_config():
    """Basic step configuration"""
    return {
        "step_id": "trigger-1",
        "step_type": "trigger",
        "config": {},
    }


class TestChatTrigger:
    """Tests for chat trigger type"""

    @pytest.mark.asyncio
    async def test_chat_trigger_with_current_message(self, step_config, execution_context):
        """Test chat trigger with current message"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "kind": "chat",
                "current_message": "Hello, how are you?",
                "history": [
                    {"role": "user", "content": "Previous message"},
                    {"role": "assistant", "content": "Previous response"},
                ],
                "need_history": True,
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "chat"
        assert result["current_message"] == "Hello, how are you?"
        assert len(result["messages"]) == 3
        assert result["messages"][0] == {"role": "user", "content": "Previous message"}
        assert result["messages"][1] == {"role": "assistant", "content": "Previous response"}
        assert result["messages"][2] == {"role": "user", "content": "Hello, how are you?"}
        assert result["attachments"] == []

    @pytest.mark.asyncio
    async def test_chat_trigger_with_attachments(self, step_config, execution_context):
        """Test chat trigger with file attachments"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "kind": "chat",
                "current_message": "Check this file",
                "attachments": [
                    {
                        "filename": "document.pdf",
                        "mime_type": "application/pdf",
                        "size": 1024,
                        "path": "/tmp/document.pdf",
                    }
                ],
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "chat"
        assert result["current_message"] == "Check this file"
        assert len(result["attachments"]) == 1
        assert result["attachments"][0]["filename"] == "document.pdf"
        assert result["attachments"][0]["mime_type"] == "application/pdf"

    @pytest.mark.asyncio
    async def test_chat_trigger_without_history(self, step_config, execution_context):
        """Test chat trigger with need_history=False"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "kind": "chat",
                "current_message": "New conversation",
                "history": [
                    {"role": "user", "content": "Old message"},
                ],
                "need_history": False,
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "chat"
        assert len(result["messages"]) == 1
        assert result["messages"][0] == {"role": "user", "content": "New conversation"}

    @pytest.mark.asyncio
    async def test_chat_trigger_with_messages_array(self, step_config, execution_context):
        """Test chat trigger with pre-formatted messages array"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "kind": "chat",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                    {"role": "user", "content": "How are you?"},
                ],
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "chat"
        assert len(result["messages"]) == 4
        assert result["messages"][0] == {"role": "system", "content": "You are a helpful assistant"}
        assert result["messages"][3] == {"role": "user", "content": "How are you?"}

    @pytest.mark.asyncio
    async def test_chat_trigger_nested_in_trigger_key(self, step_config, execution_context):
        """Test chat trigger nested under 'trigger' key"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "trigger": {
                    "kind": "chat",
                    "current_message": "Nested message",
                }
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "chat"
        assert result["current_message"] == "Nested message"

    @pytest.mark.asyncio
    async def test_chat_trigger_empty_history(self, step_config, execution_context):
        """Test chat trigger with empty history"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "kind": "chat",
                "current_message": "First message",
                "history": [],
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "chat"
        assert len(result["messages"]) == 1
        assert result["messages"][0] == {"role": "user", "content": "First message"}


class TestWebhookTrigger:
    """Tests for webhook trigger type"""

    @pytest.mark.asyncio
    async def test_webhook_trigger_with_data(self, step_config, execution_context):
        """Test webhook trigger with JSON payload"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "kind": "webhook",
                "data": {
                    "event": "user.created",
                    "user_id": "12345",
                    "email": "user@example.com",
                },
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "webhook"
        assert result["data"]["event"] == "user.created"
        assert result["data"]["user_id"] == "12345"
        assert result["data"]["email"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_webhook_trigger_default_kind(self, step_config, execution_context):
        """Test webhook trigger without explicit kind (defaults to webhook)"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "data": {
                    "message": "Hello from webhook",
                }
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "webhook"
        assert result["data"]["message"] == "Hello from webhook"

    @pytest.mark.asyncio
    async def test_webhook_trigger_passthrough(self, step_config, execution_context):
        """Test webhook trigger with direct payload (no 'data' wrapper)"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "event_type": "payment.completed",
                "amount": 100.50,
                "currency": "USD",
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "webhook"
        assert result["data"]["event_type"] == "payment.completed"
        assert result["data"]["amount"] == 100.50

    @pytest.mark.asyncio
    async def test_webhook_trigger_nested_in_trigger_key(self, step_config, execution_context):
        """Test webhook trigger nested under 'trigger' key"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "trigger": {
                    "kind": "webhook",
                },
                "data": {"status": "active"},
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "webhook"
        assert result["data"]["status"] == "active"


class TestOtherTriggerTypes:
    """Tests for other trigger types"""

    @pytest.mark.asyncio
    async def test_custom_trigger_type(self, step_config, execution_context):
        """Test custom trigger type (e.g., 'scheduled')"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "kind": "scheduled",
                "data": {
                    "schedule": "0 0 * * *",
                    "timezone": "UTC",
                },
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "scheduled"
        assert result["data"]["schedule"] == "0 0 * * *"

    @pytest.mark.asyncio
    async def test_empty_trigger_raw(self, step_config, execution_context):
        """Test with empty trigger_raw (defaults to webhook)"""
        execution_context.step_io_data = {"trigger_raw": {}}

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "webhook"
        assert result["data"] == {}

    @pytest.mark.asyncio
    async def test_missing_trigger_raw(self, step_config, execution_context):
        """Test with missing trigger_raw key"""
        execution_context.step_io_data = {}

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "webhook"
        assert result["data"] == {}


class TestMessageParsing:
    """Tests for message parsing edge cases"""

    @pytest.mark.asyncio
    async def test_invalid_message_format_in_history(self, step_config, execution_context):
        """Test chat trigger with invalid message format in history"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "kind": "chat",
                "current_message": "Hello",
                "history": [
                    {"role": "user", "content": "Valid message"},
                    {"invalid": "message"},  # Missing role/content
                    "not a dict",  # Not even a dict
                ],
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "chat"
        # Only valid messages should be included
        assert len(result["messages"]) == 2
        assert result["messages"][0] == {"role": "user", "content": "Valid message"}
        assert result["messages"][1] == {"role": "user", "content": "Hello"}

    @pytest.mark.asyncio
    async def test_invalid_message_format_in_messages_array(self, step_config, execution_context):
        """Test chat trigger with invalid message format in messages array"""
        execution_context.step_io_data = {
            "trigger_raw": {
                "kind": "chat",
                "messages": [
                    {"role": "user", "content": "Valid"},
                    {"role": "assistant"},  # Missing content
                    None,  # Not a dict
                ],
            }
        }

        result = await trigger_step(step_config, {}, execution_context)

        assert result["kind"] == "chat"
        # Only valid messages should be included
        assert len(result["messages"]) == 1
        assert result["messages"][0] == {"role": "user", "content": "Valid"}
