"""
API Schemas for workflow-engine-poc

This package contains Pydantic models for API request and response validation.
These schemas complement the SDK models and provide type safety for PoC-specific endpoints.
"""

from .requests import (
    # Agent Tool Binding
    AgentToolBindingCreate,
    AgentToolBindingUpdate,
    # Step Registration
    StepConfigCreate,
    # Approval Decisions
    ApprovalDecisionRequest,
    # File Upload
    FileUploadMetadata,
    # Workflow Execution
    WorkflowExecutionRequest,
    # Tool Updates
    ToolStubUpdate,
    # Query Parameters
    PaginationParams,
    WorkflowFilterParams,
    ExecutionFilterParams,
    ToolFilterParams,
)

from .responses import (
    # File Upload
    FileUploadResponse,
    # Step Registration
    StepInfoResponse,
    RegisteredStepsResponse,
    StepRegistrationResponse,
    # Approvals
    ApprovalDecisionResponse,
    # Monitoring & Analytics
    MetricsResponse,
    TraceInfo,
    TracesResponse,
    MonitoringComponentStatus,
    MonitoringSummary,
    MonitoringSummaryResponse,
    ExecutionSummary,
    ExecutionAnalyticsResponse,
    ErrorInfo,
    ErrorStatistics,
    ErrorAnalyticsResponse,
    # Health Checks
    HealthCheckResponse,
    RootHealthResponse,
    SystemInfo,
    DetailedHealthCheckResponse,
    MonitoringHealthInfo,
    MonitoringHealthCheckResponse,
    # Generic Responses
    DeleteResponse,
    SuccessResponse,
    ErrorResponse,
    PaginatedResponse,
    # Execution Status
    ExecutionStatusResponse,
    ExecutionResultsResponse,
)

__all__ = [
    # Request Models
    "AgentToolBindingCreate",
    "AgentToolBindingUpdate",
    "StepConfigCreate",
    "ApprovalDecisionRequest",
    "FileUploadMetadata",
    "WorkflowExecutionRequest",
    "ToolStubUpdate",
    "PaginationParams",
    "WorkflowFilterParams",
    "ExecutionFilterParams",
    "ToolFilterParams",
    # Response Models
    "FileUploadResponse",
    "StepInfoResponse",
    "RegisteredStepsResponse",
    "StepRegistrationResponse",
    "ApprovalDecisionResponse",
    "MetricsResponse",
    "TraceInfo",
    "TracesResponse",
    "MonitoringComponentStatus",
    "MonitoringSummary",
    "MonitoringSummaryResponse",
    "ExecutionSummary",
    "ExecutionAnalyticsResponse",
    "ErrorInfo",
    "ErrorStatistics",
    "ErrorAnalyticsResponse",
    "HealthCheckResponse",
    "RootHealthResponse",
    "SystemInfo",
    "DetailedHealthCheckResponse",
    "MonitoringHealthInfo",
    "MonitoringHealthCheckResponse",
    "DeleteResponse",
    "SuccessResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "ExecutionStatusResponse",
    "ExecutionResultsResponse",
]

