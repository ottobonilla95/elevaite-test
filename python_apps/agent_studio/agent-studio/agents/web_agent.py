from typing import Any

from .agent_base import Agent
from utils import agent_schema


@agent_schema
class WebAgent(Agent):
    def execute(self, query: str, **kwargs: Any) -> Any:
        """
        Ask the agent anything related to arithmetic, customer orders numbers or web search and it will try to answer it.
        You can ask it multiple questions at once. No need to ask one question at a time. You can ask it for multiple customer ids, multiple arithmetic questions, or multiple web search queries.

        You can ask:
        query : what are the customer order numbers for customer id 1111 and 2222.
        query : what is the sum of 2 and 3, and sum of 12 and 13.
        query : what is the latest news on Toshiba and Apple.
        query : what is the sum of 12 and 13, and web results for "latest news on Toshiba.
        """
        # Use the common LLM execution pattern from base class
        return self._execute_with_llm(query=query, model="gpt-4o-mini", temperature=0.7, **kwargs)
