"""
Workflow Engine Steps Package

This package contains all step implementations organized by domain:

- data_steps: Basic data processing, input/output, merging
- ai_steps: LLM agents, AI-powered processing
- file_steps: File operations, text processing, tokenization
- flow_steps: Control flow, subflows, conditional execution
- integration_steps: External API calls, database operations

Each module contains related step functions that can be registered
with the step registry for workflow execution.
"""

# Import all step functions for easy registration
from .data_steps import (
    data_input_step,
    data_processing_step,
    data_merge_step,
    delay_step,
    conditional_step,
)

from .ai_steps import (
    agent_execution_step,
)

from .file_steps import (
    file_reader_step,
    text_chunking_step,
    embedding_generation_step,
    vector_storage_step,
)

from .flow_steps import (
    subflow_step,
)

# Export all step functions
__all__ = [
    # Data processing steps
    "data_input_step",
    "data_processing_step", 
    "data_merge_step",
    "delay_step",
    "conditional_step",
    
    # AI/LLM steps
    "agent_execution_step",
    
    # File processing steps
    "file_reader_step",
    "text_chunking_step",
    "embedding_generation_step",
    "vector_storage_step",
    
    # Flow control steps
    "subflow_step",
]
