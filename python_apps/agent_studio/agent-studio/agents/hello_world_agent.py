import json
from typing import Any, Dict, Optional, List, Literal
import uuid
from datetime import datetime

from .agent_base import Agent
from utils import agent_schema, client


@agent_schema
class HelloWorldAgent(Agent):
    def __init__(
        self,
        failure_strategies: Optional[List[str]],
        name: str,
        agent_id: uuid.UUID,
        system_prompt: Any,
        persona: Optional[str],
        functions: List[Any],
        routing_options: Dict[str, str],
        parent_agent: Optional[uuid.UUID] = None,
        short_term_memory: bool = False,
        long_term_memory: bool = False,
        reasoning: bool = False,
        input_type: Optional[List[Literal["text", "voice", "image"]]] = [
            "text",
            "voice",
        ],
        output_type: Optional[List[Literal["text", "voice", "image"]]] = [
            "text",
            "voice",
        ],
        response_type: Optional[
            Literal["json", "yaml", "markdown", "HTML", "None"]
        ] = "json",
        # Execution parameters
        max_retries: int = 3,
        timeout: Optional[int] = None,
        deployed: bool = False,
        status: Literal["active", "paused", "terminated"] = "active",
        priority: Optional[int] = None,
        # Logging and monitoring
        session_id: Optional[str] = None,
        last_active: Optional[datetime] = None,
        collaboration_mode: Optional[
            Literal["single", "team", "parallel", "sequential"]
        ] = "single",  # Multi-agent behavior
        stream_name: Optional[str] = "agent:hello_world",
    ):
        super().__init__(
            agent_id=agent_id,
            collaboration_mode=collaboration_mode,
            deployed=deployed,
            failure_strategies=failure_strategies,
            functions=functions,
            input_type=input_type,
            last_active=last_active,
            long_term_memory=long_term_memory,
            max_retries=max_retries,
            name=name,
            output_type=output_type,
            parent_agent=parent_agent,
            persona=persona,
            reasoning=reasoning,
            response_type=response_type,
            routing_options=routing_options,
            short_term_memory=short_term_memory,
            session_id=session_id,
            status=status,
            system_prompt=system_prompt,
            timeout=timeout,
            priority=priority,
            stream_name=stream_name,
        )

        # Initialize Redis communication
        self.initialize_redis_communication()

        # Register message handlers for specific message types
        self.message_handlers = {
            "query": self._handle_query,
            "command": self._handle_command,
        }

    def _handle_query(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle query messages."""
        query = data.get("query", "")
        result = self._execute({"query": query})
        return {"result": result}

    def _handle_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle command messages."""
        command = data.get("command", "")
        print(f"Executing command: {command}")
        # Process command logic here
        return {"status": "command executed", "command": command}

    def _execute(self, payload: Dict[str, Any]) -> str:
        """
        A simple Hello World agent that greets users with a friendly message.
        """
        tries = 0
        routing_options = "\n".join(
            [f"{k}: {v}" for k, v in self.routing_options.items()]
        )
        query = payload["query"]
        print(f"Received query: {query}")
        system_prompt = (
            self.system_prompt.prompt
            + f"""
        Here are the routing options:
        {routing_options}

        Your response should be in the format:
        {{ "routing": "respond", "content": "Your hello world greeting message."}}

        """
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        while tries < self.max_retries:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                )

                if response.choices[0].message.content is not None:
                    return response.choices[0].message.content
                return json.dumps(
                    {
                        "routing": "respond",
                        "content": "Hello, World! I'm a simple greeting agent.",
                    }
                )

            except Exception as e:
                print(f"Error: {e}")
                # Return a default response if OpenAI API is not available
                if "openai" in str(e).lower() or "api key" in str(e).lower():
                    return json.dumps(
                        {
                            "routing": "respond",
                            "content": "Hello, World! I'm a simple greeting agent.",
                        }
                    )
            tries += 1

        # Default response if all retries fail
        return json.dumps(
            {
                "routing": "respond",
                "content": "Hello, World! I'm a simple greeting agent.",
            }
        )

    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        enable_analytics: bool = False,
        **kwargs: Any,
    ) -> str:
        return super().execute(
            query=query,
            session_id=session_id,
            user_id=user_id,
            chat_history=chat_history,
            enable_analytics=enable_analytics,
            **kwargs,
        )
