import json
from typing import Any, List, cast
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_message_param import ChatCompletionToolMessageParam

from .agent_base import Agent
from utils import agent_schema, client

from tools import tool_store


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
            print(tries)
            # print("\n\nMessage: ",messages)
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    # functions=self.functions,
                    tools=self.functions if self.functions else [],
                    # parallel_tool_calls=True,
                    tool_choice="auto",
                )
                # print("\n\nResponse: ",response)
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
                return "Response could not be processed"
            tries += 1
