"""
Data Processing Steps

Basic data processing, input/output, and manipulation steps.
These provide fundamental data operations for workflows.
"""

import asyncio
from typing import Dict, Any
from datetime import datetime
import logging

from workflow_core_sdk.execution_context import ExecutionContext

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

        if source == "subflow_input":
            # Get data from subflow input
            subflow_data = execution_context.step_io_data.get("subflow_input", {})
            return {
                "data": subflow_data,
                "input_type": "dynamic",
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "success": True,
            }
        else:
            # Default dynamic data
            return {
                "data": {
                    "message": f"Dynamic data from {source}",
                    "timestamp": datetime.now().isoformat(),
                    "source": source,
                },
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
    Data processing step that performs various transformations on input data.

    Config options:
    - processing_type: Type of processing to perform
    - options: Additional options for processing
    """

    config = step_config.get("config", {})
    processing_type = config.get("processing_type", "identity")
    options = config.get("options", {})

    # Get the data to process
    data_to_process = input_data

    if processing_type == "identity":
        # Return data as-is
        result = data_to_process

    elif processing_type == "count":
        # Count items in data
        if isinstance(data_to_process, dict):
            result = {"count": len(data_to_process)}
        elif isinstance(data_to_process, list):
            result = {"count": len(data_to_process)}
        elif isinstance(data_to_process, str):
            result = {
                "count": len(data_to_process),
                "word_count": len(data_to_process.split()),
            }
        else:
            result = {"count": 1}

    elif processing_type == "filter":
        # Filter data based on criteria
        filter_key = options.get("filter_key")
        filter_value = options.get("filter_value")

        if isinstance(data_to_process, dict) and filter_key:
            result = {k: v for k, v in data_to_process.items() if k == filter_key}
        elif isinstance(data_to_process, list) and filter_key:
            result = [
                item
                for item in data_to_process
                if isinstance(item, dict) and item.get(filter_key) == filter_value
            ]
        else:
            result = data_to_process

    elif processing_type == "sentiment_analysis":
        # Simple sentiment analysis simulation
        text = ""
        if isinstance(data_to_process, str):
            text = data_to_process
        elif isinstance(data_to_process, dict):
            text = str(data_to_process.get("text", data_to_process))

        # Simple keyword-based sentiment
        positive_words = [
            "good",
            "great",
            "excellent",
            "amazing",
            "wonderful",
            "fantastic",
        ]
        negative_words = ["bad", "terrible", "awful", "horrible", "disappointing"]

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            sentiment = "positive"
        elif negative_count > positive_count:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        result = {
            "sentiment": sentiment,
            "confidence": abs(positive_count - negative_count)
            / max(len(text.split()), 1),
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

    # Add metadata if provided in options
    metadata = options.get("metadata", {})
    if metadata:
        if isinstance(result, dict):
            result.update(metadata)
        else:
            # If result is not a dict, wrap it with metadata
            result = {"data": result, **metadata}

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
    - merge_strategy: How to merge the data ("combine", "override", etc.)
    - sources: List of data sources to merge
    """

    config = step_config.get("config", {})
    merge_strategy = config.get("merge_strategy", "combine")

    # Get data sources from input mapping or config
    data_sources = input_data.get("data_sources", {})

    if not data_sources:
        # Fallback: try to get all available step data
        data_sources = execution_context.step_io_data

    result = {}

    if merge_strategy == "combine":
        # Combine all data sources
        for source_name, source_data in data_sources.items():
            if isinstance(source_data, dict):
                result.update(source_data)
            else:
                result[source_name] = source_data

    elif merge_strategy == "override":
        # Later sources override earlier ones
        for source_name, source_data in data_sources.items():
            if isinstance(source_data, dict):
                result.update(source_data)
            else:
                result[source_name] = source_data

    elif merge_strategy == "list":
        # Combine as a list
        result = {"merged_data": list(data_sources.values())}

    else:
        # Default: just combine everything
        result = dict(data_sources)

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
    """

    config = step_config.get("config", {})
    condition = config.get("condition", "true")
    true_action = config.get("true_action", {"type": "pass"})
    false_action = config.get("false_action", {"type": "pass"})

    # Simple condition evaluation (can be enhanced)
    condition_result = True
    if condition == "false":
        condition_result = False
    elif isinstance(condition, str) and condition.startswith("input."):
        # Simple input field check
        field_path = condition[6:]  # Remove "input."
        value = input_data
        for part in field_path.split("."):
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                value = None
                break
        condition_result = bool(value)

    # Execute appropriate action
    action = true_action if condition_result else false_action
    action_type = action.get("type", "pass")

    if action_type == "pass":
        result = input_data
    elif action_type == "transform":
        transformation = action.get("transformation", {})
        result = {**input_data, **transformation}
    else:
        result = input_data

    return {
        "condition": condition,
        "condition_result": condition_result,
        "action_taken": action,
        "result": result,
        "evaluated_at": datetime.now().isoformat(),
        "success": True,
    }
