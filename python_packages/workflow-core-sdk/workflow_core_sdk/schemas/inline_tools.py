"""
Inline Tool Definition Schemas

These schemas define the structure for inline tool definitions that can be
sent by the UI when attaching tools to agents. Instead of referencing
existing tools by ID, the UI can provide full tool definitions inline.

Supported inline tool types:
- user_function: User-provided Python code with a schema
- web_search: Web search with domain restrictions and location config
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


# ============================================================================
# Web Search Tool Configuration
# ============================================================================


class WebSearchUserLocation(BaseModel):
    """User location for web search personalization."""

    country: Optional[str] = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code (e.g., 'US', 'GB')",
        max_length=2,
    )
    region: Optional[str] = Field(
        default=None,
        description="Region or state name (e.g., 'California')",
    )
    city: Optional[str] = Field(
        default=None,
        description="City name (e.g., 'San Francisco')",
    )
    timezone: Optional[str] = Field(
        default=None,
        description="IANA timezone (e.g., 'America/Los_Angeles')",
    )


class WebSearchToolConfig(BaseModel):
    """Configuration for web search tool.

    Based on OpenAI Responses API web_search_preview tool configuration.

    Provider Support:
    - OpenAI: search_context_size ✓, user_location ✓
    - Gemini: Uses GoogleSearch (no configuration options supported, will log warning)

    Note: allowed_domains and blocked_domains are reserved for future use.
    """

    type: Literal["web_search"] = "web_search"

    search_context_size: Optional[Literal["low", "medium", "high"]] = Field(
        default="medium",
        description="Amount of context to include from search results (OpenAI only)",
    )

    user_location: Optional[WebSearchUserLocation] = Field(
        default=None,
        description="User location for search personalization (OpenAI only)",
    )

    allowed_domains: Optional[List[str]] = Field(
        default=None,
        description="List of domains to restrict search to (reserved for future use)",
    )

    blocked_domains: Optional[List[str]] = Field(
        default=None,
        description="List of domains to exclude from search (reserved for future use)",
    )


# ============================================================================
# User Function Tool Configuration
# ============================================================================


class CodeExecutionToolConfig(BaseModel):
    """Configuration for code execution tool (Code Interpreter).

    This enables the agent to write and execute its own Python code
    in a secure Nsjail sandbox. The agent generates the code at runtime.

    Note: This is different from user_function where the USER provides
    the code upfront. Here, the AGENT writes the code dynamically.
    """

    type: Literal["code_execution"] = "code_execution"

    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=60,
        description="Maximum execution time in seconds",
    )

    memory_mb: int = Field(
        default=256,
        ge=64,
        le=512,
        description="Memory limit in MB",
    )


class UserFunctionDefinition(BaseModel):
    """Definition for a user-provided function tool.

    The user provides:
    - name: Function name (must match the def in code)
    - description: What the function does (shown to the agent)
    - parameters_schema: JSON Schema for function parameters
    - code: Python implementation

    At runtime, when the agent calls this function, the code is executed
    in a secure sandbox with the arguments passed by the agent.

    Note: This is different from code_execution where the AGENT writes
    the code. Here, the USER provides the code upfront.
    """

    type: Literal["user_function"] = "user_function"

    name: str = Field(
        ...,
        description="Function name (should match def name in code)",
        min_length=1,
        max_length=100,
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
    )

    description: str = Field(
        ...,
        description="Description of what the function does (shown to the agent)",
        min_length=1,
        max_length=1000,
    )

    parameters_schema: Dict[str, Any] = Field(
        ...,
        description="JSON Schema defining the function's input parameters",
    )

    code: str = Field(
        ...,
        description="Python code implementing the function",
        min_length=1,
        max_length=100_000,
    )

    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=60,
        description="Maximum execution time in seconds",
    )

    memory_mb: int = Field(
        default=256,
        ge=64,
        le=512,
        description="Memory limit in MB",
    )


# ============================================================================
# Union Type for All Inline Tool Definitions
# ============================================================================

InlineToolDefinition = Union[
    UserFunctionDefinition, WebSearchToolConfig, CodeExecutionToolConfig
]
"""Union of all supported inline tool definition types.

The 'type' field discriminates between:
- 'user_function': UserFunctionDefinition - User provides code upfront
- 'web_search': WebSearchToolConfig - Web search with optional config
- 'code_execution': CodeExecutionToolConfig - Agent writes code at runtime
"""


# ============================================================================
# Constants for Placeholder Tool IDs
# ============================================================================

# These are well-known tool IDs for placeholder/template tools.
# When an inline definition is provided, we use these as the tool_id FK.
PLACEHOLDER_TOOL_IDS = {
    "user_function": "00000000-0000-0000-0000-000000000001",
    "web_search": "00000000-0000-0000-0000-000000000002",
    "code_execution": "00000000-0000-0000-0000-000000000003",
}
