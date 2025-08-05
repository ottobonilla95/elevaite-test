from typing import Any, List, Optional

from .agent_base import Agent


class CommandAgent(Agent):
    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chat_history: Optional[List[dict]] = None,
        enable_analytics: bool = True,  # CommandAgent enables analytics by default
        execution_id: Optional[str] = None,  # Allow custom execution_id
        **kwargs: Any,
    ) -> str:
        return super().execute(
            query=query,
            session_id=session_id,
            user_id=user_id,
            chat_history=chat_history,
            enable_analytics=enable_analytics,
            execution_id=execution_id,
            **kwargs,
        )

    def execute_stream(
        self, query: Any, chat_history: Any, dynamic_agent_store: Optional[dict] = None
    ) -> Any:
        """
        CommandAgent streaming execution - delegates to base class with analytics enabled.
        """
        return super().execute_stream(
            query=query,
            chat_history=chat_history,
            enable_analytics=True,  # CommandAgent enables analytics by default
            dynamic_agent_store=dynamic_agent_store,
        )
