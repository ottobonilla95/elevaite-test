from typing import Any

from .agent_base import Agent
from utils import agent_schema


@agent_schema
class DataAgent(Agent):
    def execute(self, query: str, **kwargs: Any) -> Any:
        """
        Ask the agent anything related to the database. It can fetch data from the database, or update the database. It can also do some reasoning based on the data in the database.
        The data contains customer ID, Order numbers and location in each row.
        """
        # Use the common LLM execution pattern from base class
        return self._execute_with_llm(query=query, model="gpt-4o-mini", temperature=0.7, **kwargs)
