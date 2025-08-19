"""
Built-in Step Functions

Basic step implementations for common workflow operations.
These provide the foundation for workflow execution.
"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
import logging

from .execution_context import ExecutionContext


logger = logging.getLogger(__name__)


async def data_input_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Data input step that provides static or dynamic input data.

    Config options:
    - input_type: "static" or "dynamic"
    - data: The data to provide (for static)
    - source: Source for dynamic data
    """

    config = step_config.get("config", {})
    input_type = config.get("input_type", "static")

    if input_type == "static":
        # Return static data
        data = config.get("data", {})
        return {
            "data": data,
            "input_type": "static",
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }

    elif input_type == "dynamic":
        # For PoC, simulate dynamic data
        source = config.get("source", "default")

        # Simulate different data sources
        if source == "file":
            data = {
                "content": "Sample file content for PoC",
                "metadata": {"file_size": 1024, "format": "txt"},
            }
        elif source == "api":
            data = {"api_response": "Sample API response for PoC", "status_code": 200}
        else:
            data = {
                "message": f"Dynamic data from {source}",
                "timestamp": datetime.now().isoformat(),
            }

        return {
            "data": data,
            "input_type": "dynamic",
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }

    else:
        raise ValueError(f"Unknown input_type: {input_type}")


async def data_processing_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Data processing step that transforms input data.

    Config options:
    - processing_type: Type of processing to perform
    - options: Processing-specific options
    """

    config = step_config.get("config", {})
    processing_type = config.get("processing_type", "passthrough")
    options = config.get("options", {})

    # Get the data to process
    data_to_process = input_data

    if processing_type == "passthrough":
        # Just pass data through unchanged
        result = data_to_process

    elif processing_type == "uppercase":
        # Convert text data to uppercase
        result = {}
        for key, value in data_to_process.items():
            if isinstance(value, str):
                result[key] = value.upper()
            else:
                result[key] = value

    elif processing_type == "word_count":
        # Count words in text data
        text = ""
        if "text" in data_to_process:
            text = data_to_process["text"]
        elif "content" in data_to_process:
            text = data_to_process["content"]
        elif "data" in data_to_process and isinstance(data_to_process["data"], str):
            text = data_to_process["data"]

        word_count = len(text.split()) if text else 0

        result = {
            "word_count": word_count,
            "character_count": len(text),
            "text_length": len(text),
            "original_data": data_to_process,
        }

    elif processing_type == "sentiment_analysis":
        # Simulate sentiment analysis
        text = ""
        if "text" in data_to_process:
            text = data_to_process["text"]
        elif "content" in data_to_process:
            text = data_to_process["content"]

        # Simple sentiment simulation
        positive_words = ["good", "great", "excellent", "amazing", "wonderful"]
        negative_words = ["bad", "terrible", "awful", "horrible", "disappointing"]

        text_lower = text.lower() if text else ""
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            sentiment = "positive"
            score = 0.7
        elif negative_count > positive_count:
            sentiment = "negative"
            score = -0.7
        else:
            sentiment = "neutral"
            score = 0.0

        result = {
            "sentiment": sentiment,
            "score": score,
            "positive_indicators": positive_count,
            "negative_indicators": negative_count,
            "original_data": data_to_process,
        }

    elif processing_type == "transform":
        # Generic transformation based on options
        transformation = options.get("transformation", "identity")

        if transformation == "identity":
            result = data_to_process
        elif transformation == "uppercase":
            result = {
                k: v.upper() if isinstance(v, str) else v
                for k, v in data_to_process.items()
            }
        elif transformation == "lowercase":
            result = {
                k: v.lower() if isinstance(v, str) else v
                for k, v in data_to_process.items()
            }
        else:
            result = data_to_process

    else:
        raise ValueError(f"Unknown processing_type: {processing_type}")

    return {
        "result": result,
        "processing_type": processing_type,
        "processed_at": datetime.now().isoformat(),
        "success": True,
    }


async def data_merge_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Data merge step that combines data from multiple sources.

    Config options:
    - merge_strategy: How to merge the data
    - keys: Specific keys to merge (optional)
    """

    config = step_config.get("config", {})
    merge_strategy = config.get("merge_strategy", "combine")
    keys = config.get("keys", None)

    if merge_strategy == "combine":
        # Combine all input data into a single object
        merged_data = {}

        if keys:
            # Only merge specified keys
            for key in keys:
                if key in input_data:
                    merged_data[key] = input_data[key]
        else:
            # Merge all data
            merged_data = input_data.copy()

        result = {
            "merged_data": merged_data,
            "merge_strategy": merge_strategy,
            "keys_merged": list(merged_data.keys()),
            "total_keys": len(merged_data),
        }

    elif merge_strategy == "concatenate":
        # Concatenate string values
        concatenated = ""
        for key, value in input_data.items():
            if isinstance(value, str):
                concatenated += value + " "

        result = {
            "concatenated_text": concatenated.strip(),
            "merge_strategy": merge_strategy,
            "source_keys": list(input_data.keys()),
        }

    elif merge_strategy == "sum":
        # Sum numeric values
        total = 0
        numeric_keys = []

        for key, value in input_data.items():
            if isinstance(value, (int, float)):
                total += value
                numeric_keys.append(key)

        result = {
            "sum": total,
            "merge_strategy": merge_strategy,
            "numeric_keys": numeric_keys,
            "count": len(numeric_keys),
        }

    else:
        raise ValueError(f"Unknown merge_strategy: {merge_strategy}")

    return {"result": result, "merged_at": datetime.now().isoformat(), "success": True}


async def delay_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Delay step that waits for a specified amount of time.
    Useful for testing and workflow timing.
    """

    config = step_config.get("config", {})
    delay_seconds = config.get("delay_seconds", 1.0)

    start_time = datetime.now()
    await asyncio.sleep(delay_seconds)
    end_time = datetime.now()

    actual_delay = (end_time - start_time).total_seconds()

    return {
        "delay_requested": delay_seconds,
        "delay_actual": actual_delay,
        "started_at": start_time.isoformat(),
        "completed_at": end_time.isoformat(),
        "input_data": input_data,
        "success": True,
    }


async def conditional_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Conditional step that executes different logic based on conditions.

    Config options:
    - condition: The condition to evaluate
    - condition_type: Type of condition ("equals", "contains", "greater_than", etc.)
    - true_result: Result to return if condition is true
    - false_result: Result to return if condition is false
    """

    config = step_config.get("config", {})
    condition_type = config.get("condition_type", "equals")
    condition_value = config.get("condition_value")
    condition_key = config.get("condition_key", "value")
    true_result = config.get("true_result", {"condition_met": True})
    false_result = config.get("false_result", {"condition_met": False})

    # Get the value to test
    test_value = input_data.get(condition_key)

    # Evaluate condition
    condition_met = False

    if condition_type == "equals":
        condition_met = test_value == condition_value
    elif condition_type == "not_equals":
        condition_met = test_value != condition_value
    elif condition_type == "contains":
        condition_met = condition_value in str(test_value) if test_value else False
    elif condition_type == "greater_than":
        condition_met = (
            test_value > condition_value
            if isinstance(test_value, (int, float))
            else False
        )
    elif condition_type == "less_than":
        condition_met = (
            test_value < condition_value
            if isinstance(test_value, (int, float))
            else False
        )
    elif condition_type == "exists":
        condition_met = condition_key in input_data
    elif condition_type == "not_exists":
        condition_met = condition_key not in input_data

    # Return appropriate result
    result = true_result if condition_met else false_result

    return {
        "result": result,
        "condition_met": condition_met,
        "condition_type": condition_type,
        "test_value": test_value,
        "condition_value": condition_value,
        "evaluated_at": datetime.now().isoformat(),
        "success": True,
    }


# Test function for built-in steps
async def test_builtin_steps():
    """Test the built-in step functions"""

    from .execution_context import ExecutionContext, UserContext

    # Create test execution context
    workflow_config = {
        "workflow_id": "test-builtin",
        "name": "Test Built-in Steps",
        "steps": [],
    }

    user_context = UserContext(user_id="test_user")
    execution_context = ExecutionContext(workflow_config, user_context)

    print("Testing Built-in Steps:")
    print("=" * 50)

    # Test data input step
    print("\n1. Testing data_input_step:")
    step_config = {
        "step_id": "input_test",
        "config": {
            "input_type": "static",
            "data": {"message": "Hello, World!", "number": 42},
        },
    }
    result = await data_input_step(step_config, {}, execution_context)
    print(f"   Result: {result}")

    # Test data processing step
    print("\n2. Testing data_processing_step:")
    step_config = {
        "step_id": "process_test",
        "config": {"processing_type": "word_count"},
    }
    input_data = {"text": "This is a test sentence with multiple words."}
    result = await data_processing_step(step_config, input_data, execution_context)
    print(f"   Result: {result}")

    # Test data merge step
    print("\n3. Testing data_merge_step:")
    step_config = {"step_id": "merge_test", "config": {"merge_strategy": "combine"}}
    input_data = {"word_count": 8, "sentiment": "positive", "text": "This is a test"}
    result = await data_merge_step(step_config, input_data, execution_context)
    print(f"   Result: {result}")

    print("\n✅ Built-in steps test completed!")


if __name__ == "__main__":
    # Run test
    asyncio.run(test_builtin_steps())
