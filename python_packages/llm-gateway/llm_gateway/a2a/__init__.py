"""A2A (Agent-to-Agent) client module for communicating with external A2A agents."""

from .client import A2AClientService
from .types import (
    A2AAgentInfo,
    A2AAuthConfig,
    A2AMessageRequest,
    A2AMessageResponse,
    A2ATaskInfo,
)

__all__ = [
    "A2AClientService",
    "A2AAgentInfo",
    "A2AAuthConfig",
    "A2AMessageRequest",
    "A2AMessageResponse",
    "A2ATaskInfo",
]

