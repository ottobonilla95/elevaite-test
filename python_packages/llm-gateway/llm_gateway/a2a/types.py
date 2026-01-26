"""Types for A2A client communication."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


@dataclass
class A2AAuthConfig:
    """Authentication configuration for A2A agent connections."""

    auth_type: Literal["none", "bearer", "api_key", "oauth2"] = "none"
    """Type of authentication to use."""

    credentials: Optional[Dict[str, Any]] = None
    """Authentication credentials. Structure depends on auth_type:
    - bearer: {"token": "..."}
    - api_key: {"key": "...", "header_name": "X-API-Key"}
    - oauth2: {"client_id": "...", "client_secret": "...", ...}
    """


@dataclass
class A2AAgentInfo:
    """Information about an A2A agent for connection."""

    base_url: str
    """Base URL of the A2A agent (e.g., 'https://agent.example.com')."""

    name: Optional[str] = None
    """Display name for the agent."""

    agent_card_url: Optional[str] = None
    """URL to fetch the Agent Card. Defaults to {base_url}/.well-known/agent.json."""

    auth: Optional[A2AAuthConfig] = None
    """Authentication configuration."""

    timeout: float = 30.0
    """Request timeout in seconds."""


@dataclass
class A2AMessageRequest:
    """Request to send a message to an A2A agent."""

    content: str
    """The message content to send."""

    context_id: Optional[str] = None
    """Optional context ID for conversation continuity."""

    task_id: Optional[str] = None
    """Optional task ID to continue an existing task."""

    metadata: Optional[Dict[str, Any]] = None
    """Optional metadata to include with the message."""

    accepted_output_modes: Optional[List[str]] = None
    """Accepted output modes (e.g., ['text', 'file', 'data'])."""


@dataclass
class A2ATaskInfo:
    """Information about a task returned from an A2A agent."""

    task_id: str
    """Unique identifier for the task."""

    state: str
    """Current state of the task (submitted, working, completed, failed, etc.)."""

    context_id: Optional[str] = None
    """Context ID for the conversation."""

    message: Optional[str] = None
    """Status message from the agent."""


@dataclass
class A2AMessageResponse:
    """Response from an A2A agent."""

    task: Optional[A2ATaskInfo] = None
    """Task information if the response is task-based."""

    content: Optional[str] = None
    """Text content from the agent response."""

    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    """Artifacts (files, data) returned by the agent."""

    raw_response: Optional[Dict[str, Any]] = None
    """Raw response data for advanced use cases."""

    is_complete: bool = False
    """Whether the task/response is complete."""

    error: Optional[str] = None
    """Error message if the request failed."""
