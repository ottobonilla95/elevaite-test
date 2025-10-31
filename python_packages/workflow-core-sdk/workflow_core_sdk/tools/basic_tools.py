"""
Basic Tools for Workflow Engine

A collection of useful tools that can be used with LLM function calling.
Based on tools from the agent-studio.
"""

import json
import os
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from .decorators import function_schema, tool_handler


@function_schema
def add_numbers(a: int, b: int) -> str:
    """
    Adds two numbers and returns the sum.
    """
    return f"The sum of {a} and {b} is {a + b}"


@function_schema
def get_current_time(timezone: str = "UTC") -> str:
    """
    Gets the current time in the specified timezone.
    """
    current_time = datetime.now()
    return f"Current time ({timezone}): {current_time.strftime('%Y-%m-%d %H:%M:%S')}"


@function_schema
def print_to_console(message: str) -> str:
    """
    Prints a message to the console for debugging purposes.
    """
    print(f"[TOOL OUTPUT] {message}")
    return f"Printed to console: {message}"


@function_schema
def weather_forecast(location: str, days: int = 1) -> str:
    """
    Gets weather forecast for a location (mock implementation).
    """
    # This is a mock implementation - in production you'd call a real weather API
    weather_conditions = ["sunny", "cloudy", "rainy", "partly cloudy"]
    import random

    condition = random.choice(weather_conditions)
    temp = random.randint(15, 30)

    return f"Weather forecast for {location} ({days} day{'s' if days > 1 else ''}): {condition}, {temp}°C"


@function_schema
def web_search(query: str, num_results: int = 5) -> str:
    """
    Performs a web search and returns results (mock implementation).
    """
    # Mock implementation - in production you'd use a real search API
    return (
        f"Web search results for '{query}' (showing {num_results} results):\n"
        f"1. Mock result about {query}\n"
        f"2. Another relevant result for {query}\n"
        f"3. More information on {query}"
    )


@function_schema
def url_to_markdown(url: str) -> str:
    """
    Converts a webpage URL to markdown format.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        # Simple conversion - in production you'd use a proper HTML to markdown converter
        content = response.text
        title = "Webpage Content"

        # Extract title if possible
        if "<title>" in content and "</title>" in content:
            title_start = content.find("<title>") + 7
            title_end = content.find("</title>")
            title = content[title_start:title_end]

        return (
            f"# {title}\n\nURL: {url}\n\nContent length: {len(content)} characters\n\n"
            f"Note: This is a simplified conversion. Full content available at the URL."
        )

    except Exception as e:
        return f"Error fetching URL {url}: {str(e)}"


@function_schema
def calculate(expression: str) -> str:
    """
    Performs mathematical calculations by evaluating expressions.
    """
    try:
        # Simple eval for demo - in production use a safe math parser
        result = eval(expression)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"


@function_schema
def file_operations(operation: str, filename: str, content: str = "") -> str:
    """
    Performs basic file operations (read, write, append).
    """
    try:
        if operation == "read":
            with open(filename, "r") as f:
                content = f.read()
            return f"File content of {filename}:\n{content}"

        elif operation == "write":
            with open(filename, "w") as f:
                f.write(content)
            return f"Successfully wrote {len(content)} characters to {filename}"

        elif operation == "append":
            with open(filename, "a") as f:
                f.write(content)
            return f"Successfully appended {len(content)} characters to {filename}"

        else:
            return f"Unknown operation: {operation}. Supported: read, write, append"

    except Exception as e:
        return f"File operation failed: {str(e)}"


@function_schema
def json_operations(operation: str, data: str, key: str = "", value: str = "") -> str:
    """
    Performs operations on JSON data (parse, extract, modify).
    """
    try:
        if operation == "parse":
            parsed = json.loads(data)
            return f"JSON parsed successfully. Keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Array with ' + str(len(parsed)) + ' items'}"

        elif operation == "extract":
            parsed = json.loads(data)
            if key in parsed:
                return f"Value for key '{key}': {parsed[key]}"
            else:
                return f"Key '{key}' not found in JSON"

        elif operation == "modify":
            parsed = json.loads(data)
            parsed[key] = json.loads(value) if value.startswith("{") or value.startswith("[") else value
            return json.dumps(parsed, indent=2)

        else:
            return f"Unknown operation: {operation}. Supported: parse, extract, modify"

    except json.JSONDecodeError as e:
        return f"Invalid JSON: {str(e)}"
    except Exception as e:
        return f"JSON operation failed: {str(e)}"


@tool_handler(name="environment_info", description="Gets environment information")
def get_environment_info(info_type: str = "all") -> str:
    """
    Gets information about the current environment.
    """
    if info_type == "env_vars":
        # Return non-sensitive environment variables
        safe_vars = {
            k: v
            for k, v in os.environ.items()
            if not any(sensitive in k.lower() for sensitive in ["key", "secret", "password", "token"])
        }
        return f"Environment variables: {json.dumps(safe_vars, indent=2)}"

    elif info_type == "cwd":
        return f"Current working directory: {os.getcwd()}"

    elif info_type == "python_path":
        import sys

        return f"Python executable: {sys.executable}\nPython path: {sys.path[:3]}..."

    else:
        return (
            f"Current working directory: {os.getcwd()}\n"
            f"Python executable: {__import__('sys').executable}\n"
            f"Available info types: env_vars, cwd, python_path, all"
        )


# Tool store - maps tool names to their functions
BASIC_TOOL_STORE = {
    "add_numbers": add_numbers,
    "get_current_time": get_current_time,
    "print_to_console": print_to_console,
    "weather_forecast": weather_forecast,
    "web_search": web_search,
    "url_to_markdown": url_to_markdown,
    "calculate": calculate,
    "file_operations": file_operations,
    "json_operations": json_operations,
    "environment_info": get_environment_info,
}

# Tool schemas - maps tool names to their OpenAI schemas
BASIC_TOOL_SCHEMAS = {name: func.openai_schema for name, func in BASIC_TOOL_STORE.items()}

# ---- Optional: include ported tool groups ----
try:
    from .kevel_tools import KEVEL_TOOL_STORE, KEVEL_TOOL_SCHEMAS

    BASIC_TOOL_STORE.update(KEVEL_TOOL_STORE)
    BASIC_TOOL_SCHEMAS.update(KEVEL_TOOL_SCHEMAS)
except Exception:
    # Keep SDK usable even if optional tool groups fail to import
    pass

try:
    from .servicenow_tools import SERVICENOW_TOOL_STORE, SERVICENOW_TOOL_SCHEMAS

    BASIC_TOOL_STORE.update(SERVICENOW_TOOL_STORE)
    BASIC_TOOL_SCHEMAS.update(SERVICENOW_TOOL_SCHEMAS)
except Exception:
    pass

try:
    from .salesforce_tools import SALESFORCE_TOOL_STORE, SALESFORCE_TOOL_SCHEMAS

    BASIC_TOOL_STORE.update(SALESFORCE_TOOL_STORE)
    BASIC_TOOL_SCHEMAS.update(SALESFORCE_TOOL_SCHEMAS)
except Exception:
    pass

try:
    from .database_tools import DATABASE_TOOL_STORE, DATABASE_TOOL_SCHEMAS

    BASIC_TOOL_STORE.update(DATABASE_TOOL_STORE)
    BASIC_TOOL_SCHEMAS.update(DATABASE_TOOL_SCHEMAS)
except Exception:
    pass

# Note: Additional tools from agent-studio are registered at runtime
# by the agent-studio API during startup (see main.py lifespan function)


def get_tool_by_name(name: str):
    """Get a tool function by name."""
    return BASIC_TOOL_STORE.get(name)


def get_tool_schema(name: str):
    """Get a tool schema by name."""
    return BASIC_TOOL_SCHEMAS.get(name)


def get_all_tools():
    """Get all available tools."""
    return BASIC_TOOL_STORE.copy()


def get_all_schemas():
    """Get all tool schemas."""
    return BASIC_TOOL_SCHEMAS.copy()


def get_tools_by_category(category: Optional[str] = None):
    """Get tools filtered by category."""
    if category is None:
        return get_all_tools()

    filtered_tools = {}
    for name, func in BASIC_TOOL_STORE.items():
        tool_category = getattr(func, "_tool_category", "general")
        if tool_category == category:
            filtered_tools[name] = func

    return filtered_tools
