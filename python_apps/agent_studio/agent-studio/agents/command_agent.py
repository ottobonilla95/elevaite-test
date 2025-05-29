import json
from typing import Any, List, cast, Optional

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
from services.analytics_service import analytics_service
from db.database import get_db


class CommandAgent(Agent):
    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        This agent can call any agent, tool, or component. It can also call a router agent to call multiple agents.
        Enhanced with comprehensive analytics tracking.
        """
        # Get database session
        db = next(get_db())

        # Track the overall workflow
        workflow_type = "command_agent_orchestration"
        agents_involved = []

        # Start analytics tracking
        with analytics_service.track_workflow(
            workflow_type=workflow_type,
            agents_involved=agents_involved,
            session_id=session_id,
            user_id=user_id,
            db=db,
        ) as workflow_id:

            with analytics_service.track_agent_execution(
                agent_id=self.agent_id,
                agent_name="CommandAgent",
                query=query,
                session_id=session_id,
                user_id=user_id,
                correlation_id=str(workflow_id),
                db=db,
            ) as execution_id:

                tries = 0
                system_prompt = self.system_prompt.prompt
                tools_called = []
                api_calls_count = 0

                messages: List[ChatCompletionMessageParam] = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ]

                while tries < self.max_retries:
                    analytics_service.logger.info(
                        f"Command Agent attempt {tries + 1}/{self.max_retries}"
                    )

                    try:
                        # Track API call
                        api_calls_count += 1

                        response = client.chat.completions.create(
                            model="o3-mini",
                            messages=messages,
                            tools=self.functions,
                            tool_choice="auto",
                        )

                        analytics_service.logger.debug(
                            f"OpenAI API response received for execution {execution_id}"
                        )

                        if (
                            response.choices[0].finish_reason == "tool_calls"
                            and response.choices[0].message.tool_calls is not None
                        ):
                            tool_calls = response.choices[0].message.tool_calls
                            _message: ChatCompletionAssistantMessageParam = {
                                "role": "assistant",
                                "tool_calls": cast(
                                    List[ChatCompletionMessageToolCallParam], tool_calls
                                ),
                            }
                            messages.append(_message)

                            for tool in tool_calls:
                                analytics_service.logger.info(
                                    f"Executing tool: {tool.function.name}"
                                )

                                tool_id = tool.id
                                arguments = json.loads(tool.function.arguments)
                                function_name = tool.function.name

                                # Track tool usage
                                external_api = None
                                if function_name in ["web_search", "weather_forecast"]:
                                    external_api = function_name

                                with analytics_service.track_tool_usage(
                                    tool_name=function_name,
                                    execution_id=execution_id,
                                    input_data=arguments,
                                    external_api_called=external_api,
                                    db=db,
                                ) as usage_id:

                                    if function_name in agent_store:
                                        result = agent_store[function_name](**arguments)
                                        if function_name not in agents_involved:
                                            agents_involved.append(function_name)
                                    else:
                                        result = tool_store[function_name](**arguments)

                                    # Update tool metrics with output
                                    analytics_service.update_tool_metrics(
                                        usage_id=usage_id,
                                        output_data={
                                            "result": str(result)[:1000]
                                        },  # Truncate for storage
                                        db=db,
                                    )

                                # Track tool call for execution metrics
                                tools_called.append(
                                    {
                                        "tool_name": function_name,
                                        "arguments": arguments,
                                        "usage_id": str(usage_id),
                                    }
                                )

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

                            # Update execution metrics before returning
                            analytics_service.update_execution_metrics(
                                execution_id=execution_id,
                                response=response.choices[0].message.content,
                                tools_called=tools_called,
                                tool_count=len(tools_called),
                                retry_count=tries,
                                api_calls_count=api_calls_count,
                                db=db,
                            )

                            return response.choices[0].message.content

                    except Exception as e:
                        analytics_service.logger.error(
                            f"Error in Command Agent execution: {str(e)}"
                        )
                        tries += 1
                        if tries >= self.max_retries:
                            # Update execution metrics with final retry count
                            analytics_service.update_execution_metrics(
                                execution_id=execution_id,
                                tools_called=tools_called,
                                tool_count=len(tools_called),
                                retry_count=tries,
                                api_calls_count=api_calls_count,
                                db=db,
                            )
                            raise Exception(f"Max retries reached: {str(e)}")

                # This shouldn't be reached, but just in case
                raise Exception("Unexpected end of execution loop")

    def execute_stream(self, query: Any, chat_history: Any) -> Any:
        """
        Ask the agent anything related to arithmetic, customer orders numbers or web search and it will try to answer it.
        You can ask it multiple questions at once. No need to ask one question at a time. You can ask it for multiple customer ids, multiple arithmetic questions, or multiple web search queries.
        """

        tries = 0
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
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=self.functions,
                    stream=False,
                )
                print("\n\nResponse: ", response)
                if (
                    response.choices[0].finish_reason == "tool_calls"
                    and response.choices[0].message.tool_calls is not None
                ):
                    tool_calls = response.choices[0].message.tool_calls[:1]
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
                        result = agent_store[function_name](**arguments)
                        print(result)
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "content": str(result),
                            }
                        )
                        yield json.loads(result).get(
                            "content", "Agent Responded"
                        ) + "\n"

                else:
                    if response.choices[0].message.content is None:
                        raise Exception("No content in response")
                    yield "Command Agent Responded\n"
                    yield (
                        json.loads(response.choices[0].message.content).get(
                            "content", "Command Agent Could Not Respond"
                        )
                        + "\n\n"
                    )  # Stream the final response
                    return

            except Exception as e:
                print(f"Error: {e}")
            tries += 1
