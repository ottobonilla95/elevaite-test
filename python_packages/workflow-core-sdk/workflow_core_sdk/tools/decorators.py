"""
Tool Decorators for Workflow Engine

Provides decorators for creating tools that can be used with LLM function calling.
Based on the agent-studio implementation.
"""

import inspect
import re
from typing import Any, Callable, Dict, Optional, Protocol, get_type_hints


class OpenAISchemaFunction(Protocol):
    openai_schema: Dict[str, Any]

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


def _parse_docstring_params(docstring: Optional[str]) -> Dict[str, Dict[str, str]]:
    """
    Parse parameter information from Google-style or NumPy-style docstrings.

    Supports formats like:
    - Google: "param_name (type): Description"
    - Google: "param_name: Description"
    - NumPy: "param_name : type\n    Description"

    Args:
        docstring: The function's docstring

    Returns:
        Dictionary mapping parameter names to their title and description
        Example: {"api_key": {"title": "API Key", "description": "Your API key"}}
    """
    if not docstring:
        return {}

    params_info: Dict[str, Dict[str, str]] = {}

    # Try to find Args/Arguments/Parameters section
    # Match until we hit another section (Returns, Raises, etc.) or end of string
    args_match = re.search(
        r"^\s*(?:Args|Arguments|Parameters):\s*\n((?:.*\n)*?)(?:^\s*(?:Returns|Raises|Yields|Examples?|Notes?|See Also|Attributes|References):|$)",
        docstring,
        re.MULTILINE,
    )

    if not args_match:
        return {}

    args_section = args_match.group(1)

    # Parse parameters line by line to handle multi-line descriptions
    # Split into lines and process
    lines = args_section.split("\n")
    current_param = None
    current_desc_lines = []

    for line in lines:
        # Check if this line starts a new parameter (has a colon and word before it)
        param_match = re.match(r"^(\s*)(\w+)\s*(?:\([^)]+\))?\s*:\s*(.*)$", line)

        if param_match:
            # Save previous parameter if exists
            if current_param:
                description = " ".join(current_desc_lines).strip()
                title = current_param.replace("_", " ").title()
                params_info[current_param] = {"title": title, "description": description}

            # Start new parameter
            len(param_match.group(1))
            current_param = param_match.group(2)
            current_desc_lines = [param_match.group(3)] if param_match.group(3).strip() else []
        elif current_param and line.strip():
            # This is a continuation line for the current parameter
            current_desc_lines.append(line.strip())

    # Don't forget the last parameter
    if current_param:
        description = " ".join(current_desc_lines).strip()
        title = current_param.replace("_", " ").title()
        params_info[current_param] = {"title": title, "description": description}

    return params_info


def function_schema(func: Callable[..., Any]) -> OpenAISchemaFunction:
    """
    Decorator that generates an OpenAI function schema and attaches it to the function.

    This decorator analyzes the function signature and docstring to create
    an OpenAI-compatible tool schema that can be used for function calling.

    Args:
        func: The function to decorate

    Returns:
        The decorated function with an attached openai_schema attribute

    Example:
        @function_schema
        def add_numbers(a: int, b: int) -> str:
            '''Adds two numbers and returns the sum.'''
            return f"The sum of {a} and {b} is {a + b}"
    """

    def python_function_to_openai_schema(func) -> Dict[str, Any]:
        """Converts a function into an OpenAI JSON schema with title and description from docstring."""
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)

        # Parse docstring to extract parameter information
        params_info = _parse_docstring_params(func.__doc__)

        schema = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or f"Function {func.__name__}",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }

        for param_name, param in signature.parameters.items():
            param_type = type_hints.get(param_name, str)
            param_info = {"type": _python_type_to_json_type(param_type)}

            # Add title and description from parsed docstring
            if param_name in params_info:
                param_info["title"] = params_info[param_name]["title"]
                param_info["description"] = params_info[param_name]["description"]
            else:
                # Fallback: generate title from parameter name
                param_info["title"] = param_name.replace("_", " ").title()
                param_info["description"] = f"Parameter {param_name}"

            schema["function"]["parameters"]["properties"][param_name] = param_info

            # Mark as required if no default value
            if param.default == inspect.Parameter.empty:
                schema["function"]["parameters"]["required"].append(param_name)

        return schema

    def _python_type_to_json_type(python_type) -> str:
        """Convert Python type to JSON schema type."""
        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }

        # Handle typing module types
        if hasattr(python_type, "__origin__"):
            origin = python_type.__origin__
            if origin is list:
                return "array"
            elif origin is dict:
                return "object"
            elif origin is tuple:
                return "array"

        return type_mapping.get(python_type, "string")

    # Generate and attach the schema
    schema = python_function_to_openai_schema(func)
    func.openai_schema = schema

    return func


def tool_handler(name: str = None, description: str = None, category: str = "general"):
    """
    Enhanced decorator for tool functions with additional metadata.

    Args:
        name: Override the function name in the schema
        description: Override the function description
        category: Tool category for organization

    Example:
        @tool_handler(name="calculate", description="Performs mathematical calculations")
        def math_calculator(expression: str) -> str:
            '''Evaluates a mathematical expression.'''
            return str(eval(expression))
    """

    def decorator(func: Callable[..., Any]) -> OpenAISchemaFunction:
        # Apply the function_schema decorator first
        decorated_func = function_schema(func)

        # Override name and description if provided
        if name:
            decorated_func.openai_schema["function"]["name"] = name
        if description:
            decorated_func.openai_schema["function"]["description"] = description

        # Add metadata
        decorated_func._tool_category = category
        decorated_func._tool_name = name or func.__name__

        return decorated_func

    return decorator


def async_tool_handler(name: str = None, description: str = None, category: str = "general"):
    """
    Decorator for async tool functions.

    Same as tool_handler but marks the function as async for proper handling.
    """

    def decorator(func: Callable[..., Any]) -> OpenAISchemaFunction:
        decorated_func = tool_handler(name, description, category)(func)
        decorated_func._is_async = True
        return decorated_func

    return decorator


def create_tool_schema(name: str, description: str, parameters: Dict[str, Any], required: list = None) -> Dict[str, Any]:
    """
    Manually create a tool schema without decorating a function.

    Useful for creating schemas for external APIs or complex tools.

    Args:
        name: Tool name
        description: Tool description
        parameters: Parameter schema
        required: List of required parameter names

    Returns:
        OpenAI-compatible tool schema
    """
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": parameters, "required": required or []},
        },
    }


def extract_tool_info(func: OpenAISchemaFunction) -> Dict[str, Any]:
    """
    Extract tool information from a decorated function.

    Args:
        func: Function decorated with @function_schema or @tool_handler

    Returns:
        Dictionary with tool metadata
    """
    return {
        "name": getattr(func, "_tool_name", func.__name__),
        "category": getattr(func, "_tool_category", "general"),
        "is_async": getattr(func, "_is_async", False),
        "schema": func.openai_schema,
        "function": func,
    }
