"""
Schema Utilities for Workflow Steps

Provides utilities for generating OpenAI-compatible schemas for workflow steps,
including automatic schema generation from function signatures.
"""

import inspect
from typing import Any, Callable, Dict, Optional, get_type_hints


def python_type_to_json_type(python_type: Any) -> str:
    """
    Convert Python type to JSON schema type.
    
    Args:
        python_type: Python type annotation
        
    Returns:
        JSON schema type string
    """
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


def function_to_openai_schema(
    func: Callable[..., Any],
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert a Python function to an OpenAI function calling schema.
    
    This analyzes the function signature and type hints to generate
    a complete OpenAI-compatible schema.
    
    Args:
        func: The function to convert
        name: Override function name (defaults to func.__name__)
        description: Override description (defaults to func.__doc__)
        
    Returns:
        OpenAI function calling schema
        
    Example:
        >>> def add_numbers(a: int, b: int) -> int:
        ...     '''Adds two numbers together.'''
        ...     return a + b
        >>> schema = function_to_openai_schema(add_numbers)
        >>> schema['function']['name']
        'add_numbers'
    """
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    schema = {
        "type": "function",
        "function": {
            "name": name or func.__name__,
            "description": description or func.__doc__ or f"Function {func.__name__}",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            },
        },
    }
    
    for param_name, param in signature.parameters.items():
        # Skip special parameters
        if param_name in ["step_config", "input_data", "execution_context"]:
            continue
            
        param_type = type_hints.get(param_name, str)
        param_info = {"type": python_type_to_json_type(param_type)}
        
        # Add description from docstring if available
        if func.__doc__:
            # Simple extraction - could be enhanced with proper docstring parsing
            param_info["description"] = f"Parameter {param_name}"
        
        schema["function"]["parameters"]["properties"][param_name] = param_info
        
        # Mark as required if no default value
        if param.default == inspect.Parameter.empty:
            schema["function"]["parameters"]["required"].append(param_name)
    
    return schema


def create_step_input_schema(
    step_type: str,
    parameters_schema: Dict[str, Any],
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an OpenAI-compatible input schema for a workflow step.
    
    Args:
        step_type: The step type identifier
        parameters_schema: JSON schema for the step's config parameters
        description: Description of the step's inputs
        
    Returns:
        OpenAI function calling schema for step inputs
    """
    return {
        "type": "function",
        "function": {
            "name": step_type,
            "description": description or f"Input parameters for {step_type}",
            "parameters": parameters_schema
        }
    }


def create_step_output_schema(
    step_type: str,
    output_schema: Dict[str, Any],
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create an OpenAI-compatible output schema for a workflow step.
    
    Args:
        step_type: The step type identifier
        output_schema: JSON schema for the step's output
        description: Description of the step's outputs
        
    Returns:
        OpenAI function calling schema for step outputs
    """
    return {
        "type": "function",
        "function": {
            "name": f"{step_type}_output",
            "description": description or f"Output from {step_type}",
            "parameters": output_schema
        }
    }


def infer_output_schema_from_function(func: Callable[..., Any]) -> Dict[str, Any]:
    """
    Infer output schema from a step function's return type annotation.
    
    Args:
        func: The step function
        
    Returns:
        JSON schema for the function's output
        
    Note:
        This is a best-effort inference. For complex return types,
        it's better to explicitly define the output schema.
    """
    type_hints = get_type_hints(func)
    return_type = type_hints.get("return", dict)
    
    # Default schema for dict return type (most common for steps)
    if return_type == dict or return_type == Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "success": {
                    "type": "boolean",
                    "description": "Whether the step executed successfully"
                },
                "result": {
                    "description": "The step's output data"
                },
                "error": {
                    "type": "string",
                    "description": "Error message if success is false"
                }
            }
        }
    
    # For other types, create a simple wrapper
    return {
        "type": "object",
        "properties": {
            "result": {
                "type": python_type_to_json_type(return_type),
                "description": "The step's output"
            }
        }
    }


def extract_output_fields(output_schema: Dict[str, Any], step_id: str) -> list[Dict[str, Any]]:
    """
    Extract available output fields from a step's output schema.
    
    This is useful for building UI components that allow users to map
    step outputs to subsequent step inputs.
    
    Args:
        output_schema: The step's output schema (OpenAI format)
        step_id: The step instance ID
        
    Returns:
        List of available output fields with their paths and types
        
    Example:
        >>> schema = {
        ...     "type": "function",
        ...     "function": {
        ...         "parameters": {
        ...             "type": "object",
        ...             "properties": {
        ...                 "result": {"type": "object"},
        ...                 "success": {"type": "boolean"}
        ...             }
        ...         }
        ...     }
        ... }
        >>> fields = extract_output_fields(schema, "step1")
        >>> fields[0]['path']
        'step1.result'
    """
    fields = []
    
    if "function" not in output_schema:
        return fields
    
    parameters = output_schema["function"].get("parameters", {})
    properties = parameters.get("properties", {})
    
    def extract_nested_fields(props: Dict[str, Any], prefix: str = ""):
        for field_name, field_schema in props.items():
            field_path = f"{prefix}.{field_name}" if prefix else field_name
            full_path = f"{step_id}.{field_path}"
            
            field_info = {
                "path": full_path,
                "name": field_name,
                "type": field_schema.get("type", "any"),
                "description": field_schema.get("description", "")
            }
            fields.append(field_info)
            
            # Recursively extract nested object properties
            if field_schema.get("type") == "object" and "properties" in field_schema:
                extract_nested_fields(field_schema["properties"], field_path)
    
    extract_nested_fields(properties)
    return fields

