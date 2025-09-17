from typing import Any, Dict, Optional, TypedDict


class ExecutionEvent(TypedDict, total=False):
    kind: str  # e.g. status|step|error
    execution_id: str
    workflow_id: Optional[str]
    status: Optional[str]
    step_id: Optional[str]
    error: Optional[str]
    payload: Optional[Dict[str, Any]]

