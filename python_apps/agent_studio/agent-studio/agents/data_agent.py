from typing import Any, Dict, List, Optional

from .agent_base import Agent
from utils import agent_schema


@agent_schema
class DataAgent(Agent):
    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        enable_analytics: bool = False,
        **kwargs: Any,
    ) -> str:
        """
        Ask the agent anything related to the database. It can fetch data from the database, or update the database. It can also do some reasoning based on the data in the database.
        The data contains customer ID, Order numbers and location in each row.
        """
        return super().execute(
            query=query,
            session_id=session_id,
            user_id=user_id,
            chat_history=chat_history,
            enable_analytics=enable_analytics,
            **kwargs,
        )
