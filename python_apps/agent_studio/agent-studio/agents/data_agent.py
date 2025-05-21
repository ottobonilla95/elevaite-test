import json
from typing import Any

from .agent_base import Agent
from utils import agent_schema, client

from tools import tool_store


@agent_schema
class DataAgent(Agent):
    def execute(self, **kwargs: Any) -> Any:
        """
        Ask the agent anything related to the database. It can fetch data from the database, or update the database. It can also do some reasoning based on the data in the database.
        The data contains customer ID, Order numbers and location in each row.
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
        {{ "routing": "respond", "content": "The answer to the query."}}

        """
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        while tries < self.max_retries:
            print(tries)
            # print("\n\nMessage: ",messages)
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    # functions=self.functions,
                    tools=self.functions,
                    # parallel_tool_calls=True,
                    tool_choice="auto",
                )
                # print("\n\nResponse: ",response)
                if response.choices[0].finish_reason == "tool_calls" and response.choices[0].message.tool_calls is not None:
                    tool_calls = response.choices[0].message.tool_calls
                    messages += [
                        {"role": "assistant", "tool_calls": tool_calls},
                    ]
                    for tool in tool_calls:
                        print(tool.function.name)
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        result = tool_store[function_name](**arguments)
                        print(result)
                        messages += [
                            {
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "content": str(result),
                            }
                        ]

                else:
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
            tries += 1
