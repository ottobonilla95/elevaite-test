import os
import sys
import dotenv
import openai
import inspect
import functools
from typing import Any, Callable, Dict, List, Protocol, Union, cast, get_type_hints

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from data_classes import Agent

# Load environment variables
dotenv.load_dotenv(".env.local")
dotenv.load_dotenv(".env")

# Create OpenAI client with a dummy API key if not available
# This allows imports to work even without a valid API key
api_key = os.getenv("OPENAI_API_KEY", "dummy_key_for_import_testing")
try:
    client = openai.OpenAI(api_key=api_key)
except Exception as e:
    print(f"Warning: Could not initialize OpenAI client: {e}")
    client = None


class OpenAISchemaFunction(Protocol):
    openai_schema: Dict[str, Any]

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


# Function Schema function
def function_schema(func: Callable[..., Any]) -> OpenAISchemaFunction:
    """
    Decorator that generates an OpenAI function schema and attaches it to the function.
    """

    def python_function_to_openai_schema(func) -> Dict[str, Any]:
        """Converts a function into an OpenAI JSON schema."""
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)

        schema = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or f"Function {func.__name__}",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }

        for param_name, param in signature.parameters.items():
            param_type = type_hints.get(param_name, Any)
            openai_type, is_optional = python_type_to_openai_type(param_type)

            # schema["parameters"]["properties"][param_name] = {
            schema["function"]["parameters"]["properties"][param_name] = {
                "type": openai_type,
                "description": f"{param_name} parameter",
            }

            # Add to required list only if it's not Optional and has no default value
            if not is_optional and param.default is inspect.Parameter.empty:
                # schema["parameters"]["required"].append(param_name)
                schema["function"]["parameters"]["required"].append(param_name)

        return schema

    def python_type_to_openai_type(py_type) -> tuple[str, bool]:
        """Maps Python types to OpenAI JSON schema types, supporting Optional and List."""
        from typing import get_origin, get_args

        # Handle Optional[X] (Union[X, None])
        if get_origin(py_type) is Union:
            args = get_args(py_type)
            non_none_types = [t for t in args if t is not type(None)]
            if len(non_none_types) == 1:
                openai_type, _ = python_type_to_openai_type(non_none_types[0])
                return openai_type, True  # It's Optional

        # Handle List[X]
        if get_origin(py_type) is list or get_origin(py_type) is List:
            return "array", False

        # Base type mapping
        mapping = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
            dict: "object",
        }

        return mapping.get(py_type, "string"), False  # Default to string

    # Cast the function to a type that allows attribute assignment
    decorated_func = cast(OpenAISchemaFunction, func)
    # Now assign the schema
    decorated_func.openai_schema = python_function_to_openai_schema(func)
    # Return the original function type
    return decorated_func


class AgentWithSchema(Agent):
    openai_schema: Dict[str, Any]

    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


# Agent Schema function
def agent_schema(cls: type[Agent]) -> AgentWithSchema:
    """
    Decorator that generates an OpenAI function schema for an agent and attaches it to the class.
    The tool name will be the agent class name, not the 'execute' function.
    """

    def python_function_to_openai_schema(agent_cls: type[Agent]) -> Dict[str, Any]:
        """Converts an agent class into an OpenAI JSON schema based on its `execute` method."""
        execute_method = getattr(agent_cls, "execute", None)
        if execute_method is None:
            raise ValueError(f"{agent_cls.__name__} must have an 'execute' method.")

        signature = inspect.signature(execute_method)
        type_hints = get_type_hints(execute_method)

        schema = {
            "type": "function",
            "function": {
                "name": agent_cls.__name__,  # Tool name = Class name
                "description": execute_method.__doc__
                or f"Agent {agent_cls.__name__} execution function",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }

        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue  # Skip 'self' parameter

            param_type = type_hints.get(param_name, Any)
            openai_type, is_optional = python_type_to_openai_type(param_type)

            schema["function"]["parameters"]["properties"][param_name] = {
                "type": openai_type,
                "description": f"{param_name} parameter",
            }

            if not is_optional and param.default is inspect.Parameter.empty:
                schema["function"]["parameters"]["required"].append(param_name)

        return schema

    def python_type_to_openai_type(py_type) -> tuple[str, bool]:
        """Maps Python types to OpenAI JSON schema types, handling Optional and List types."""
        from typing import get_origin, get_args

        if get_origin(py_type) is Union:
            args = get_args(py_type)
            non_none_types = [t for t in args if t is not type(None)]
            if len(non_none_types) == 1:
                openai_type, _ = python_type_to_openai_type(non_none_types[0])
                return openai_type, True  # It's Optional

        if get_origin(py_type) is list or get_origin(py_type) is List:
            return "array", False

        mapping = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
            dict: "object",
        }

        return mapping.get(py_type, "string"), False  # Default to string

    # Cast the function to a type that allows attribute assignment
    decorated_cls = cast(AgentWithSchema, cls)
    # Now assign the schema
    decorated_cls.openai_schema = python_function_to_openai_schema(cls)
    # Return the original function type
    return decorated_cls


# Log Decorator
def log_decorator(func: Callable) -> Callable:
    """Decorator to log the input and output of a function."""

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        self.logs["input"].append(kwargs)
        try:
            result = func(self, *args, **kwargs)
            self.logs["output"].append(result)
            return result
        except Exception as e:
            self.logs["output"].append(f"Error: {e}")
            raise

    return wrapper
