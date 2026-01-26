"""
Unit tests for data processing steps

Tests data_input_step, data_processing_step, data_merge_step, delay_step, and conditional_step.
"""

import pytest
from unittest.mock import MagicMock

from workflow_core_sdk.steps.data_steps import (
    data_input_step,
    data_processing_step,
    data_merge_step,
    delay_step,
    conditional_step,
)
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
        "step_id": "data-step-1",
        "step_type": "data_input",
        "config": {},
    }


class TestDataInputStep:
    """Tests for data_input_step"""

    @pytest.mark.asyncio
    async def test_static_input(self, step_config, execution_context):
        """Test static data input"""
        step_config["config"] = {
            "input_type": "static",
            "data": {"message": "Hello", "value": 42},
        }

        result = await data_input_step(step_config, {}, execution_context)

        assert result["success"] is True
        assert result["input_type"] == "static"
        assert result["data"]["message"] == "Hello"
        assert result["data"]["value"] == 42
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_static_input_default(self, step_config, execution_context):
        """Test static input with default empty data"""
        step_config["config"] = {"input_type": "static"}

        result = await data_input_step(step_config, {}, execution_context)

        assert result["success"] is True
        assert result["input_type"] == "static"
        assert result["data"] == {}

    @pytest.mark.asyncio
    async def test_dynamic_input_default_source(self, step_config, execution_context):
        """Test dynamic input with default source"""
        step_config["config"] = {"input_type": "dynamic", "source": "api"}

        result = await data_input_step(step_config, {}, execution_context)

        assert result["success"] is True
        assert result["input_type"] == "dynamic"
        assert result["source"] == "api"
        assert "Dynamic data from api" in result["data"]["message"]

    @pytest.mark.asyncio
    async def test_dynamic_input_subflow_source(self, step_config, execution_context):
        """Test dynamic input from subflow"""
        execution_context.step_io_data = {"subflow_input": {"user_id": "123", "action": "create"}}
        step_config["config"] = {"input_type": "dynamic", "source": "subflow_input"}

        result = await data_input_step(step_config, {}, execution_context)

        assert result["success"] is True
        assert result["input_type"] == "dynamic"
        assert result["source"] == "subflow_input"
        assert result["data"]["user_id"] == "123"
        assert result["data"]["action"] == "create"

    @pytest.mark.asyncio
    async def test_invalid_input_type(self, step_config, execution_context):
        """Test with invalid input type"""
        step_config["config"] = {"input_type": "invalid"}

        with pytest.raises(ValueError, match="Unknown input_type"):
            await data_input_step(step_config, {}, execution_context)

    @pytest.mark.asyncio
    async def test_default_input_type(self, step_config, execution_context):
        """Test with no input_type specified (defaults to static)"""
        step_config["config"] = {"data": {"default": "value"}}

        result = await data_input_step(step_config, {}, execution_context)

        assert result["input_type"] == "static"
        assert result["data"]["default"] == "value"


class TestDataProcessingStep:
    """Tests for data_processing_step"""

    @pytest.mark.asyncio
    async def test_identity_processing(self, step_config, execution_context):
        """Test identity processing (pass-through)"""
        step_config["config"] = {"processing_type": "identity"}
        input_data = {"key": "value", "number": 123}

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["processing_type"] == "identity"
        assert result["result"] == input_data

    @pytest.mark.asyncio
    async def test_count_dict(self, step_config, execution_context):
        """Test counting items in a dictionary"""
        step_config["config"] = {"processing_type": "count"}
        input_data = {"a": 1, "b": 2, "c": 3}

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["count"] == 3

    @pytest.mark.asyncio
    async def test_count_list(self, step_config, execution_context):
        """Test counting items in a list"""
        step_config["config"] = {"processing_type": "count"}
        input_data = [1, 2, 3, 4, 5]

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["count"] == 5

    @pytest.mark.asyncio
    async def test_count_string(self, step_config, execution_context):
        """Test counting characters and words in a string"""
        step_config["config"] = {"processing_type": "count"}
        input_data = "Hello world from test"

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["count"] == 21  # character count
        assert result["result"]["word_count"] == 4

    @pytest.mark.asyncio
    async def test_filter_dict(self, step_config, execution_context):
        """Test filtering dictionary by key"""
        step_config["config"] = {
            "processing_type": "filter",
            "options": {"filter_key": "name"},
        }
        input_data = {"name": "John", "age": 30, "city": "NYC"}

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"] == {"name": "John"}

    @pytest.mark.asyncio
    async def test_filter_list(self, step_config, execution_context):
        """Test filtering list by key-value"""
        step_config["config"] = {
            "processing_type": "filter",
            "options": {"filter_key": "status", "filter_value": "active"},
        }
        input_data = [
            {"id": 1, "status": "active"},
            {"id": 2, "status": "inactive"},
            {"id": 3, "status": "active"},
        ]

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert len(result["result"]) == 2
        assert all(item["status"] == "active" for item in result["result"])

    @pytest.mark.asyncio
    async def test_sentiment_positive(self, step_config, execution_context):
        """Test sentiment analysis with positive text"""
        step_config["config"] = {"processing_type": "sentiment_analysis"}
        input_data = "This is a great and excellent product! Amazing quality!"

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["sentiment"] == "positive"
        assert result["result"]["positive_indicators"] > 0

    @pytest.mark.asyncio
    async def test_sentiment_negative(self, step_config, execution_context):
        """Test sentiment analysis with negative text"""
        step_config["config"] = {"processing_type": "sentiment_analysis"}
        input_data = "This is terrible and awful. Very disappointing."

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["sentiment"] == "negative"
        assert result["result"]["negative_indicators"] > 0

    @pytest.mark.asyncio
    async def test_sentiment_neutral(self, step_config, execution_context):
        """Test sentiment analysis with neutral text"""
        step_config["config"] = {"processing_type": "sentiment_analysis"}
        input_data = "The product arrived on time."

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["sentiment"] == "neutral"

    @pytest.mark.asyncio
    async def test_transform_uppercase(self, step_config, execution_context):
        """Test uppercase transformation"""
        step_config["config"] = {
            "processing_type": "transform",
            "options": {"transformation": "uppercase"},
        }
        input_data = {"name": "john", "city": "nyc"}

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["name"] == "JOHN"
        assert result["result"]["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_transform_lowercase(self, step_config, execution_context):
        """Test lowercase transformation"""
        step_config["config"] = {
            "processing_type": "transform",
            "options": {"transformation": "lowercase"},
        }
        input_data = {"name": "JOHN", "city": "NYC"}

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["name"] == "john"
        assert result["result"]["city"] == "nyc"

    @pytest.mark.asyncio
    async def test_processing_with_metadata(self, step_config, execution_context):
        """Test processing with metadata addition"""
        step_config["config"] = {
            "processing_type": "identity",
            "options": {"metadata": {"processed_by": "test", "version": "1.0"}},
        }
        input_data = {"data": "value"}

        result = await data_processing_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["data"] == "value"
        assert result["result"]["processed_by"] == "test"
        assert result["result"]["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_invalid_processing_type(self, step_config, execution_context):
        """Test with invalid processing type"""
        step_config["config"] = {"processing_type": "invalid"}

        with pytest.raises(ValueError, match="Unknown processing_type"):
            await data_processing_step(step_config, {}, execution_context)


class TestDataMergeStep:
    """Tests for data_merge_step"""

    @pytest.mark.asyncio
    async def test_merge_combine_strategy(self, step_config, execution_context):
        """Test merging data with combine strategy"""
        step_config["config"] = {"merge_strategy": "combine"}
        input_data = {
            "data_sources": {
                "source1": {"name": "John", "age": 30},
                "source2": {"city": "NYC", "country": "USA"},
            }
        }

        result = await data_merge_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["name"] == "John"
        assert result["result"]["age"] == 30
        assert result["result"]["city"] == "NYC"
        assert result["result"]["country"] == "USA"

    @pytest.mark.asyncio
    async def test_merge_override_strategy(self, step_config, execution_context):
        """Test merging data with override strategy"""
        step_config["config"] = {"merge_strategy": "override"}
        input_data = {
            "data_sources": {
                "source1": {"name": "John", "age": 30},
                "source2": {"name": "Jane", "city": "NYC"},
            }
        }

        result = await data_merge_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["name"] == "Jane"  # Overridden by source2
        assert result["result"]["age"] == 30
        assert result["result"]["city"] == "NYC"

    @pytest.mark.asyncio
    async def test_merge_list_strategy(self, step_config, execution_context):
        """Test merging data as a list"""
        step_config["config"] = {"merge_strategy": "list"}
        input_data = {
            "data_sources": {
                "source1": {"name": "John"},
                "source2": {"name": "Jane"},
                "source3": {"name": "Bob"},
            }
        }

        result = await data_merge_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert "merged_data" in result["result"]
        assert len(result["result"]["merged_data"]) == 3

    @pytest.mark.asyncio
    async def test_merge_from_execution_context(self, step_config, execution_context):
        """Test merging data from execution context when no data_sources provided"""
        step_config["config"] = {"merge_strategy": "combine"}
        execution_context.step_io_data = {
            "step1": {"value": 1},
            "step2": {"value": 2},
        }
        input_data = {}

        result = await data_merge_step(step_config, input_data, execution_context)

        assert result["success"] is True
        # Should merge from execution context
        assert "step1" in result["result"] or "value" in result["result"]

    @pytest.mark.asyncio
    async def test_merge_non_dict_values(self, step_config, execution_context):
        """Test merging with non-dict values"""
        step_config["config"] = {"merge_strategy": "combine"}
        input_data = {
            "data_sources": {
                "source1": "string_value",
                "source2": 123,
                "source3": {"key": "value"},
            }
        }

        result = await data_merge_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["result"]["source1"] == "string_value"
        assert result["result"]["source2"] == 123
        assert result["result"]["key"] == "value"


class TestDelayStep:
    """Tests for delay_step"""

    @pytest.mark.asyncio
    async def test_delay_default(self, step_config, execution_context):
        """Test delay with default 1 second"""
        step_config["config"] = {}

        result = await delay_step(step_config, {"test": "data"}, execution_context)

        assert result["success"] is True
        assert result["delay_requested"] == 1.0
        assert result["delay_actual"] >= 0.9  # Allow some tolerance
        assert result["input_data"]["test"] == "data"

    @pytest.mark.asyncio
    async def test_delay_custom(self, step_config, execution_context):
        """Test delay with custom duration"""
        step_config["config"] = {"delay_seconds": 0.1}

        result = await delay_step(step_config, {}, execution_context)

        assert result["success"] is True
        assert result["delay_requested"] == 0.1
        assert result["delay_actual"] >= 0.09  # Allow some tolerance
        assert "started_at" in result
        assert "completed_at" in result


class TestConditionalStep:
    """Tests for conditional_step"""

    @pytest.mark.asyncio
    async def test_condition_true(self, step_config, execution_context):
        """Test conditional with true condition"""
        step_config["config"] = {
            "condition": "true",
            "true_action": {"type": "pass"},
            "false_action": {"type": "pass"},
        }
        input_data = {"value": 42}

        result = await conditional_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["condition_result"] is True
        assert result["result"]["value"] == 42

    @pytest.mark.asyncio
    async def test_condition_false(self, step_config, execution_context):
        """Test conditional with false condition"""
        step_config["config"] = {
            "condition": "false",
            "true_action": {"type": "pass"},
            "false_action": {"type": "pass"},
        }
        input_data = {"value": 42}

        result = await conditional_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["condition_result"] is False
        assert result["result"]["value"] == 42

    @pytest.mark.asyncio
    async def test_condition_input_field_exists(self, step_config, execution_context):
        """Test conditional checking input field existence"""
        step_config["config"] = {
            "condition": "input.user.name",
            "true_action": {"type": "pass"},
            "false_action": {"type": "pass"},
        }
        input_data = {"user": {"name": "John", "age": 30}}

        result = await conditional_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["condition_result"] is True

    @pytest.mark.asyncio
    async def test_condition_input_field_missing(self, step_config, execution_context):
        """Test conditional with missing input field"""
        step_config["config"] = {
            "condition": "input.user.email",
            "true_action": {"type": "pass"},
            "false_action": {"type": "pass"},
        }
        input_data = {"user": {"name": "John"}}

        result = await conditional_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["condition_result"] is False

    @pytest.mark.asyncio
    async def test_condition_transform_action(self, step_config, execution_context):
        """Test conditional with transform action"""
        step_config["config"] = {
            "condition": "true",
            "true_action": {
                "type": "transform",
                "transformation": {"status": "approved", "processed": True},
            },
            "false_action": {"type": "pass"},
        }
        input_data = {"id": 123}

        result = await conditional_step(step_config, input_data, execution_context)

        assert result["success"] is True
        assert result["condition_result"] is True
        assert result["result"]["id"] == 123
        assert result["result"]["status"] == "approved"
        assert result["result"]["processed"] is True
