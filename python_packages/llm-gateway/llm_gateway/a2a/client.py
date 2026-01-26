"""A2A Client Service for communicating with external A2A agents.

Uses the official a2a-sdk to connect to and communicate with A2A-compliant agents.
"""

import logging
import uuid
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from a2a.client import (
    A2ACardResolver,
    ClientCallInterceptor,
    ClientConfig,
    ClientFactory,
)
from a2a.types import AgentCard, Message, Part, Role, TaskState, TextPart

from .auth import create_auth_interceptor
from .types import A2AAgentInfo, A2AMessageRequest, A2AMessageResponse, A2ATaskInfo


logger = logging.getLogger(__name__)


def _create_message(
    content: str, context_id: str | None = None, task_id: str | None = None
) -> Message:
    """Create an A2A Message with the given content."""
    return Message(
        message_id=str(uuid.uuid4()),
        role=Role.user,
        parts=[Part(root=TextPart(text=content))],
        context_id=context_id,
        task_id=task_id,
    )


class A2AClientService:
    """Service for communicating with A2A agents.

    This service wraps the official a2a-sdk to provide a simplified interface
    for sending messages to external A2A agents and handling responses.
    """

    def __init__(self, default_timeout: float = 30.0):
        """Initialize the A2A client service.

        Args:
            default_timeout: Default timeout for HTTP requests in seconds.
        """
        self._default_timeout = default_timeout
        self._card_cache: Dict[str, AgentCard] = {}
        self._interceptor_cache: Dict[str, ClientCallInterceptor] = {}

    def _get_interceptors(
        self, agent: A2AAgentInfo
    ) -> Optional[List[ClientCallInterceptor]]:
        """Get authentication interceptors for an agent.

        Args:
            agent: Agent connection information with auth config.

        Returns:
            List of interceptors, or None if no auth is configured.
        """
        if not agent.auth or agent.auth.auth_type == "none":
            return None

        # Cache interceptors by base_url to reuse OAuth2 token state
        cache_key = agent.base_url
        if cache_key not in self._interceptor_cache:
            interceptor = create_auth_interceptor(agent.auth)
            if interceptor:
                self._interceptor_cache[cache_key] = interceptor

        interceptor = self._interceptor_cache.get(cache_key)
        return [interceptor] if interceptor else None

    async def get_agent_card(
        self,
        agent: A2AAgentInfo,
        force_refresh: bool = False,
    ) -> AgentCard:
        """Fetch and cache an agent's card.

        Args:
            agent: Agent connection information.
            force_refresh: If True, bypass cache and fetch fresh card.

        Returns:
            The agent's AgentCard.
        """
        cache_key = agent.base_url
        if not force_refresh and cache_key in self._card_cache:
            return self._card_cache[cache_key]

        timeout = httpx.Timeout(agent.timeout or self._default_timeout)
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            resolver = A2ACardResolver(http_client, agent.base_url)
            card = await resolver.get_agent_card(
                relative_card_path=agent.agent_card_url,
            )

        self._card_cache[cache_key] = card
        logger.info(f"Fetched agent card for {card.name} at {agent.base_url}")
        return card

    async def send_message(
        self,
        agent: A2AAgentInfo,
        request: A2AMessageRequest,
    ) -> A2AMessageResponse:
        """Send a message to an A2A agent and return the response.

        Args:
            agent: Agent connection information.
            request: The message request to send.

        Returns:
            The agent's response.
        """
        config = ClientConfig(
            streaming=False,
            polling=True,
            accepted_output_modes=request.accepted_output_modes or ["text"],
        )

        interceptors = self._get_interceptors(agent)
        client = await ClientFactory.connect(
            agent.base_url,
            client_config=config,
            interceptors=interceptors,
        )
        message = _create_message(request.content, request.context_id, request.task_id)

        response = A2AMessageResponse()
        async for event in client.send_message(message):
            response = self._process_event(event, response)
        return response

    async def stream_message(
        self,
        agent: A2AAgentInfo,
        request: A2AMessageRequest,
    ) -> AsyncIterator[A2AMessageResponse]:
        """Send a message to an A2A agent and stream responses."""
        config = ClientConfig(
            streaming=True,
            accepted_output_modes=request.accepted_output_modes or ["text"],
        )

        interceptors = self._get_interceptors(agent)
        client = await ClientFactory.connect(
            agent.base_url,
            client_config=config,
            interceptors=interceptors,
        )
        message = _create_message(request.content, request.context_id, request.task_id)

        response = A2AMessageResponse()
        async for event in client.send_message(message):
            response = self._process_event(event, response)
            yield response

    def _process_event(
        self,
        event: Any,
        response: A2AMessageResponse,
    ) -> A2AMessageResponse:
        """Process an event from the A2A agent and update the response.

        Args:
            event: The event from the agent (Task, Message, or update event).
            response: The current response being built.

        Returns:
            Updated response.
        """
        if isinstance(event, Message):
            # Direct message response
            text_parts = []
            for part in event.parts or []:
                # a2a-sdk uses discriminated unions - access data via .root
                if hasattr(part.root, "text"):
                    text_parts.append(part.root.text)  # type: ignore[attr-defined]
                elif hasattr(part.root, "data"):
                    response.artifacts.append({"type": "data", "data": part.root.data})  # type: ignore[attr-defined]
                elif hasattr(part.root, "file"):
                    response.artifacts.append({"type": "file", "file": part.root.file})  # type: ignore[attr-defined]
            response.content = "".join(text_parts) if text_parts else response.content
            response.raw_response = (
                event.model_dump() if hasattr(event, "model_dump") else None
            )

        elif isinstance(event, tuple):
            # (Task, UpdateEvent) pair - we only use the Task
            task, _ = event
            if task:
                response.task = A2ATaskInfo(
                    task_id=str(task.id),
                    state=task.status.state if task.status else "unknown",
                    context_id=str(task.context_id) if task.context_id else None,
                    message=task.status.message if task.status else None,
                )
                response.is_complete = task.status and task.status.state in (
                    TaskState.completed,
                    TaskState.failed,
                    TaskState.canceled,
                )
                # Extract content from task artifacts
                for artifact in task.artifacts or []:
                    artifact_data: Dict[str, Any] = {
                        "id": artifact.artifact_id,
                        "name": artifact.name,
                        "parts": [],
                    }
                    for part in artifact.parts or []:
                        # a2a-sdk uses discriminated unions - access data via .root
                        if hasattr(part.root, "text"):
                            if not response.content:
                                response.content = part.root.text  # type: ignore[attr-defined]
                            artifact_data["parts"].append(
                                {"type": "text", "text": part.root.text}
                            )  # type: ignore[attr-defined]
                        elif hasattr(part.root, "data"):
                            artifact_data["parts"].append(
                                {"type": "data", "data": part.root.data}
                            )  # type: ignore[attr-defined]
                        elif hasattr(part.root, "file"):
                            artifact_data["parts"].append(
                                {"type": "file", "file": part.root.file}
                            )  # type: ignore[attr-defined]
                    response.artifacts.append(artifact_data)

        return response

    def _extract_status_message(self, status_message: Message | None) -> str | None:
        """Extract text content from a status Message object."""
        if not status_message or not status_message.parts:
            return None
        for part in status_message.parts:
            if hasattr(part.root, "text"):
                return part.root.text  # type: ignore[return-value]
        return None

    async def get_task_status(self, agent: A2AAgentInfo, task_id: str) -> A2ATaskInfo:
        """Get the current status of a task."""
        from a2a.types import TaskQueryParams

        interceptors = self._get_interceptors(agent)
        client = await ClientFactory.connect(
            agent.base_url,
            client_config=ClientConfig(streaming=False),
            interceptors=interceptors,
        )
        task = await client.get_task(TaskQueryParams(id=task_id))

        return A2ATaskInfo(
            task_id=str(task.id),
            state=task.status.state if task.status else "unknown",
            context_id=str(task.context_id) if task.context_id else None,
            message=self._extract_status_message(
                task.status.message if task.status else None
            ),
        )

    async def cancel_task(self, agent: A2AAgentInfo, task_id: str) -> A2ATaskInfo:
        """Cancel a running task."""
        from a2a.types import TaskIdParams

        interceptors = self._get_interceptors(agent)
        client = await ClientFactory.connect(
            agent.base_url,
            client_config=ClientConfig(streaming=False),
            interceptors=interceptors,
        )
        task = await client.cancel_task(TaskIdParams(id=task_id))

        return A2ATaskInfo(
            task_id=str(task.id),
            state=task.status.state if task.status else "canceled",
            context_id=str(task.context_id) if task.context_id else None,
            message=self._extract_status_message(
                task.status.message if task.status else None
            ),
        )
