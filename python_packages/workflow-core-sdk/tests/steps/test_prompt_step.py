"""
Unit tests for prompt_step.

Tests the Prompt node step that provides prompt configuration for connected
Agent steps, including variable resolution and template injection.
"""

import pytest
from unittest.mock import MagicMock

from workflow_core_sdk.steps.prompt_steps import prompt_step, _resolve_variable_sources


@pytest.fixture
def execution_context():
    """Create a mock execution context."""
    context = MagicMock()
    context.execution_id = "test-execution-id"
    context.workflow_id = "test-workflow-id"
    context.step_io_data = {}
    return context


class TestResolveVariableSources:
    """Tests for _resolve_variable_sources helper function."""

    def test_resolve_from_input_data(self, execution_context):
        """Test resolving variable from input_data source."""
        variables = [{"name": "user_name", "source": "name", "default_value": "default"}]
        input_data = {"name": "Alice"}

        result = _resolve_variable_sources(variables, execution_context, input_data)

        assert result["user_name"] == "Alice"

    def test_resolve_from_step_output(self, execution_context):
        """Test resolving variable from step output using dot notation."""
        execution_context.step_io_data = {"data_step": {"user": "Bob", "age": 30}}
        variables = [{"name": "customer", "source": "data_step.user"}]

        result = _resolve_variable_sources(variables, execution_context, {})

        assert result["customer"] == "Bob"

    def test_fallback_to_default(self, execution_context):
        """Test falling back to default when source not found."""
        variables = [{"name": "greeting", "source": "nonexistent", "default_value": "Hello"}]

        result = _resolve_variable_sources(variables, execution_context, {})

        assert result["greeting"] == "Hello"

    def test_skip_variable_without_name(self, execution_context):
        """Test that variables without names are skipped."""
        variables = [
            {"source": "name", "default_value": "default"},
            {"name": "valid", "source": "name", "default_value": "default"},
        ]
        input_data = {"name": "Alice"}

        result = _resolve_variable_sources(variables, execution_context, input_data)

        assert "valid" in result
        assert len(result) == 1


class TestPromptStep:
    """Tests for prompt_step function."""

    @pytest.mark.asyncio
    async def test_basic_prompt_output(self, execution_context):
        """Test basic prompt step output structure."""
        step_config = {
            "step_id": "prompt-1",
            "step_type": "prompt",
            "parameters": {
                "system_prompt": "You are a helpful assistant.",
                "query_template": "Help with {{task}}",
            },
        }
        input_data = {"task": "coding"}

        result = await prompt_step(step_config, input_data, execution_context)

        assert result["step_type"] == "prompt"
        assert result["step_id"] == "prompt-1"
        assert result["system_prompt"] == "You are a helpful assistant."
        assert result["query_template"] == "Help with coding"
        assert result["raw_system_prompt"] == "You are a helpful assistant."
        assert result["raw_query_template"] == "Help with {{task}}"

    @pytest.mark.asyncio
    async def test_variable_injection(self, execution_context):
        """Test that variables are injected into templates."""
        step_config = {
            "step_id": "prompt-1",
            "parameters": {
                "system_prompt": "Hello {{name}}, you are {{role}}.",
                "variables": [{"name": "name", "source": "user_name"}, {"name": "role", "default_value": "a tester"}],
            },
        }
        input_data = {"user_name": "Alice"}

        result = await prompt_step(step_config, input_data, execution_context)

        assert result["system_prompt"] == "Hello Alice, you are a tester."
        assert result["variables"]["name"] == "Alice"
        assert result["variables"]["role"] == "a tester"

    @pytest.mark.asyncio
    async def test_builtin_variable_injection(self, execution_context):
        """Test that built-in variables are injected."""
        step_config = {
            "step_id": "prompt-1",
            "parameters": {
                "system_prompt": "Current year: {{current_year}}",
            },
        }

        result = await prompt_step(step_config, {}, execution_context)

        from datetime import datetime

        assert result["system_prompt"] == f"Current year: {datetime.now().year}"

    @pytest.mark.asyncio
    async def test_model_overrides(self, execution_context):
        """Test that model overrides are extracted."""
        step_config = {
            "step_id": "prompt-1",
            "parameters": {"system_prompt": "Test", "model_name": "gpt-4", "temperature": 0.7, "max_tokens": 2000},
        }

        result = await prompt_step(step_config, {}, execution_context)

        assert result["model_overrides"]["model_name"] == "gpt-4"
        assert result["model_overrides"]["temperature"] == 0.7
        assert result["model_overrides"]["max_tokens"] == 2000

    @pytest.mark.asyncio
    async def test_override_agent_prompt_default(self, execution_context):
        """Test that override_agent_prompt defaults to True."""
        step_config = {
            "step_id": "prompt-1",
            "parameters": {
                "system_prompt": "Test",
            },
        }

        result = await prompt_step(step_config, {}, execution_context)

        assert result["override_agent_prompt"] is True

    @pytest.mark.asyncio
    async def test_override_agent_prompt_false(self, execution_context):
        """Test setting override_agent_prompt to False."""
        step_config = {"step_id": "prompt-1", "parameters": {"system_prompt": "Test", "override_agent_prompt": False}}

        result = await prompt_step(step_config, {}, execution_context)

        assert result["override_agent_prompt"] is False

    @pytest.mark.asyncio
    async def test_step_data_variable_resolution(self, execution_context):
        """Test resolving variables from previous step output."""
        execution_context.step_io_data = {"input-step": {"user_query": "Help me debug", "priority": "high"}}
        step_config = {
            "step_id": "prompt-1",
            "parameters": {
                "query_template": "Task: {{query}} (Priority: {{priority}})",
                "variables": [
                    {"name": "query", "source": "input-step.user_query"},
                    {"name": "priority", "source": "input-step.priority"},
                ],
            },
        }

        result = await prompt_step(step_config, {}, execution_context)

        assert result["query_template"] == "Task: Help me debug (Priority: high)"

    @pytest.mark.asyncio
    async def test_preserve_unresolved_variables(self, execution_context):
        """Test that unresolved variables are preserved in output."""
        step_config = {
            "step_id": "prompt-1",
            "parameters": {
                "system_prompt": "Hello {{unknown_var}}",
            },
        }

        result = await prompt_step(step_config, {}, execution_context)

        # Unresolved variables should be preserved for agent to handle
        assert result["system_prompt"] == "Hello {{unknown_var}}"

    @pytest.mark.asyncio
    async def test_empty_parameters(self, execution_context):
        """Test prompt step with empty parameters."""
        step_config = {"step_id": "prompt-1", "parameters": {}}

        result = await prompt_step(step_config, {}, execution_context)

        assert result["system_prompt"] is None
        assert result["query_template"] is None
        assert result["variables"] == {}
        assert result["model_overrides"] == {}

    @pytest.mark.asyncio
    async def test_config_fallback(self, execution_context):
        """Test that 'config' is used as fallback if 'parameters' not present."""
        step_config = {
            "step_id": "prompt-1",
            "config": {
                "system_prompt": "Config-based prompt",
            },
        }

        result = await prompt_step(step_config, {}, execution_context)

        assert result["system_prompt"] == "Config-based prompt"

    @pytest.mark.asyncio
    async def test_auto_variable_from_input_data(self, execution_context):
        """Test that variables in template are auto-resolved from input_data."""
        step_config = {
            "step_id": "prompt-1",
            "parameters": {
                "system_prompt": "User: {{user_name}}, Task: {{task_type}}",
            },
        }
        input_data = {"user_name": "Bob", "task_type": "debugging"}

        result = await prompt_step(step_config, input_data, execution_context)

        # Variables should be resolved even without explicit variable definitions
        assert result["system_prompt"] == "User: Bob, Task: debugging"
        assert "user_name" in result["variables"]
        assert "task_type" in result["variables"]
