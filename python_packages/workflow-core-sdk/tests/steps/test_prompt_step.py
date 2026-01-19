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


class TestRealisticScenarios:
    """Integration-style tests simulating realistic workflow scenarios."""

    @pytest.mark.asyncio
    async def test_customer_support_prompt_scenario(self, execution_context):
        """
        Realistic scenario: Customer support agent prompt configuration.

        Simulates a workflow where:
        1. An input step captures customer info
        2. A prompt step configures the agent with customer context
        """
        # Simulate data from previous input step
        execution_context.step_io_data = {
            "customer-input": {
                "customer_name": "Jane Smith",
                "ticket_id": "TICKET-12345",
                "issue_category": "billing",
                "previous_interactions": 3,
            }
        }
        execution_context.user_name = "Support Agent John"

        step_config = {
            "step_id": "support-prompt",
            "step_type": "prompt",
            "parameters": {
                "system_prompt": """You are a customer support agent helping {{customer_name}}.
Ticket ID: {{ticket_id}}
Issue Category: {{issue_category}}
Previous Interactions: {{interactions}}
Current Date: {{current_date}}
Agent: {{user_name}}

Be professional and helpful. Reference the ticket ID when appropriate.""",
                "query_template": "Customer {{customer_name}} says: {{customer_message}}",
                "variables": [
                    {"name": "customer_name", "source": "customer-input.customer_name"},
                    {"name": "ticket_id", "source": "customer-input.ticket_id"},
                    {"name": "issue_category", "source": "customer-input.issue_category"},
                    {"name": "interactions", "source": "customer-input.previous_interactions"},
                ],
                "model_name": "gpt-4",
                "temperature": 0.3,  # Lower temp for support consistency
            },
        }
        input_data = {"customer_message": "I was charged twice for my subscription"}

        result = await prompt_step(step_config, input_data, execution_context)

        # Verify customer info is injected
        assert "Jane Smith" in result["system_prompt"]
        assert "TICKET-12345" in result["system_prompt"]
        assert "billing" in result["system_prompt"]
        assert "3" in result["system_prompt"]

        # Verify user_name from context is injected
        assert "Support Agent John" in result["system_prompt"]

        # Verify current_date built-in is injected (should be a date string)
        from datetime import datetime

        assert datetime.now().strftime("%Y") in result["system_prompt"]

        # Verify query template
        assert "Jane Smith" in result["query_template"]
        assert "charged twice" in result["query_template"]

        # Verify model overrides
        assert result["model_overrides"]["model_name"] == "gpt-4"
        assert result["model_overrides"]["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_code_review_prompt_scenario(self, execution_context):
        """
        Realistic scenario: Code review agent prompt configuration.

        Simulates a workflow where:
        1. A file processing step extracts code
        2. A prompt step configures the code review agent
        """
        execution_context.step_io_data = {
            "code-extractor": {
                "filename": "user_service.py",
                "language": "python",
                "line_count": 150,
                "code_snippet": "def get_user(id):\n    return db.query(User).get(id)",
            }
        }
        execution_context.execution_id = "review-exec-001"

        step_config = {
            "step_id": "review-prompt",
            "step_type": "prompt",
            "parameters": {
                "system_prompt": """You are a senior code reviewer.
Review ID: {{execution_id}}
File: {{filename}}
Language: {{language}}
Lines: {{line_count}}

Focus on:
1. Security vulnerabilities
2. Performance issues
3. Code style and best practices
4. Potential bugs""",
                "query_template": "Please review this code:\n```{{language}}\n{{code}}\n```",
                "variables": [
                    {"name": "filename", "source": "code-extractor.filename"},
                    {"name": "language", "source": "code-extractor.language"},
                    {"name": "line_count", "source": "code-extractor.line_count"},
                    {"name": "code", "source": "code-extractor.code_snippet"},
                ],
                "model_name": "claude-3-opus",
                "max_tokens": 4000,
            },
        }

        result = await prompt_step(step_config, {}, execution_context)

        # Verify file info is injected
        assert "user_service.py" in result["system_prompt"]
        assert "python" in result["system_prompt"]
        assert "150" in result["system_prompt"]
        assert "review-exec-001" in result["system_prompt"]

        # Verify code is in query template
        assert "def get_user" in result["query_template"]
        assert "```python" in result["query_template"]

        # Verify model overrides
        assert result["model_overrides"]["model_name"] == "claude-3-opus"
        assert result["model_overrides"]["max_tokens"] == 4000

    @pytest.mark.asyncio
    async def test_multi_step_chain_scenario(self, execution_context):
        """
        Realistic scenario: Multi-step workflow data chain.

        Simulates a workflow with multiple preceding steps where
        the prompt step combines data from multiple sources.
        """
        execution_context.step_io_data = {
            "data-collector": {
                "company": "Acme Corp",
                "industry": "Technology",
            },
            "research-step": {
                "recent_news": "Acme Corp announced Q4 earnings",
                "stock_price": "$125.50",
            },
            "sentiment-analyzer": {
                "overall_sentiment": "positive",
                "confidence": 0.85,
            },
        }
        execution_context.workflow_id = "market-analysis-wf"

        step_config = {
            "step_id": "analyst-prompt",
            "step_type": "prompt",
            "parameters": {
                "system_prompt": """You are a market analyst.
Workflow: {{workflow_id}}
Analysis Time: {{current_time}}

Company Profile:
- Name: {{company}}
- Industry: {{industry}}

Recent News: {{news}}
Current Stock: {{stock}}

Market Sentiment: {{sentiment}} (Confidence: {{confidence}})

Provide insights based on this information.""",
                "query_template": "What is your analysis of {{company}} given the recent developments?",
                "variables": [
                    {"name": "company", "source": "data-collector.company"},
                    {"name": "industry", "source": "data-collector.industry"},
                    {"name": "news", "source": "research-step.recent_news"},
                    {"name": "stock", "source": "research-step.stock_price"},
                    {"name": "sentiment", "source": "sentiment-analyzer.overall_sentiment"},
                    {"name": "confidence", "source": "sentiment-analyzer.confidence"},
                ],
                "temperature": 0.5,
            },
        }

        result = await prompt_step(step_config, {}, execution_context)

        # Verify data from all three steps is combined
        assert "Acme Corp" in result["system_prompt"]
        assert "Technology" in result["system_prompt"]
        assert "Q4 earnings" in result["system_prompt"]
        assert "$125.50" in result["system_prompt"]
        assert "positive" in result["system_prompt"]
        assert "0.85" in result["system_prompt"]
        assert "market-analysis-wf" in result["system_prompt"]

        # Verify query template
        assert "Acme Corp" in result["query_template"]

    @pytest.mark.asyncio
    async def test_dynamic_prompt_with_user_preferences(self, execution_context):
        """
        Realistic scenario: Dynamic prompt based on user preferences.

        Simulates personalized agent behavior based on user settings.
        """
        execution_context.step_io_data = {
            "user-preferences": {
                "response_style": "concise",
                "expertise_level": "expert",
                "language": "English",
            }
        }
        execution_context.user_id = "user-abc-123"
        execution_context.user_name = "Dr. Sarah Chen"
        execution_context.session_id = "session-xyz-789"

        step_config = {
            "step_id": "personalized-prompt",
            "step_type": "prompt",
            "parameters": {
                "system_prompt": """Session: {{session_id}}
User: {{user_name}} ({{user_id}})

Preferences:
- Style: {{style}}
- Expertise: {{level}}
- Language: {{lang}}

Adjust your responses according to user preferences.""",
                "variables": [
                    {"name": "style", "source": "user-preferences.response_style"},
                    {"name": "level", "source": "user-preferences.expertise_level"},
                    {"name": "lang", "source": "user-preferences.language"},
                ],
            },
        }

        result = await prompt_step(step_config, {}, execution_context)

        # Verify context variables are injected
        assert "Dr. Sarah Chen" in result["system_prompt"]
        assert "user-abc-123" in result["system_prompt"]
        assert "session-xyz-789" in result["system_prompt"]

        # Verify preferences from step data
        assert "concise" in result["system_prompt"]
        assert "expert" in result["system_prompt"]
        assert "English" in result["system_prompt"]

    @pytest.mark.asyncio
    async def test_fallback_to_defaults_scenario(self, execution_context):
        """
        Realistic scenario: Graceful fallback when some data is missing.

        Simulates a workflow where not all expected data is available,
        and the prompt should use sensible defaults.
        """
        # Only partial data available
        execution_context.step_io_data = {
            "partial-data": {
                "name": "Quick Task",
                # priority and deadline are missing
            }
        }

        step_config = {
            "step_id": "fallback-prompt",
            "step_type": "prompt",
            "parameters": {
                "system_prompt": """Task: {{task_name}}
Priority: {{priority}}
Deadline: {{deadline}}

Process this task appropriately.""",
                "variables": [
                    {"name": "task_name", "source": "partial-data.name"},
                    {"name": "priority", "source": "partial-data.priority", "default_value": "medium"},
                    {"name": "deadline", "source": "partial-data.deadline", "default_value": "not specified"},
                ],
            },
        }

        result = await prompt_step(step_config, {}, execution_context)

        # Verify available data is used
        assert "Quick Task" in result["system_prompt"]

        # Verify defaults are applied for missing data
        assert "medium" in result["system_prompt"]
        assert "not specified" in result["system_prompt"]

        # Verify the variables dict has the resolved values
        assert result["variables"]["task_name"] == "Quick Task"
        assert result["variables"]["priority"] == "medium"
        assert result["variables"]["deadline"] == "not specified"


class TestDemoWorkflows:
    """Demo workflow tests - these simulate real workflows for product demos."""

    @pytest.mark.asyncio
    async def test_ad_copy_transformer_full_workflow(self, execution_context):
        """
        Demo Workflow 1: Ad Copy Transformer (Full Workflow)

        Theme: Simple text transformation with Prompt Node

        Flow:
            Input Node ──┐
                         ├──► Agent Node ──► Output Node
            Prompt Node ─┘

        This workflow takes raw product specs, configures an agent with a
        prompt to transform them, and outputs compelling ad copy.
        """
        # ============================================================
        # STEP 1: Input Node
        # User provides raw product specifications
        # ============================================================
        input_node_output = {"raw_copy": "Arlo Pro 5 camera 2K video color night vision weather resistant"}

        # Store input node output in execution context
        execution_context.step_io_data = {"input-node": input_node_output}

        # ============================================================
        # STEP 2: Prompt Node
        # Configures the agent with system prompt, query template, and model settings
        # ============================================================
        prompt_node_config = {
            "step_id": "prompt-node",
            "step_type": "prompt",
            "parameters": {
                "system_prompt": "You are an expert advertising copywriter specializing in home security products. Create compelling, concise ad copy.",
                "query_template": "Transform this product spec list into a compelling ad copy that emphasizes peace of mind and home security. Keep it under 100 characters for social media ads.\n\nProduct specs: {{raw_copy}}",
                "variables": [{"name": "raw_copy", "source": "input-node.raw_copy"}],
                "model_name": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 150,
            },
        }

        prompt_node_output = await prompt_step(prompt_node_config, {}, execution_context)

        # Verify prompt node processed correctly
        assert prompt_node_output["step_type"] == "prompt"
        assert "Arlo Pro 5" in prompt_node_output["query_template"]
        assert prompt_node_output["model_overrides"]["model_name"] == "gpt-4"

        # Store prompt node output in execution context
        execution_context.step_io_data["prompt-node"] = prompt_node_output

        # ============================================================
        # STEP 3: Agent Node
        # Receives configuration from Prompt Node and data from Input Node
        # (Simulated - in real execution, this calls the LLM)
        # ============================================================
        agent_node_config = {
            "step_id": "agent-node",
            "step_type": "agent_execution",
            "dependencies": ["input-node", "prompt-node"],
            "config": {
                "agent_name": "AdCopyWriter",
            },
        }

        # Simulate what the agent execution step would receive
        # It gets the prompt configuration from the connected prompt node
        prompt_config = None
        for dep_id in agent_node_config.get("dependencies", []):
            dep_output = execution_context.step_io_data.get(dep_id, {})
            if isinstance(dep_output, dict) and dep_output.get("step_type") == "prompt":
                prompt_config = dep_output
                break

        assert prompt_config is not None, "Agent should receive prompt config from prompt node"
        assert (
            prompt_config["system_prompt"]
            == "You are an expert advertising copywriter specializing in home security products. Create compelling, concise ad copy."
        )
        assert "Arlo Pro 5" in prompt_config["query_template"]
        model_overrides = prompt_config["model_overrides"]
        assert model_overrides["model_name"] == "gpt-4"
        assert model_overrides["temperature"] == 0.7

        # Simulate agent execution result
        # In real execution, this would be the LLM response
        agent_node_output = {
            "success": True,
            "response": "See every detail, day or night. Arlo Pro 5: 2K clarity + color night vision. Your home, always protected.",
            "agent_name": "AdCopyWriter",
            "model": "gpt-4",
            "execution_time_seconds": 1.2,
        }

        # Store agent output
        execution_context.step_io_data["agent-node"] = agent_node_output

        # ============================================================
        # STEP 4: Output Node
        # Receives the final ad copy from the Agent Node
        # In a real workflow, output node config would be:
        # {"step_id": "output-node", "dependencies": ["agent-node"],
        #  "config": {"output_mapping": {"ad_copy": "agent-node.response"}}}
        # ============================================================
        # Simulate output node extracting the response
        final_output = {"ad_copy": execution_context.step_io_data["agent-node"]["response"]}

        # ============================================================
        # FINAL VERIFICATION
        # ============================================================
        assert (
            final_output["ad_copy"]
            == "See every detail, day or night. Arlo Pro 5: 2K clarity + color night vision. Your home, always protected."
        )
        assert len(final_output["ad_copy"]) < 120  # Should be concise for social media

        # Verify the full workflow state
        assert "input-node" in execution_context.step_io_data
        assert "prompt-node" in execution_context.step_io_data
        assert "agent-node" in execution_context.step_io_data
        assert execution_context.step_io_data["agent-node"]["success"] is True
