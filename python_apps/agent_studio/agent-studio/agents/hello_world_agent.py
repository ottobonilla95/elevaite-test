import json
from typing import Any

from .agent_base import Agent
from utils import agent_schema, client


@agent_schema
class HelloWorldAgent(Agent):
    def execute(self, **kwargs: Any) -> Any:
        """
        A simple Hello World agent that greets users with a friendly message.
        """
        tries = 0
        routing_options = "\n".join([f"{k}: {v}" for k, v in self.routing_options.items()])
        query = kwargs["query"]
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
                return json.dumps({"routing": "respond", "content": "Hello, World! I'm a simple greeting agent."})

            except Exception as e:
                print(f"Error: {e}")
            tries += 1

        # Default response if all retries fail
        return json.dumps({"routing": "respond", "content": "Hello, World! I'm a simple greeting agent."})
