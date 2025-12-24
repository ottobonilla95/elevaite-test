"""
Unit tests for input_step

Tests the input node step that provides data entry points for workflows.
Input nodes can be triggered externally (webhook, schedule, gmail, slack) or 
filled manually (chat, manual, form).
"""

import pytest
from unittest.mock import MagicMock

from workflow_core_sdk.steps.input_steps import input_step
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
        "step_id": "input-1",
        "step_type": "input",
        "parameters": {"kind": "manual"},
        "config": {},
    }


class TestInputStepBasics:
    """Tests for basic input node functionality"""

    @pytest.mark.asyncio
    async def test_input_step_with_direct_data(self, step_config, execution_context):
        """Test input step with data provided directly to the step"""
        execution_context.step_io_data = {
            "input-1": {"message": "Hello from input", "value": 42}
        }

        result = await input_step(step_config, {}, execution_context)

        assert result["kind"] == "manual"
        assert result["step_id"] == "input-1"
        assert result["source"] == "direct"
        assert result["data"]["message"] == "Hello from input"
        assert result["data"]["value"] == 42

    @pytest.mark.asyncio
    async def test_input_step_with_trigger_raw_fallback(self, step_config, execution_context):
        """Test input step falls back to trigger_raw for backwards compatibility"""
        execution_context.step_io_data = {
            "trigger_raw": {"kind": "webhook", "data": {"event": "test"}}
        }

        result = await input_step(step_config, {}, execution_context)

        assert result["kind"] == "manual"
        assert result["step_id"] == "input-1"
        assert result["source"] == "trigger_raw"
        assert result["data"]["kind"] == "webhook"

    @pytest.mark.asyncio
    async def test_input_step_no_data_available(self, step_config, execution_context):
        """Test input step when no data is available"""
        execution_context.step_io_data = {}

        result = await input_step(step_config, {}, execution_context)

        assert result["kind"] == "manual"
        assert result["step_id"] == "input-1"
        assert result["source"] == "none"
        assert result["awaiting_input"] is True
        assert result["data"] == {}


class TestInputStepKinds:
    """Tests for different input kinds"""

    @pytest.mark.asyncio
    async def test_webhook_input_kind(self, execution_context):
        """Test webhook input kind"""
        step_config = {
            "step_id": "webhook-input",
            "step_type": "input",
            "parameters": {"kind": "webhook"},
        }
        execution_context.step_io_data = {
            "webhook-input": {"event": "user.created", "user_id": "123"}
        }

        result = await input_step(step_config, {}, execution_context)

        assert result["kind"] == "webhook"
        assert result["data"]["event"] == "user.created"

    @pytest.mark.asyncio
    async def test_chat_input_kind(self, execution_context):
        """Test chat input kind"""
        step_config = {
            "step_id": "chat-input",
            "step_type": "input",
            "parameters": {"kind": "chat"},
        }
        execution_context.step_io_data = {
            "chat-input": {"message": "Hello!", "history": []}
        }

        result = await input_step(step_config, {}, execution_context)

        assert result["kind"] == "chat"
        assert result["data"]["message"] == "Hello!"

    @pytest.mark.asyncio
    async def test_gmail_input_kind(self, execution_context):
        """Test gmail input kind"""
        step_config = {
            "step_id": "gmail-input",
            "step_type": "input",
            "parameters": {"kind": "gmail"},
        }
        execution_context.step_io_data = {
            "gmail-input": {"from": "user@example.com", "subject": "Test", "body": "Hello"}
        }

        result = await input_step(step_config, {}, execution_context)

        assert result["kind"] == "gmail"
        assert result["data"]["from"] == "user@example.com"

    @pytest.mark.asyncio
    async def test_slack_input_kind(self, execution_context):
        """Test slack input kind"""
        step_config = {
            "step_id": "slack-input",
            "step_type": "input",
            "parameters": {"kind": "slack"},
        }
        execution_context.step_io_data = {
            "slack-input": {"channel": "#general", "text": "Hello team"}
        }

        result = await input_step(step_config, {}, execution_context)

        assert result["kind"] == "slack"
        assert result["data"]["channel"] == "#general"

