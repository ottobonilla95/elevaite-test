"""Prompt node step - provides prompt configuration for connected Agent steps.

The Prompt step acts like an input step but specifically for prompt configuration.
It outputs prompt templates and variable definitions that connected Agent steps
can use to configure their prompts.

Features:
- Define system prompts and query templates with {{variable}} syntax
- Variables are resolved at runtime from step outputs, input data, or built-ins
- Override or extend agent prompt configuration
- Pass model configuration overrides (model_name, temperature, max_tokens)
"""

from typing import Any, Dict, List

from workflow_core_sdk.execution_context import ExecutionContext
from workflow_core_sdk.utils.variable_injection import inject_variables, extract_variables


def _resolve_variable_sources(
    variables: List[Dict[str, Any]],
    execution_context: ExecutionContext,
    input_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Resolve variable values from their defined sources.

    Args:
        variables: List of variable definitions with 'name', 'source', 'default_value'
        execution_context: The workflow execution context
        input_data: Input data passed to the step

    Returns:
        Dict mapping variable names to their resolved values
    """
    resolved = {}

    for var in variables:
        name = var.get("name")
        source = var.get("source")
        default = var.get("default_value")

        if not name:
            continue

        value = None

        # Try to resolve from source
        if source:
            # Check if source is a step reference (e.g., "step_id.field" or "step_id.nested.field")
            if "." in source:
                parts = source.split(".")
                step_id = parts[0]
                field_path = parts[1:]  # Remaining parts form the nested path
                step_data = execution_context.step_io_data.get(step_id, {})

                # Navigate nested path
                current = step_data
                for key in field_path:
                    if isinstance(current, dict):
                        current = current.get(key)
                    else:
                        current = None
                        break
                value = current
            else:
                # Direct reference to step output or input_data
                if source in execution_context.step_io_data:
                    value = execution_context.step_io_data[source]
                elif source in input_data:
                    value = input_data[source]

        # Fall back to default if no value found
        if value is None and default is not None:
            value = default

        if value is not None:
            resolved[name] = value

    return resolved


async def prompt_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Process a prompt step and output prompt configuration for connected Agent steps.

    The prompt step:
    1. Extracts prompt templates from parameters
    2. Resolves variable values from defined sources
    3. Injects variables into templates
    4. Returns the processed prompt configuration

    Args:
        step_config: The step configuration
        input_data: Input data passed to the step
        execution_context: The workflow execution context

    Returns:
        Dict containing:
        - system_prompt: Processed system prompt (with variables injected)
        - query_template: Processed query template (with variables injected)
        - raw_system_prompt: Original template before injection
        - raw_query_template: Original template before injection
        - variables: Resolved variable values
        - model_overrides: Model configuration overrides
        - override_agent_prompt: Whether to override or append to agent prompt
    """
    step_id = step_config.get("step_id", "prompt")
    params = step_config.get("parameters", step_config.get("config", {}))

    # Extract templates
    raw_system_prompt = params.get("system_prompt")
    raw_query_template = params.get("query_template")
    variable_defs = params.get("variables", [])
    override_agent_prompt = params.get("override_agent_prompt", True)

    # Model overrides
    model_overrides = {}
    if params.get("provider"):
        model_overrides["provider"] = params["provider"]
    if params.get("model_name"):
        model_overrides["model_name"] = params["model_name"]
    if params.get("temperature") is not None:
        model_overrides["temperature"] = params["temperature"]
    if params.get("max_tokens") is not None:
        model_overrides["max_tokens"] = params["max_tokens"]

    # Resolve variable values from sources
    resolved_variables = _resolve_variable_sources(variable_defs, execution_context, input_data)

    # Also include any variables from input_data that match template variables
    if raw_system_prompt:
        for var_name in extract_variables(raw_system_prompt):
            if var_name not in resolved_variables and var_name in input_data:
                resolved_variables[var_name] = input_data[var_name]
    if raw_query_template:
        for var_name in extract_variables(raw_query_template):
            if var_name not in resolved_variables and var_name in input_data:
                resolved_variables[var_name] = input_data[var_name]

    # Inject variables into templates
    system_prompt = (
        inject_variables(
            raw_system_prompt,
            custom_variables=resolved_variables,
            execution_context=execution_context,
            preserve_unresolved=True,  # Keep unresolved for agent to handle
        )
        if raw_system_prompt
        else None
    )

    query_template = (
        inject_variables(
            raw_query_template,
            custom_variables=resolved_variables,
            execution_context=execution_context,
            preserve_unresolved=True,
        )
        if raw_query_template
        else None
    )

    return {
        "step_id": step_id,
        "step_type": "prompt",
        "system_prompt": system_prompt,
        "query_template": query_template,
        "raw_system_prompt": raw_system_prompt,
        "raw_query_template": raw_query_template,
        "variables": resolved_variables,
        "model_overrides": model_overrides,
        "override_agent_prompt": override_agent_prompt,
    }
