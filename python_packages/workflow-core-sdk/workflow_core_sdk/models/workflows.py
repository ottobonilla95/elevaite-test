from typing import Any, Dict, List, Optional, TypedDict


class StepConfig(TypedDict, total=False):
    step_id: str
    step_type: str
    depends_on: List[str]
    step_order: Optional[int]
    config: Dict[str, Any]


class WorkflowConfig(TypedDict, total=False):
    workflow_id: Optional[str]
    name: Optional[str]
    steps: List[StepConfig]
    trigger: Dict[str, Any]
    metadata: Dict[str, Any]
