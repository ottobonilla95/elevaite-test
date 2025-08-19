"""
Pydantic models for the Workflow Execution Engine API
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepConfig(BaseModel):
    """Configuration for a workflow step"""
    step_id: str = Field(..., description="Unique identifier for the step")
    step_name: str = Field(..., description="Human-readable name for the step")
    step_type: str = Field(..., description="Type of step (e.g., 'agent_execution', 'file_reader')")
    step_order: Optional[int] = Field(None, description="Order of execution (optional)")
    dependencies: List[str] = Field(default_factory=list, description="List of step IDs this step depends on")
    input_mapping: Dict[str, str] = Field(default_factory=dict, description="Mapping of input data from previous steps")
    config: Dict[str, Any] = Field(default_factory=dict, description="Step-specific configuration")
    timeout_seconds: Optional[int] = Field(None, description="Timeout for step execution")
    max_retries: int = Field(default=0, description="Maximum number of retries on failure")
    retry_delay_seconds: Optional[int] = Field(None, description="Delay between retries")


class WorkflowConfig(BaseModel):
    """Configuration for a complete workflow"""
    workflow_id: Optional[str] = Field(None, description="Unique identifier for the workflow")
    name: str = Field(..., description="Human-readable name for the workflow")
    description: Optional[str] = Field(None, description="Description of the workflow")
    execution_pattern: str = Field(default="sequential", description="Execution pattern: sequential, parallel, or conditional")
    steps: List[StepConfig] = Field(..., description="List of steps in the workflow")
    global_config: Dict[str, Any] = Field(default_factory=dict, description="Global configuration for all steps")
    timeout_seconds: Optional[int] = Field(None, description="Overall workflow timeout")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the workflow")


class ExecutionRequest(BaseModel):
    """Request to execute a workflow"""
    workflow_config: WorkflowConfig = Field(..., description="The workflow configuration to execute")
    user_id: Optional[str] = Field(None, description="ID of the user executing the workflow")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    organization_id: Optional[str] = Field(None, description="Organization ID")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Initial input data for the workflow")
    execution_options: Dict[str, Any] = Field(default_factory=dict, description="Execution-specific options")


class ExecutionResponse(BaseModel):
    """Response from workflow execution request"""
    execution_id: str = Field(..., description="Unique identifier for this execution")
    status: str = Field(..., description="Current status of the execution")
    message: str = Field(..., description="Human-readable message about the execution")
    started_at: Optional[str] = Field(None, description="ISO timestamp when execution started")


class StepRegistrationRequest(BaseModel):
    """Request to register a new step type"""
    step_type: str = Field(..., description="Unique type identifier for the step")
    name: str = Field(..., description="Human-readable name for the step type")
    description: Optional[str] = Field(None, description="Description of what this step does")
    function_reference: str = Field(..., description="Python path or RPC endpoint for the step function")
    execution_type: str = Field(default="local", description="Execution type: local, rpc, or api")
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema for step parameters")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema for step output")
    endpoint_config: Dict[str, Any] = Field(default_factory=dict, description="Configuration for RPC/API endpoints")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the step")


class AgentConfig(BaseModel):
    """Configuration for agent execution steps"""
    agent_name: str = Field(..., description="Name of the agent")
    agent_type: str = Field(default="command", description="Type of agent")
    model: str = Field(..., description="LLM model to use")
    temperature: float = Field(default=0.1, description="Temperature for LLM generation")
    max_tokens: int = Field(default=1000, description="Maximum tokens for response")
    system_prompt: str = Field(..., description="System prompt for the agent")
    tools: List[str] = Field(default_factory=list, description="List of tools available to the agent")
    additional_config: Dict[str, Any] = Field(default_factory=dict, description="Additional agent configuration")


class TokenizerStepConfig(BaseModel):
    """Configuration for tokenizer steps"""
    tokenizer_step: str = Field(..., description="Type of tokenizer step")
    input_source: Optional[str] = Field(None, description="Source of input data")
    output_format: str = Field(default="json", description="Format of output data")
    processing_options: Dict[str, Any] = Field(default_factory=dict, description="Processing-specific options")


class ValidationResult(BaseModel):
    """Result of workflow validation"""
    is_valid: bool = Field(..., description="Whether the workflow is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    step_validation: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Per-step validation results")


class ExecutionSummary(BaseModel):
    """Summary of workflow execution"""
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: ExecutionStatus
    current_step: Optional[str]
    completed_steps: int
    failed_steps: int
    pending_steps: int
    total_steps: int
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_ms: Optional[int]
    user_id: Optional[str]
    session_id: Optional[str]


class StepResult(BaseModel):
    """Result of a single step execution"""
    step_id: str
    status: str
    output_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time_ms: Optional[int]
    retry_count: int
    started_at: Optional[str]
    completed_at: Optional[str]


class ExecutionResults(BaseModel):
    """Detailed results of workflow execution"""
    execution_id: str
    status: ExecutionStatus
    step_results: Dict[str, StepResult]
    step_io_data: Dict[str, Any]
    metadata: Dict[str, Any]
    analytics_ids: Dict[str, Any]


class AnalyticsQuery(BaseModel):
    """Query parameters for execution analytics"""
    limit: int = Field(default=100, description="Maximum number of results")
    offset: int = Field(default=0, description="Offset for pagination")
    status: Optional[ExecutionStatus] = Field(None, description="Filter by execution status")
    workflow_id: Optional[str] = Field(None, description="Filter by workflow ID")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    start_date: Optional[str] = Field(None, description="Filter executions after this date (ISO format)")
    end_date: Optional[str] = Field(None, description="Filter executions before this date (ISO format)")


class AnalyticsResponse(BaseModel):
    """Response for analytics queries"""
    total_executions: int
    executions: List[ExecutionSummary]
    statistics: Dict[str, Any]
    pagination: Dict[str, Any]


# Example workflow configurations for testing
EXAMPLE_SIMPLE_WORKFLOW = {
    "name": "Simple Test Workflow",
    "description": "A simple workflow for testing",
    "execution_pattern": "sequential",
    "steps": [
        {
            "step_id": "step1",
            "step_name": "Initialize",
            "step_type": "data_input",
            "step_order": 1,
            "config": {
                "input_type": "static",
                "data": {"message": "Hello, World!"}
            }
        },
        {
            "step_id": "step2",
            "step_name": "Process",
            "step_type": "data_processing",
            "step_order": 2,
            "dependencies": ["step1"],
            "input_mapping": {
                "input_data": "step1.data"
            },
            "config": {
                "processing_type": "transform",
                "transformation": "uppercase"
            }
        }
    ]
}

EXAMPLE_AGENT_WORKFLOW = {
    "name": "Agent Execution Workflow",
    "description": "Workflow with agent execution",
    "execution_pattern": "sequential",
    "steps": [
        {
            "step_id": "read_file",
            "step_name": "Read File",
            "step_type": "file_reader",
            "step_order": 1,
            "config": {
                "file_path": "/tmp/test.txt",
                "encoding": "utf-8"
            }
        },
        {
            "step_id": "analyze_content",
            "step_name": "Analyze Content",
            "step_type": "agent_execution",
            "step_order": 2,
            "dependencies": ["read_file"],
            "input_mapping": {
                "content": "read_file.content"
            },
            "config": {
                "agent_config": {
                    "agent_name": "Content Analyzer",
                    "model": "gpt-4o-mini",
                    "temperature": 0.1,
                    "max_tokens": 500,
                    "system_prompt": "You are a content analyzer. Analyze the provided content and summarize it.",
                    "tools": []
                },
                "query": "Please analyze and summarize the provided content.",
                "return_simplified": True
            }
        }
    ]
}

EXAMPLE_PARALLEL_WORKFLOW = {
    "name": "Parallel Processing Workflow",
    "description": "Workflow with parallel step execution",
    "execution_pattern": "parallel",
    "steps": [
        {
            "step_id": "init",
            "step_name": "Initialize",
            "step_type": "data_input",
            "step_order": 1,
            "config": {
                "data": {"text": "Sample text for processing"}
            }
        },
        {
            "step_id": "process_a",
            "step_name": "Process A",
            "step_type": "data_processing",
            "step_order": 2,
            "dependencies": ["init"],
            "input_mapping": {
                "text": "init.data.text"
            },
            "config": {
                "processing_type": "word_count"
            }
        },
        {
            "step_id": "process_b",
            "step_name": "Process B",
            "step_type": "data_processing",
            "step_order": 2,
            "dependencies": ["init"],
            "input_mapping": {
                "text": "init.data.text"
            },
            "config": {
                "processing_type": "sentiment_analysis"
            }
        },
        {
            "step_id": "merge",
            "step_name": "Merge Results",
            "step_type": "data_merge",
            "step_order": 3,
            "dependencies": ["process_a", "process_b"],
            "input_mapping": {
                "word_count": "process_a.result",
                "sentiment": "process_b.result"
            },
            "config": {
                "merge_strategy": "combine"
            }
        }
    ]
}
