#!/usr/bin/env python3
"""
FastMCP Test Server for MCP Tool Execution Testing

This server provides simple test tools for validating MCP tool execution.
Run with: python scripts/mcp_test_server.py

The server will start on http://localhost:8765 by default.
"""

import json
from datetime import datetime
from typing import Any, Dict

try:
    from fastmcp import FastMCP
except ImportError:
    print("❌ FastMCP not installed. Install with: pip install fastmcp")
    exit(1)

# Create FastMCP server
mcp = FastMCP("Test MCP Server")


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        The sum of a and b
    """
    return a + b


@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        The product of a and b
    """
    return a * b


@mcp.tool()
def echo(message: str) -> str:
    """Echo back a message.

    Args:
        message: The message to echo

    Returns:
        The same message
    """
    return message


@mcp.tool()
def get_current_time() -> str:
    """Get the current UTC time.

    Returns:
        Current UTC time in ISO format
    """
    return datetime.utcnow().isoformat()


@mcp.tool()
def greet(name: str, greeting: str = "Hello") -> str:
    """Greet someone with a custom greeting.

    Args:
        name: The name of the person to greet
        greeting: The greeting to use (default: "Hello")

    Returns:
        A greeting message
    """
    return f"{greeting}, {name}!"


@mcp.tool()
def calculate_stats(numbers: list[float]) -> Dict[str, float]:
    """Calculate statistics for a list of numbers.

    Args:
        numbers: List of numbers to analyze

    Returns:
        Dictionary with min, max, mean, and sum
    """
    if not numbers:
        return {"min": 0, "max": 0, "mean": 0, "sum": 0}

    return {
        "min": min(numbers),
        "max": max(numbers),
        "mean": sum(numbers) / len(numbers),
        "sum": sum(numbers),
    }


@mcp.tool()
def format_json(data: Dict[str, Any], indent: int = 2) -> str:
    """Format a dictionary as pretty-printed JSON.

    Args:
        data: The data to format
        indent: Number of spaces for indentation (default: 2)

    Returns:
        Pretty-printed JSON string
    """
    return json.dumps(data, indent=indent)


@mcp.tool()
def reverse_string(text: str) -> str:
    """Reverse a string.

    Args:
        text: The string to reverse

    Returns:
        The reversed string
    """
    return text[::-1]


@mcp.tool()
def count_words(text: str) -> int:
    """Count the number of words in a text.

    Args:
        text: The text to analyze

    Returns:
        Number of words
    """
    return len(text.split())


@mcp.tool()
def to_uppercase(text: str) -> str:
    """Convert text to uppercase.

    Args:
        text: The text to convert

    Returns:
        Uppercase text
    """
    return text.upper()


if __name__ == "__main__":

    print("🚀 Starting FastMCP Test Server...")
    print("📍 Server will be available at: http://localhost:8765")
    print("🔧 Available tools:")
    print("   - add(a, b): Add two numbers")
    print("   - multiply(a, b): Multiply two numbers")
    print("   - echo(message): Echo a message")
    print("   - get_current_time(): Get current UTC time")
    print("   - greet(name, greeting='Hello'): Greet someone")
    print("   - calculate_stats(numbers): Calculate statistics")
    print("   - format_json(data, indent=2): Format JSON")
    print("   - reverse_string(text): Reverse a string")
    print("   - count_words(text): Count words")
    print("   - to_uppercase(text): Convert to uppercase")
    print("\n📡 Endpoints:")
    print("   - GET  /tools - List available tools")
    print("   - POST /execute - Execute a tool")
    print("   - GET  /health - Health check")
    print("\nPress Ctrl+C to stop the server\n")

    # Run the server with HTTP transport
    mcp.run(transport="http", host="0.0.0.0", port=8765)
