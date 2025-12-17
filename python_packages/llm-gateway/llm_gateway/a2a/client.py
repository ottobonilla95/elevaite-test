"""A2A Client Service for communicating with external A2A agents.

Uses the official a2a-sdk to connect to and communicate with A2A-compliant agents.
"""

import logging
from typing import Any, AsyncIterator, Dict, Optional

import httpx
from a2a.client import (
    A2ACardResolver,
    Client,
    ClientConfig,
    ClientFactory,
    create_text_message_object,
)
from a2a.types import AgentCard, Message, Task, TaskState

from .types import (
    A2AAgentInfo,
    A2AMessageRequest,
    A2AMessageResponse,
    A2ATaskInfo,
)


logger = logging.getLogger(__name__)


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

    async def create_client(
        self,
        agent: A2AAgentInfo,
        streaming: bool = True,
    ) -> Client:
        """Create an A2A client for the specified agent.

        Args:
            agent: Agent connection information.
            streaming: Whether to enable streaming support.

        Returns:
            An A2A Client instance.
        """
        config = ClientConfig(
            streaming=streaming,
            accepted_output_modes=["text", "file", "data"],
        )

        # Get the agent card first
        card = await self.get_agent_card(agent)

        # Create client using the factory
        timeout = httpx.Timeout(agent.timeout or self._default_timeout)
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            config.httpx_client = http_client
            factory = ClientFactory(config)
            client = factory.create(card)

        return client

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

        timeout = httpx.Timeout(agent.timeout or self._default_timeout)
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            client = await ClientFactory.connect(
                agent.base_url,
                client_config=config,
            )

            # Create message using SDK helper
            message = create_text_message_object(
                content=request.content,
                context_id=request.context_id,
                task_id=request.task_id,
            )

            # Send message and collect response
            response = A2AMessageResponse()
            async for event in client.send_message(message):
                response = self._process_event(event, response)

            return response

    async def stream_message(
        self,
        agent: A2AAgentInfo,
        request: A2AMessageRequest,
    ) -> AsyncIterator[A2AMessageResponse]:
        """Send a message to an A2A agent and stream responses.

        Args:
            agent: Agent connection information.
            request: The message request to send.

        Yields:
            Incremental response updates from the agent.
        """
        config = ClientConfig(
            streaming=True,
            accepted_output_modes=request.accepted_output_modes or ["text"],
        )

        timeout = httpx.Timeout(agent.timeout or self._default_timeout)
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            client = await ClientFactory.connect(
                agent.base_url,
                client_config=config,
            )

            message = create_text_message_object(
                content=request.content,
                context_id=request.context_id,
                task_id=request.task_id,
            )

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
                    text_parts.append(part.root.text)
                elif hasattr(part.root, "data"):
                    response.artifacts.append({"type": "data", "data": part.root.data})
                elif hasattr(part.root, "file"):
                    response.artifacts.append({"type": "file", "file": part.root.file})
            response.content = "".join(text_parts) if text_parts else response.content
            response.raw_response = event.model_dump() if hasattr(event, "model_dump") else None

        elif isinstance(event, tuple):
            # (Task, UpdateEvent) pair
            task, update = event
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
                    artifact_data = {
                        "id": artifact.artifact_id,
                        "name": artifact.name,
                        "parts": [],
                    }
                    for part in artifact.parts or []:
                        # a2a-sdk uses discriminated unions - access data via .root
                        if hasattr(part.root, "text"):
                            if not response.content:
                                response.content = part.root.text
                            artifact_data["parts"].append({"type": "text", "text": part.root.text})
                        elif hasattr(part.root, "data"):
                            artifact_data["parts"].append({"type": "data", "data": part.root.data})
                        elif hasattr(part.root, "file"):
                            artifact_data["parts"].append({"type": "file", "file": part.root.file})
                    response.artifacts.append(artifact_data)

        return response

    async def get_task_status(
        self,
        agent: A2AAgentInfo,
        task_id: str,
    ) -> A2ATaskInfo:
        """Get the current status of a task.

        Args:
            agent: Agent connection information.
            task_id: The task ID to query.

        Returns:
            Current task information.
        """
        from a2a.types import TaskQueryParams

        config = ClientConfig(streaming=False)
        timeout = httpx.Timeout(agent.timeout or self._default_timeout)
        async with httpx.AsyncClient(timeout=timeout) as _:
            client = await ClientFactory.connect(
                agent.base_url,
                client_config=config,
            )

            params = TaskQueryParams(id=task_id)
            task = await client.get_task(params)

            return A2ATaskInfo(
                task_id=str(task.id),
                state=task.status.state if task.status else "unknown",
                context_id=str(task.context_id) if task.context_id else None,
                message=task.status.message if task.status else None,
            )

    async def cancel_task(
        self,
        agent: A2AAgentInfo,
        task_id: str,
    ) -> A2ATaskInfo:
        """Cancel a running task.

        Args:
            agent: Agent connection information.
            task_id: The task ID to cancel.

        Returns:
            Updated task information.
        """
        from a2a.types import TaskIdParams

        config = ClientConfig(streaming=False)
        timeout = httpx.Timeout(agent.timeout or self._default_timeout)
        async with httpx.AsyncClient(timeout=timeout) as _:
            client = await ClientFactory.connect(
                agent.base_url,
                client_config=config,
            )

            params = TaskIdParams(id=task_id)
            task = await client.cancel_task(params)

            return A2ATaskInfo(
                task_id=str(task.id),
                state=task.status.state if task.status else "canceled",
                context_id=str(task.context_id) if task.context_id else None,
                message=task.status.message if task.status else None,
            )
