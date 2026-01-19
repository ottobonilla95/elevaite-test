"""
Workflow Engine Steps Package

This package contains all step implementations organized by domain:

- data_steps: Basic data processing, input/output, merging
- ai_steps: LLM agents, AI-powered processing (including external A2A agents)
- file_steps: File operations, text processing, tokenization
- flow_steps: Control flow, subflows, conditional execution
- trigger_steps: Workflow trigger normalization
- input_steps: Input node entry points
- output_steps: Output node endpoints (pass-through for canvas display)
- merge_steps: Merge node for combining multiple inputs
- prompt_steps: Prompt node for configuring agent prompts with variable injection
- tool_steps: Tool execution
- human_steps: Human approval/interaction
- ingestion_steps: Ingestion service integration

Each module contains related step functions that can be registered
with the step registry for workflow execution.

Note: Steps are imported lazily by the step registry to avoid
import errors from optional dependencies.
"""

# Export all step function names (but don't import them yet)
__all__ = [
    # Data processing steps
    "data_input_step",
    "data_processing_step",
    "data_merge_step",
    "delay_step",
    "conditional_step",
    # AI/LLM steps (includes built-in agents and external A2A agents)
    "agent_execution_step",
    # File processing steps
    "file_reader_step",
    "text_chunking_step",
    "embedding_generation_step",
    "vector_storage_step",
    # Flow control steps
    "subflow_step",
    # Trigger steps
    "trigger_step",
    # Input/Output/Merge/Prompt steps (multi-trigger support)
    "input_step",
    "output_step",
    "merge_step",
    "prompt_step",
    # Tool steps
    "tool_execution_step",
    # Human steps
    "human_approval_step",
    # Ingestion steps
    "ingestion_step",
]
