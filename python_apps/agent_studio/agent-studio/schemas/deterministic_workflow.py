"""
Deterministic Workflow Configuration Schemas

Schemas for storing and managing deterministic workflows in the database.
These workflows can be created by users and stored in the database for reuse.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class WorkflowStepConfig(BaseModel):
    """Configuration for a single workflow step"""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_name: str
    step_type: Literal[
        "data_input", "data_output", "transformation", "validation", 
        "batch_processing", "conditional_branch", "parallel_execution",
        "aggregation", "notification", "data_processing"
    ]
    step_order: int = 0
    
    # Dependencies and execution
    dependencies: List[str] = []
    execution_pattern: Literal["sequential", "parallel", "conditional", "dag"] = "sequential"
    
    # Data flow configuration
    input_mapping: Dict[str, str] = {}  # Map input fields to previous step outputs
    
    # Step-specific configuration
    config: Dict[str, Any] = {}
    
    # Error handling
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    rollback_enabled: bool = False
    rollback_config: Optional[Dict[str, Any]] = None
    
    # Batch processing
    batch_size: Optional[int] = None
    parallel_batches: bool = False


class DeterministicWorkflowConfig(BaseModel):
    """Complete configuration for a deterministic workflow"""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Execution configuration
    execution_pattern: Literal["sequential", "parallel", "conditional", "dag"] = "sequential"
    timeout_seconds: Optional[int] = None
    max_retries: int = 3
    
    # Workflow steps
    steps: List[WorkflowStepConfig] = []
    
    # Metadata
    tags: List[str] = []
    category: Optional[str] = None
    created_by: Optional[str] = None
    
    # Validation
    @validator('steps')
    def validate_steps(cls, v):
        if not v:
            raise ValueError("Workflow must have at least one step")
        
        # Check for duplicate step_ids
        step_ids = [step.step_id for step in v]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("Duplicate step_ids found")
        
        # Validate dependencies exist
        for step in v:
            for dep in step.dependencies:
                if dep not in step_ids:
                    raise ValueError(f"Step {step.step_id} depends on non-existent step {dep}")
        
        return v


class DeterministicWorkflowTemplate(BaseModel):
    """Template for creating deterministic workflows"""
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    template_name: str
    description: str
    category: str
    
    # Template configuration
    config_template: DeterministicWorkflowConfig
    
    # Parameters that can be customized when using template
    configurable_parameters: Dict[str, Any] = {}
    
    # Metadata
    created_by: Optional[str] = None
    is_public: bool = False
    usage_count: int = 0


# Database schemas for API
class DeterministicWorkflowCreate(BaseModel):
    """Schema for creating a new deterministic workflow"""
    workflow_name: str
    description: Optional[str] = None
    config: DeterministicWorkflowConfig
    is_active: bool = True
    created_by: Optional[str] = None


class DeterministicWorkflowUpdate(BaseModel):
    """Schema for updating a deterministic workflow"""
    workflow_name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[DeterministicWorkflowConfig] = None
    is_active: Optional[bool] = None
    updated_by: Optional[str] = None


class DeterministicWorkflowResponse(BaseModel):
    """Response schema for deterministic workflow queries"""
    id: int
    workflow_id: str
    workflow_name: str
    description: Optional[str] = None
    config: DeterministicWorkflowConfig
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


# Execution request/response schemas
class WorkflowExecutionRequest(BaseModel):
    """Request to execute a deterministic workflow"""
    workflow_id: str
    input_data: Dict[str, Any]
    execution_config: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class WorkflowExecutionResponse(BaseModel):
    """Response from workflow execution request"""
    execution_id: str
    workflow_id: str
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    message: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None