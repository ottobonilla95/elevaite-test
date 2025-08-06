"""
Workflow execution utilities and helper functions.

This module contains all the helper functions for workflow execution,
including deterministic workflow detection, hybrid workflow routing,
and execution logic that was previously in workflow_endpoints.py.
"""

import json
import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import concurrent.futures

from services.workflow_execution_context import WorkflowExecutionContext
from schemas.deterministic_workflow import (
    WorkflowExecutionRequest as DetWorkflowExecutionRequest,
)
from db.schemas import workflows as schemas
from fastapi_logger import ElevaiteLogger


logger = ElevaiteLogger()


# Workflow Detection Functions


def is_deterministic_workflow(configuration: Dict[str, Any]) -> bool:
    """
    Check if a workflow configuration represents a deterministic workflow.

    A deterministic workflow is identified by:
    1. Having a 'workflow_type' field set to 'deterministic'
    2. Having a 'steps' field with deterministic step configurations
    3. Not having traditional 'agents' and 'connections' fields
    """
    # Check for explicit deterministic workflow type
    if configuration.get("workflow_type") == "deterministic":
        return True

    # Check for deterministic workflow structure (steps without agents)
    has_steps = "steps" in configuration and isinstance(configuration["steps"], list)
    has_agents = "agents" in configuration and isinstance(configuration["agents"], list)

    # If it has steps but no agents, it's likely a deterministic workflow
    if has_steps and not has_agents:
        return True

    # Check if steps contain deterministic step types
    if has_steps:
        deterministic_step_types = {
            "data_input",
            "data_output",
            "transformation",
            "validation",
            "batch_processing",
            "conditional_branch",
            "parallel_execution",
            "aggregation",
            "notification",
            "data_processing",
        }

        for step in configuration["steps"]:
            if (
                isinstance(step, dict)
                and step.get("step_type") in deterministic_step_types
            ):
                return True

    return False


def is_hybrid_workflow(configuration: Dict[str, Any]) -> bool:
    """
    Check if a workflow configuration represents a hybrid workflow.

    A hybrid workflow has:
    1. Traditional agents and connections
    2. At least one DeterministicWorkflowAgent
    3. Execution logic with conditional routing
    """
    # Must have agents (traditional workflow structure)
    agents = configuration.get("agents", [])
    if not agents:
        return False

    # Check for DeterministicWorkflowAgent
    has_deterministic_agent = any(
        agent.get("agent_type") == "DeterministicWorkflowAgent" for agent in agents
    )

    # Check for execution logic with routing rules
    has_execution_logic = "execution_logic" in configuration

    return has_deterministic_agent or has_execution_logic


# Input Analysis Functions


def analyze_input_context(
    execution_request: schemas.WorkflowExecutionRequest,
) -> Dict[str, Any]:
    """
    Analyze the execution request to determine input context for conditional routing.
    """
    context = {
        "has_file": False,
        "query_length": len(execution_request.query),
        "has_chat_history": bool(execution_request.chat_history),
        "runtime_overrides": execution_request.runtime_overrides or {},
    }

    # Check for file attachments in runtime overrides or query
    if execution_request.runtime_overrides:
        context["has_file"] = bool(
            execution_request.runtime_overrides.get("file_attachment")
            or execution_request.runtime_overrides.get("uploaded_file")
            or execution_request.runtime_overrides.get("document")
        )

    # Simple heuristic: check if query mentions file-related keywords
    file_keywords = ["file", "document", "upload", "pdf", "doc", "attachment"]
    query_lower = execution_request.query.lower()
    context["mentions_file"] = any(keyword in query_lower for keyword in file_keywords)

    return context


def evaluate_condition(condition: str, context: Dict[str, Any]) -> bool:
    """
    Evaluate a condition string against the input context.
    Supports simple JavaScript-like expressions.
    """
    try:
        # Simple condition evaluation - can be extended for more complex logic
        if condition == "input.has_file":
            return context.get("has_file", False)
        elif condition == "!input.has_file":
            return not context.get("has_file", False)
        elif condition == "input.mentions_file":
            return context.get("mentions_file", False)
        elif "has_file" in condition:
            return context.get("has_file", False)
        else:
            # Default to false for unknown conditions
            return False
    except Exception:
        return False


# Workflow Configuration Functions


def convert_to_deterministic_config(
    workflow, execution_request: schemas.WorkflowExecutionRequest
) -> Dict[str, Any]:
    """
    Convert a workflow configuration to deterministic workflow format.
    """
    config = workflow.configuration.copy()

    # If it's already in deterministic format, return as-is
    if is_deterministic_workflow(config):
        return config

    # Otherwise, create a basic deterministic wrapper
    # This handles cases where someone saves a deterministic workflow through the regular workflow API
    return {
        "workflow_id": str(workflow.workflow_id),
        "workflow_name": workflow.name,
        "description": workflow.description or "",
        "version": workflow.version,
        "execution_pattern": "sequential",
        "steps": config.get("steps", []),
        "workflow_type": "deterministic",
    }


# Response Formatting Functions


def safe_json_serialize(obj):
    """Safely serialize objects to JSON string."""
    try:
        if isinstance(obj, str):
            return json.dumps({"content": obj})
        elif isinstance(obj, (dict, list, int, float, bool)) or obj is None:
            return json.dumps(obj)
        elif hasattr(obj, "__iter__") and not isinstance(obj, str):
            return json.dumps({"content": str(list(obj))})
        else:
            return json.dumps({"content": str(obj)})
    except (TypeError, ValueError) as e:
        return json.dumps({"content": str(obj), "serialization_error": str(e)})


def create_success_response(
    result: Any, workflow_id: str, execution_id: str = ""
) -> schemas.WorkflowExecutionResponse:
    """Create a standardized success response."""
    formatted_response = safe_json_serialize(result)

    return schemas.WorkflowExecutionResponse(
        status="success",
        response=formatted_response,
        execution_id=execution_id,
        workflow_id=workflow_id,
        deployment_id="",
        timestamp=datetime.now().isoformat(),
    )


def create_error_response(
    error: str, workflow_id: str, execution_id: str = ""
) -> schemas.WorkflowExecutionResponse:
    """Create a standardized error response."""
    return schemas.WorkflowExecutionResponse(
        status="error",
        response=json.dumps({"error": error}),
        execution_id=execution_id,
        workflow_id=workflow_id,
        deployment_id="",
        timestamp=datetime.now().isoformat(),
    )


# Execution Timeout Wrapper


def execute_with_timeout(func, *args, timeout_seconds=60, **kwargs):
    """Execute a function with timeout using ThreadPoolExecutor."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(func, *args, **kwargs)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise HTTPException(
                status_code=504,
                detail=f"Execution timed out after {timeout_seconds} seconds",
            )
