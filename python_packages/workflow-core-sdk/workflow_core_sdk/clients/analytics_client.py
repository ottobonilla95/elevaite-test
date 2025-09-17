from typing import Any, Dict, Optional


class AnalyticsClient:
    """Interface for sending execution metrics/events to Analytics Service."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = base_url or ""

    async def send_event(self, event: Dict[str, Any]) -> None:
        """Send a single event (placeholder)."""
        raise NotImplementedError

    async def stream_events(self, events: "list[dict]") -> None:
        """Send a batch/stream of events (placeholder)."""
        raise NotImplementedError

