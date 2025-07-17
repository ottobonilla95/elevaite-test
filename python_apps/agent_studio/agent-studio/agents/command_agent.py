import json
from typing import Any, List, cast, Optional

from utils import client
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_message_tool_call_param import (
    ChatCompletionMessageToolCallParam,
)
from .agent_base import Agent
from .tools import tool_store
from . import agent_store


class CommandAgent(Agent):
    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chat_history: Optional[List[dict]] = None,
        enable_analytics: bool = True,  # CommandAgent enables analytics by default
        **kwargs: Any,
    ) -> str:
        return super().execute(
            query=query,
            session_id=session_id,
            user_id=user_id,
            chat_history=chat_history,
            enable_analytics=enable_analytics,
            **kwargs,
        )

    def execute_stream(
        self, query: Any, chat_history: Any, dynamic_agent_store: Optional[dict] = None
    ) -> Any:
        tries = 0
        tool_call_count = 0  # Track tool calls to prevent infinite loops
        max_tool_calls = 5  # Limit tool calls per conversation
        routing_options = "\n".join(
            [f"{k}: {v}" for k, v in self.routing_options.items()]
        )
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
            {"role": "system", "content": system_prompt}
        ]
        messages.append(
            {"role": "user", "content": f"Here is the chat history: {chat_history}"}
        )
        messages.append(
            {
                "role": "user",
                "content": "Read the context and chat history and then answer the query."
                + "\n\nHere is the query: "
                + query,
            }
        )

        while tries < self.max_retries:
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.functions,
                    temperature=self.temperature,
                    stream=False,
                )
                print("\n\nResponse: ", response)

                if (
                    response.choices[0].finish_reason == "tool_calls"
                    and response.choices[0].message.tool_calls is not None
                ):
                    # Check if we've exceeded max tool calls
                    if tool_call_count >= max_tool_calls:
                        yield f"Maximum tool calls ({max_tool_calls}) reached. Ending conversation.\n"
                        return

                    tool_call_count += 1
                    tool_calls = response.choices[0].message.tool_calls

                    messages.append(
                        {
                            "role": "assistant",
                            "tool_calls": cast(
                                List[ChatCompletionMessageToolCallParam], tool_calls
                            ),
                        },
                    )
                    for tool in tool_calls:
                        yield f"Agent Called: {tool.function.name}\n"
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name

                        # Use dynamic_agent_store if provided, otherwise fall back to imported agent_store
                        current_agent_store = (
                            dynamic_agent_store if dynamic_agent_store else agent_store
                        )

                        if function_name in current_agent_store:
                            result = current_agent_store[function_name](**arguments)
                        else:
                            result = tool_store[function_name](**arguments)

                        print(result)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "content": str(result),
                            }
                        )

                        try:
                            if isinstance(result, str):
                                parsed_result = json.loads(result)
                                yield parsed_result.get(
                                    "content", "Agent Responded"
                                ) + "\n"
                            else:
                                yield str(result) + "\n"
                        except json.JSONDecodeError:
                            yield str(result) + "\n"

                    print(f"✅ Processed all {len(tool_calls)} tool calls successfully")
                    # After processing all tool calls, continue the conversation to get assistant's final response
                    # The loop will continue and make another API call with the updated messages
                    # Increment tries to ensure conversation progresses and doesn't loop infinitely
                    tries += 1

                else:
                    if response.choices[0].message.content is None:
                        raise Exception("No content in response")
                    yield "Command Agent Responded\n"

                    try:
                        parsed_content = json.loads(response.choices[0].message.content)
                        yield parsed_content.get(
                            "content", "Command Agent Could Not Respond"
                        ) + "\n\n"
                    except json.JSONDecodeError:
                        yield response.choices[0].message.content + "\n\n"
                    return

            except Exception as e:
                print(f"Error: {e}")
                tries += 1

                if tries >= self.max_retries:
                    yield f"Error after {self.max_retries} attempts: {str(e)}\n"
                    return
