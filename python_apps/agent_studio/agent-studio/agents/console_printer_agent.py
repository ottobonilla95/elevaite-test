import json
from typing import Any, Dict, List, Literal, cast
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_message_param import ChatCompletionToolMessageParam

from pydantic import BaseModel

from .agent_base import Agent
from utils import agent_schema, client

from tools import tool_store


class ConsolePrinterAgentInput(BaseModel):
    query: str


@agent_schema
class ConsolePrinterAgent(Agent):
    def execute(self, query: str, **kwargs: ConsolePrinterAgentInput) -> Any:
        """
        This agent prints the input to the console.
        """
        # query = kwargs["query"]
        tries = 0
        routing_options = "\n".join([f"{k}: {v}" for k, v in self.routing_options.items()])
        system_prompt = (
            self.system_prompt.prompt
            + f"""
        Here are the routing options:
        {routing_options}

        Your response should be in the format:
        {{ "routing": "respond", "content": "The answer to the query."}}

        """
        )
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]
        while tries < self.max_retries:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=self.functions,
                    stream=False,
                )
                if response.choices[0].finish_reason == "tool_calls" and response.choices[0].message.tool_calls is not None:
                    tool_calls = response.choices[0].message.tool_calls
                    messages.append(
                        cast(
                            ChatCompletionMessageParam,
                            {"role": "assistant", "tool_calls": cast(List[ChatCompletionToolMessageParam], tool_calls)},
                        )
                    )
                    for tool in tool_calls:
                        print(tool.function.name)
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        result = tool_store[function_name](**arguments)
                        print(result)
                        messages.append(
                            cast(
                                ChatCompletionMessageParam,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_id,
                                    "content": str(result),
                                },
                            )
                        )

                else:
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
            tries += 1
