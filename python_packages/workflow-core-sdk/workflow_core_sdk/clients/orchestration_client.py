from typing import Any, Dict, Optional


class OrchestrationClient:
    """Lightweight client to talk to orchestration service APIs."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or ""

    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    async def report_status(self, execution_id: str, status: str) -> None:
        raise NotImplementedError
