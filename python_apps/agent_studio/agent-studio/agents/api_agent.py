from typing import Any

from .agent_base import Agent
from utils import agent_schema


@agent_schema
class APIAgent(Agent):
    def execute(self, **kwargs: Any) -> Any:
        """
        Ask the agent anything related to the APIs. It can call any of the following APIs and get the results for you.

        Valid APIs:
        1. Weather API - to answer any weather related queries for a city.
        """
        query = kwargs["query"]

        # Use the common LLM execution pattern from base class
        return self._execute_with_llm(query=query, model="gpt-4o-mini", temperature=0.7, **kwargs)
