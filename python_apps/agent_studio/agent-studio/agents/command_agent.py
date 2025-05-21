import json
from typing import Any, List, cast

from utils import client
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)
from openai.types.chat.chat_completion_message_tool_call_param import (
    ChatCompletionMessageToolCallParam,
)
from .agent_base import Agent
from tools import tool_store
from . import agent_store


class CommandAgent(Agent):
    def execute(self, **kwargs: Any) -> str:
        """
        This agent can call any agent, tool, or component. It can also call a router agent to call multiple agents.
        """
        tries = 0
        system_prompt = self.system_prompt.prompt
        query = kwargs["query"]

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]

        while tries < self.max_retries:
            print("\n\nCommand Agent Tries: ", tries)
            try:
                response = client.chat.completions.create(
                    model="o3-mini",
                    messages=messages,
                    # temperature=float(self.system_prompt.hyper_parameters["temperature"]),
                    # functions=self.functions,
                    tools=self.functions,
                    # parallel_tool_calls=True,
                    tool_choice="auto",
                )
                print("\n\nResponse: ", response)
                if response.choices[0].finish_reason == "tool_calls" and response.choices[0].message.tool_calls is not None:
                    tool_calls = response.choices[0].message.tool_calls
                    _message: ChatCompletionAssistantMessageParam = {
                        "role": "assistant",
                        "tool_calls": cast(List[ChatCompletionMessageToolCallParam], tool_calls),
                    }
                    messages.append(_message)
                    for tool in tool_calls:
                        print("\n\nAgent Called: ", tool.function.name)
                        print(tool.function.arguments)
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        if function_name in agent_store:
                            result = agent_store[function_name](**arguments)
                        else:
                            result = tool_store[function_name](**arguments)
                        # print(result)
                        agent_response = json.loads(result)  # noqa: F841
                        # if agent_response["routing"] == "respond":
                        #     return agent_response["content"]
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "content": str(result),
                            }
                        )

                else:
                    if response.choices[0].message.content is None:
                        raise Exception("No content in response")
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
            tries += 1
        raise Exception("Max retries reached")

    def execute_stream(self, query: Any, chat_history: Any) -> Any:
        """
        Ask the agent anything related to arithmetic, customer orders numbers or web search and it will try to answer it.
        You can ask it multiple questions at once. No need to ask one question at a time. You can ask it for multiple customer ids, multiple arithmetic questions, or multiple web search queries.
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
        messages: List[ChatCompletionMessageParam] = [{"role": "system", "content": system_prompt}]
        messages.append({"role": "user", "content": f"Here is the chat history: {chat_history}"})
        messages.append(
            {
                "role": "user",
                "content": "Read the context and chat history and then answer the query." + "\n\nHere is the query: " + query,
            }
        )
        while tries < self.max_retries:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=self.functions,
                    stream=False,
                )
                print("\n\nResponse: ", response)
                if response.choices[0].finish_reason == "tool_calls" and response.choices[0].message.tool_calls is not None:
                    tool_calls = response.choices[0].message.tool_calls[:1]
                    messages.append(
                        {
                            "role": "assistant",
                            "tool_calls": cast(List[ChatCompletionMessageToolCallParam], tool_calls),
                        },
                    )
                    for tool in tool_calls:
                        yield f"Agent Called: {tool.function.name}\n"
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        result = agent_store[function_name](**arguments)
                        print(result)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "content": str(result),
                            }
                        )
                        yield json.loads(result).get("content", "Agent Responded") + "\n"

                else:
                    if response.choices[0].message.content is None:
                        raise Exception("No content in response")
                    yield "Command Agent Responded\n"
                    yield (
                        json.loads(response.choices[0].message.content).get("content", "Command Agent Could Not Respond")
                        + "\n\n"
                    )  # Stream the final response
                    return

            except Exception as e:
                print(f"Error: {e}")
            tries += 1
