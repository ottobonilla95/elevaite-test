
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, ConfigDict

class AgentExecutionMetricsBase(BaseModel):
    agent_id: uuid.UUID
    agent_name: str
    start_time: datetime
    status: str
    query: Optional[str] = None
    response: Optional[str] = None
    error_message: Optional[str] = None
    tools_called: Optional[Dict[str, Any]] = None
    tool_count: int = 0
    retry_count: int = 0
    max_retries: int = 3
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tokens_used: Optional[int] = None
    api_calls_count: int = 0

class AgentExecutionMetricsCreate(AgentExecutionMetricsBase):
    pass

class AgentExecutionMetricsUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: Optional[str] = None
    response: Optional[str] = None
    error_message: Optional[str] = None
    tools_called: Optional[Dict[str, Any]] = None
    tool_count: Optional[int] = None
    retry_count: Optional[int] = None
    tokens_used: Optional[int] = None
    api_calls_count: Optional[int] = None

class AgentExecutionMetricsInDB(AgentExecutionMetricsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    execution_id: uuid.UUID
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None

class AgentExecutionMetricsResponse(AgentExecutionMetricsInDB):
    pass

class ToolUsageMetricsBase(BaseModel):
    tool_name: str
    execution_id: uuid.UUID
    start_time: datetime
    status: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    external_api_called: Optional[str] = None
    api_response_time_ms: Optional[int] = None
    api_status_code: Optional[int] = None

class ToolUsageMetricsCreate(ToolUsageMetricsBase):
    pass

class ToolUsageMetricsUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: Optional[str] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    api_response_time_ms: Optional[int] = None
    api_status_code: Optional[int] = None

class ToolUsageMetricsInDB(ToolUsageMetricsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usage_id: uuid.UUID
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None

class ToolUsageMetricsResponse(ToolUsageMetricsInDB):
    pass

class WorkflowMetricsBase(BaseModel):
    workflow_type: str
    start_time: datetime
    status: str
    agents_involved: Optional[Dict[str, Any]] = None
    agent_count: int = 1
    total_tool_calls: int = 0
    total_api_calls: int = 0
    total_tokens_used: Optional[int] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    user_satisfaction_score: Optional[float] = None
    task_completion_rate: Optional[float] = None

class WorkflowMetricsCreate(WorkflowMetricsBase):
    pass

class WorkflowMetricsUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    status: Optional[str] = None
    agents_involved: Optional[Dict[str, Any]] = None
    agent_count: Optional[int] = None
    total_tool_calls: Optional[int] = None
    total_api_calls: Optional[int] = None
    total_tokens_used: Optional[int] = None
    user_satisfaction_score: Optional[float] = None
    task_completion_rate: Optional[float] = None

class WorkflowMetricsInDB(WorkflowMetricsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: uuid.UUID
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None

class WorkflowMetricsResponse(WorkflowMetricsInDB):
    pass

class SessionMetricsBase(BaseModel):
    session_id: str
    start_time: datetime
    user_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    agents_used: Optional[Dict[str, Any]] = None
    unique_agents_count: int = 0
    average_response_time_ms: Optional[float] = None
    total_tokens_used: Optional[int] = None
    is_active: bool = True

class SessionMetricsCreate(SessionMetricsBase):
    pass

class SessionMetricsUpdate(BaseModel):
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    total_queries: Optional[int] = None
    successful_queries: Optional[int] = None
    failed_queries: Optional[int] = None
    agents_used: Optional[Dict[str, Any]] = None
    unique_agents_count: Optional[int] = None
    average_response_time_ms: Optional[float] = None
    total_tokens_used: Optional[int] = None
    is_active: Optional[bool] = None

class SessionMetricsInDB(SessionMetricsBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None

class SessionMetricsResponse(SessionMetricsInDB):
    pass

class AgentUsageStats(BaseModel):
    agent_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_duration_ms: Optional[float] = None
    total_tool_calls: int = 0
    success_rate: float = 0.0
    last_used: Optional[datetime] = None

class ToolUsageStats(BaseModel):
    tool_name: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    average_duration_ms: Optional[float] = None
    success_rate: float = 0.0
    most_used_by_agent: Optional[str] = None

class WorkflowPerformanceStats(BaseModel):
    workflow_type: str
    total_workflows: int
    successful_workflows: int
    failed_workflows: int
    average_duration_ms: Optional[float] = None
    average_agent_count: float = 1.0
    success_rate: float = 0.0

class ErrorSummary(BaseModel):
    error_type: str
    count: int
    percentage: float
    most_affected_agent: Optional[str] = None
    most_affected_tool: Optional[str] = None

class SessionActivityStats(BaseModel):
    total_sessions: int
    active_sessions: int
    average_session_duration_ms: Optional[float] = None
    average_queries_per_session: float = 0.0
    total_queries: int
    successful_queries: int
    failed_queries: int
    query_success_rate: float = 0.0
