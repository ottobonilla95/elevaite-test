from typing import Any, Dict, Optional, TypedDict


class ExecutionSummary(TypedDict, total=False):
    execution_id: str
    workflow_id: Optional[str]
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    execution_time_seconds: Optional[float]
    current_step: Optional[str]
    total_steps: Optional[int]
    completed_steps: Optional[int]
    failed_steps: Optional[int]
    pending_steps: Optional[int]
    user_context: Optional[Dict[str, Any]]

