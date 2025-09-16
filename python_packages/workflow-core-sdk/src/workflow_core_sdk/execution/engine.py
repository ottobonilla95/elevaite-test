from typing import Any, Dict, Optional


class WorkflowEngine:
    """Minimal engine interface. Implementations will be extracted from the PoC."""

    async def execute(
        self,
        workflow_config: Dict[str, Any],
        *,
        execution_id: str,
        trigger_payload: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
        wait: bool = False,
    ) -> Dict[str, Any]:
        """Execute a workflow configuration. Returns normalized result dict.
        Placeholder method to be implemented by extraction.
        """
        raise NotImplementedError

    async def resume(
        self,
        execution_id: str,
        step_id: str,
        decision_output: Dict[str, Any],
    ) -> bool:
        """Resume a paused execution by injecting decision output for a waiting step."""
        raise NotImplementedError

