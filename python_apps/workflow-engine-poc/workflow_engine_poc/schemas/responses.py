"""
Response schemas for workflow-engine-poc API endpoints

These models define the structure of responses for endpoints that don't
have corresponding models in the SDK.
"""

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid as uuid_module


# ============================================================================
# File Upload Responses
# ============================================================================


class FileUploadResponse(BaseModel):
    """Response model for file upload endpoint"""

    message: str = Field(description="Success message")
    filename: str = Field(description="Original filename")
    file_path: str = Field(description="Path where file was saved")
    file_size: int = Field(description="Size of uploaded file in bytes")
    upload_timestamp: str = Field(description="ISO timestamp of upload")
    auto_processing: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Auto-processing details if workflow was triggered",
    )


# ============================================================================
# Step Registration Responses
# ============================================================================


class StepInfoResponse(BaseModel):
    """Response model for step information"""

    step_type: str = Field(description="Step type identifier")
    name: str = Field(description="Human-readable step name")
    description: Optional[str] = Field(default=None, description="Step description")
    category: Optional[str] = Field(default=None, description="Step category")
    parameters_schema: Dict[str, Any] = Field(description="Parameters JSON Schema")
    return_schema: Optional[Dict[str, Any]] = Field(default=None, description="Return value schema")
    execution_config: Optional[Dict[str, Any]] = Field(default=None, description="Execution configuration")
    handler_url: Optional[str] = Field(default=None, description="Remote handler URL")
    handler_method: Optional[str] = Field(default=None, description="HTTP method for handler")
    tags: Optional[List[str]] = Field(default=None, description="Step tags")
    version: str = Field(description="Step version")
    is_async: bool = Field(description="Whether step is async")
    registered_at: Optional[str] = Field(default=None, description="Registration timestamp")


class RegisteredStepsResponse(BaseModel):
    """Response model for listing registered steps"""

    steps: List[StepInfoResponse] = Field(description="List of registered steps")
    total: int = Field(description="Total number of registered steps")


class StepRegistrationResponse(BaseModel):
    """Response model for step registration"""

    message: str = Field(description="Success message")
    step_type: str = Field(description="Registered step type")


# ============================================================================
# Approval Responses
# ============================================================================


class ApprovalDecisionResponse(BaseModel):
    """Response model for approval/denial actions"""

    status: Literal["ok", "error"] = Field(description="Operation status")
    backend: str = Field(description="Execution backend used")
    message: Optional[str] = Field(default=None, description="Optional status message")


# ============================================================================
# Monitoring & Analytics Responses
# ============================================================================


class MetricsResponse(BaseModel):
    """Response model for Prometheus metrics endpoint"""

    # This endpoint returns plain text, so this model is for documentation only
    content: str = Field(description="Prometheus metrics in text format")


class TraceInfo(BaseModel):
    """Information about a single trace"""

    trace_id: str = Field(description="Unique trace identifier")
    timestamp: str = Field(description="Trace timestamp")
    duration_ms: Optional[float] = Field(default=None, description="Trace duration in milliseconds")
    status: Optional[str] = Field(default=None, description="Trace status")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional trace metadata")


class TracesResponse(BaseModel):
    """Response model for traces endpoint"""

    traces: List[TraceInfo] = Field(description="List of traces")
    total: int = Field(description="Total number of traces available")
    limit: int = Field(description="Limit applied to results")


class MonitoringComponentStatus(BaseModel):
    """Status of a monitoring component"""

    traces: Literal["active", "inactive", "degraded"] = Field(description="Traces component status")
    metrics: Literal["active", "inactive", "degraded"] = Field(description="Metrics component status")
    error_tracking: Literal["active", "inactive", "degraded"] = Field(description="Error tracking status")


class MonitoringSummary(BaseModel):
    """Summary of monitoring metrics"""

    active_traces: int = Field(default=0, description="Number of active traces")
    total_requests: int = Field(default=0, description="Total requests processed")
    error_rate: float = Field(default=0.0, description="Error rate (0.0 to 1.0)")
    avg_response_time: float = Field(default=0.0, description="Average response time in ms")


class MonitoringSummaryResponse(BaseModel):
    """Response model for monitoring summary endpoint"""

    monitoring_status: Literal["active", "inactive", "degraded"] = Field(description="Overall monitoring status")
    summary: MonitoringSummary = Field(description="Monitoring metrics summary")
    components: MonitoringComponentStatus = Field(description="Status of monitoring components")


class ExecutionSummary(BaseModel):
    """Summary of a workflow execution"""

    execution_id: str = Field(description="Execution ID")
    workflow_id: str = Field(description="Workflow ID")
    status: str = Field(description="Execution status")
    started_at: Optional[str] = Field(default=None, description="Start timestamp")
    completed_at: Optional[str] = Field(default=None, description="Completion timestamp")
    duration_ms: Optional[float] = Field(default=None, description="Execution duration in ms")
    step_count: Optional[int] = Field(default=None, description="Number of steps")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ExecutionAnalyticsResponse(BaseModel):
    """Response model for execution analytics endpoint"""

    executions: List[ExecutionSummary] = Field(description="List of execution summaries")
    total: int = Field(description="Total number of executions")
    limit: int = Field(description="Limit applied")
    offset: int = Field(description="Offset applied")
    filter: Optional[Dict[str, Any]] = Field(default=None, description="Filters applied")


class ErrorInfo(BaseModel):
    """Information about an error"""

    error_id: Optional[str] = Field(default=None, description="Error identifier")
    timestamp: str = Field(description="Error timestamp")
    component: str = Field(description="Component where error occurred")
    error_type: str = Field(description="Type of error")
    message: str = Field(description="Error message")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace if available")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional error metadata")


class ErrorStatistics(BaseModel):
    """Error statistics summary"""

    total_errors: int = Field(description="Total number of errors")
    errors_by_component: Dict[str, List[ErrorInfo]] = Field(description="Errors grouped by component")
    recent_errors: List[ErrorInfo] = Field(description="Most recent errors")
    last_updated: Optional[str] = Field(default=None, description="Last update timestamp")


class ErrorAnalyticsResponse(BaseModel):
    """Response model for error analytics endpoint"""

    component: Optional[str] = Field(default=None, description="Component filter applied")
    errors: Optional[List[ErrorInfo]] = Field(default=None, description="Errors for specific component")
    total: Optional[int] = Field(default=None, description="Total errors for component")
    statistics: Optional[ErrorStatistics] = Field(default=None, description="Full error statistics")


# ============================================================================
# Health Check Responses
# ============================================================================


class HealthCheckResponse(BaseModel):
    """Response model for basic health check"""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(description="Health status")
    registered_steps: int = Field(description="Number of registered steps")
    step_types: List[str] = Field(description="List of registered step types")


class RootHealthResponse(BaseModel):
    """Response model for root endpoint"""

    message: str = Field(description="Welcome message")
    version: str = Field(description="API version")
    status: Literal["running", "starting", "stopping"] = Field(description="Service status")


class SystemInfo(BaseModel):
    """System information"""

    uptime: str = Field(description="System uptime")
    memory_usage: str = Field(description="Memory usage information")


class DetailedHealthCheckResponse(BaseModel):
    """Response model for detailed health check"""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(description="Health status")
    timestamp: Optional[str] = Field(default=None, description="Health check timestamp")
    error_statistics: Optional[ErrorStatistics] = Field(default=None, description="Error statistics")
    system_info: Optional[SystemInfo] = Field(default=None, description="System information")
    error: Optional[str] = Field(default=None, description="Error message if degraded")


class MonitoringHealthInfo(BaseModel):
    """Monitoring health information"""

    active_traces: int = Field(description="Number of active traces")
    total_requests: int = Field(description="Total requests processed")
    error_rate: float = Field(description="Error rate")
    avg_response_time: float = Field(description="Average response time in ms")


class MonitoringHealthCheckResponse(BaseModel):
    """Response model for monitoring health check"""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(description="Monitoring health status")
    monitoring: MonitoringHealthInfo = Field(description="Monitoring metrics")
    error: Optional[str] = Field(default=None, description="Error message if degraded")


# ============================================================================
# Generic API Responses
# ============================================================================


class DeleteResponse(BaseModel):
    """Generic response for delete operations"""

    deleted: bool = Field(description="Whether the resource was deleted")
    message: Optional[str] = Field(default=None, description="Optional message")


class SuccessResponse(BaseModel):
    """Generic success response"""

    success: bool = Field(description="Whether the operation succeeded")
    message: Optional[str] = Field(default=None, description="Optional message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Optional response data")


class ErrorResponse(BaseModel):
    """Generic error response"""

    error: str = Field(description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    code: Optional[str] = Field(default=None, description="Error code")
    timestamp: Optional[str] = Field(default=None, description="Error timestamp")


# ============================================================================
# Paginated Response Wrapper
# ============================================================================


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper"""

    items: List[Any] = Field(description="List of items")
    total: int = Field(description="Total number of items available")
    limit: int = Field(description="Limit applied to results")
    offset: int = Field(description="Offset applied to results")
    has_more: bool = Field(description="Whether more results are available")


# ============================================================================
# Execution Status Responses
# ============================================================================


class ExecutionStatusResponse(BaseModel):
    """Response model for execution status endpoint"""

    execution_id: str = Field(description="Execution ID")
    workflow_id: str = Field(description="Workflow ID")
    status: str = Field(description="Current execution status")
    started_at: Optional[str] = Field(default=None, description="Start timestamp")
    completed_at: Optional[str] = Field(default=None, description="Completion timestamp")
    current_step: Optional[str] = Field(default=None, description="Current step ID")
    progress: Optional[float] = Field(default=None, description="Progress percentage (0-100)")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Execution metadata")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ExecutionResultsResponse(BaseModel):
    """Response model for execution results endpoint"""

    execution_id: str = Field(description="Execution ID")
    workflow_id: str = Field(description="Workflow ID")
    status: str = Field(description="Execution status")
    results: Dict[str, Any] = Field(description="Execution results")
    outputs: Optional[Dict[str, Any]] = Field(default=None, description="Step outputs")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Execution metadata")
    started_at: Optional[str] = Field(default=None, description="Start timestamp")
    completed_at: Optional[str] = Field(default=None, description="Completion timestamp")

