"""Variable injection utility for workflow templates.

This module provides functionality to replace {{variable_name}} placeholders
in strings with runtime values. It's used for prompt templates, input mappings,
and other dynamic content in workflows.

Example:
    >>> inject_variables("Current time is {{current_time}}")
    "Current time is 2026-01-19T12:30:45Z"

    >>> inject_variables("Hello {{user_name}}", {"user_name": "Alice"})
    "Hello Alice"
"""

import re
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
import uuid

# Pattern to match {{variable_name}} placeholders
VARIABLE_PATTERN = re.compile(r"\{\{(\s*[\w\.]+\s*)\}\}")


def get_builtin_variables() -> Dict[str, Callable[[], Any]]:
    """
    Get the built-in system variables that are always available.

    Returns:
        Dict mapping variable names to callables that produce their values.
    """
    return {
        # Time-related variables
        "current_time": lambda: datetime.now(timezone.utc).isoformat(),
        "current_date": lambda: datetime.now(timezone.utc).date().isoformat(),
        "current_timestamp": lambda: int(datetime.now(timezone.utc).timestamp()),
        "current_year": lambda: datetime.now(timezone.utc).year,
        "current_month": lambda: datetime.now(timezone.utc).month,
        "current_day": lambda: datetime.now(timezone.utc).day,
        "current_hour": lambda: datetime.now(timezone.utc).hour,
        "current_minute": lambda: datetime.now(timezone.utc).minute,
        # Unique identifiers
        "uuid": lambda: str(uuid.uuid4()),
        "execution_id": lambda: str(uuid.uuid4()),  # Can be overridden by context
    }


def resolve_variable(
    var_name: str,
    custom_variables: Optional[Dict[str, Any]] = None,
    execution_context: Optional[Any] = None,
) -> Optional[str]:
    """
    Resolve a single variable name to its value.

    Args:
        var_name: The variable name (without braces)
        custom_variables: Custom variable values provided at runtime
        execution_context: Optional execution context for accessing step data

    Returns:
        The resolved value as a string, or None if not found
    """
    var_name = var_name.strip()

    # Check custom variables first (highest priority)
    if custom_variables and var_name in custom_variables:
        value = custom_variables[var_name]
        return str(value) if value is not None else None

    # Check for dot notation (e.g., "step_id.field_name")
    if "." in var_name and execution_context:
        parts = var_name.split(".", 1)
        step_id, field_name = parts[0], parts[1]

        # Try to get from execution context step_io_data
        if hasattr(execution_context, "step_io_data"):
            step_data = execution_context.step_io_data.get(step_id, {})
            if isinstance(step_data, dict):
                value = step_data.get(field_name)
                if value is not None:
                    return str(value)

    # Check execution context for special variables (before built-in fallback)
    if execution_context:
        if var_name == "execution_id" and hasattr(execution_context, "execution_id"):
            return str(execution_context.execution_id)
        if var_name == "workflow_id" and hasattr(execution_context, "workflow_id"):
            return str(execution_context.workflow_id)
        if var_name == "user_id" and hasattr(execution_context, "user_id"):
            return str(execution_context.user_id)
        if var_name == "session_id" and hasattr(execution_context, "session_id"):
            return str(execution_context.session_id)

    # Check built-in variables (fallback)
    builtins = get_builtin_variables()
    if var_name in builtins:
        return str(builtins[var_name]())

    return None


def inject_variables(
    template: str,
    custom_variables: Optional[Dict[str, Any]] = None,
    execution_context: Optional[Any] = None,
    preserve_unresolved: bool = False,
) -> str:
    """
    Replace {{variable_name}} placeholders in a template with their values.

    Args:
        template: The string containing {{variable}} placeholders
        custom_variables: Custom variable values to use for replacement
        execution_context: Optional execution context for accessing step data
        preserve_unresolved: If True, keep unresolved variables as-is;
                            if False, replace with empty string

    Returns:
        The template with variables replaced

    Example:
        >>> inject_variables("Hello {{user_name}}, time is {{current_time}}",
        ...                  {"user_name": "Alice"})
        "Hello Alice, time is 2026-01-19T12:30:45+00:00"
    """
    if not template or not isinstance(template, str):
        return template

    def replace_match(match: re.Match) -> str:
        var_name = match.group(1)
        resolved = resolve_variable(var_name, custom_variables, execution_context)

        if resolved is not None:
            return resolved
        elif preserve_unresolved:
            return match.group(0)  # Keep original {{variable}}
        else:
            return ""  # Replace with empty string

    return VARIABLE_PATTERN.sub(replace_match, template)


def extract_variables(template: str) -> list[str]:
    """
    Extract all variable names from a template.

    Args:
        template: The string containing {{variable}} placeholders

    Returns:
        List of variable names (without braces)
    """
    if not template or not isinstance(template, str):
        return []

    matches = VARIABLE_PATTERN.findall(template)
    return [m.strip() for m in matches]
