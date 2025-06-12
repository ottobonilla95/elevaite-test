from typing import Any, Dict, List, Optional

from .agent_base import Agent
from utils import agent_schema


@agent_schema
class WebAgent(Agent):
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
        Ask the agent anything related to arithmetic, customer orders numbers or web search and it will try to answer it.
        You can ask it multiple questions at once. No need to ask one question at a time. You can ask it for multiple customer ids, multiple arithmetic questions, or multiple web search queries.

        You can ask:
        query : what are the customer order numbers for customer id 1111 and 2222.
        query : what is the sum of 2 and 3, and sum of 12 and 13.
        query : what is the latest news on Toshiba and Apple.
        query : what is the sum of 12 and 13, and web results for "latest news on Toshiba.
        """
        return super().execute(
            query=query,
            session_id=session_id,
            user_id=user_id,
            chat_history=chat_history,
            enable_analytics=enable_analytics,
            **kwargs,
        )
