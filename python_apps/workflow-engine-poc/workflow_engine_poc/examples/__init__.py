"""
Example Workflows Package

This package contains example workflow configurations for testing and demonstration.
These examples showcase different features and patterns of the workflow engine.
"""

from .workflows import (
    EXAMPLE_SIMPLE_WORKFLOW,
    EXAMPLE_AGENT_WORKFLOW,
    EXAMPLE_PARALLEL_WORKFLOW,
    EXAMPLE_SUBFLOW_CHILD,
    EXAMPLE_SUBFLOW_PARENT,
)

__all__ = [
    "EXAMPLE_SIMPLE_WORKFLOW",
    "EXAMPLE_AGENT_WORKFLOW", 
    "EXAMPLE_PARALLEL_WORKFLOW",
    "EXAMPLE_SUBFLOW_CHILD",
    "EXAMPLE_SUBFLOW_PARENT",
]
