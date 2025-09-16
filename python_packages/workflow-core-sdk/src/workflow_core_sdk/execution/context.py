from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionContext:
    """Lightweight representation of workflow execution state.
    Concrete fields/methods will be migrated from the PoC.
    """

    execution_id: str
    workflow_id: Optional[str] = None
    status: str = "pending"
    step_results: Dict[str, Any] = field(default_factory=dict)
    global_variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    completed_steps: List[str] = field(default_factory=list)
    failed_steps: List[str] = field(default_factory=list)

    def get_execution_summary(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "status": self.status,
            "completed_steps": len(self.completed_steps),
            "failed_steps": len(self.failed_steps),
        }

