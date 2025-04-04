import inspect
from typing import Any, Dict, List, Union, get_type_hints
import functools
from typing import Any, Callable
import os
import openai
import dotenv

dotenv.load_dotenv(".env.local")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Function Schema function
def function_schema(func):
    """
    Decorator that generates an OpenAI function schema and attaches it to the function.
    """
    def python_function_to_openai_schema(func) -> Dict[str, Any]:
        """Converts a function into an OpenAI JSON schema."""
        signature = inspect.signature(func)
        type_hints = get_type_hints(func)

        schema = {
            "type": "function",
            "function":{
            "name": func.__name__,
            "description": func.__doc__ or f"Function {func.__name__}",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        }

        for param_name, param in signature.parameters.items():
            param_type = type_hints.get(param_name, Any)
            openai_type, is_optional = python_type_to_openai_type(param_type)

            # schema["parameters"]["properties"][param_name] = {
            schema["function"]["parameters"]["properties"][param_name] = {
                "type": openai_type,
                "description": f"{param_name} parameter"
            }

            # Add to required list only if it's not Optional and has no default value
            if not is_optional and param.default is inspect.Parameter.empty:
                # schema["parameters"]["required"].append(param_name)
                schema["function"]["parameters"]["required"].append(param_name)

        return schema

    def python_type_to_openai_type(py_type) -> (str, bool):
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

    # Attach schema as a function attribute
    func.openai_schema = python_function_to_openai_schema(func)
    return func

# Agent Schema function
def agent_schema(cls):
    """
    Decorator that generates an OpenAI function schema for an agent and attaches it to the class.
    The tool name will be the agent class name, not the 'execute' function.
    """
    def python_function_to_openai_schema(agent_cls) -> Dict[str, Any]:
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
                "description": execute_method.__doc__ or f"Agent {agent_cls.__name__} execution function",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue  # Skip 'self' parameter

            param_type = type_hints.get(param_name, Any)
            openai_type, is_optional = python_type_to_openai_type(param_type)

            schema["function"]["parameters"]["properties"][param_name] = {
                "type": openai_type,
                "description": f"{param_name} parameter"
            }

            if not is_optional and param.default is inspect.Parameter.empty:
                schema["function"]["parameters"]["required"].append(param_name)

        return schema

    def python_type_to_openai_type(py_type) -> (str, bool):
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

    # Attach schema as a class attribute
    cls.openai_schema = python_function_to_openai_schema(cls)
    return cls

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