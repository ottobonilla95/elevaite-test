from tools import weather_forecast
from data_classes import Agent
from utils import agent_schema
from typing import Any, List, cast
import json
from tools import tool_store
from utils import client
from datetime import datetime
import uuid
from tools import web_search, tool_schemas
from prompts import web_agent_system_prompt, api_agent_system_prompt, data_agent_system_prompt
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_assistant_message_param import ChatCompletionAssistantMessageParam
from openai.types.chat.chat_completion_message_tool_call_param import ChatCompletionMessageToolCallParam


@agent_schema
class WebAgent(Agent):
    def execute(self, **kwargs: Any) -> Any:
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
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]

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
                        messages += [{"role": "tool", "tool_call_id": tool_id, "content": str(result)}]

                else:
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
                return "Response could not be processed"
            tries += 1


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
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]
        )
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]

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
                        messages += [{"role": "tool", "tool_call_id": tool_id, "content": str(result)}]

                else:
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
            tries += 1


@agent_schema
class APIAgent(Agent):
    def execute(self, **kwargs: Any) -> Any:
        """
        Ask the agent anything related to the APIs. It can call any of the following APIs and get the results for you.

        Valid APIs:
        1. Weather API - to answer any weather related queries for a city.
        """
        query = kwargs["query"]
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
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]

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
                        messages += [{"role": "tool", "tool_call_id": tool_id, "content": str(result)}]

                else:
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
            tries += 1


web_agent = WebAgent(
    name="WebSearchAgent",
    agent_id=uuid.uuid4(),
    system_prompt=web_agent_system_prompt,
    persona="Helper",
    functions=[web_search.openai_schema],
    routing_options={
        "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
        "respond": "If you think you have the answer, you can stop here.",
        "give_up": "If you think you can't answer the query, you can give up and let the user know.",
    },
    short_term_memory=True,
    long_term_memory=False,
    reasoning=False,
    input_type=["text", "voice"],
    output_type=["text", "voice"],
    response_type="json",
    max_retries=5,
    timeout=None,
    deployed=False,
    status="active",
    priority=None,
    failure_strategies=["retry", "escalate"],
    session_id=None,
    last_active=datetime.now(),
    collaboration_mode="single",
)

api_agent = APIAgent(
    agent_id=uuid.uuid4(),
    name="APIAgent",
    system_prompt=api_agent_system_prompt,
    persona="Helper",
    functions=[weather_forecast.openai_schema],
    routing_options={
        "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
        "respond": "If you think you have the answer, you can stop here.",
        "give_up": "If you think you can't answer the query, you can give up and let the user know.",
    },
    short_term_memory=True,
    long_term_memory=False,
    reasoning=False,
    input_type=["text", "voice"],
    output_type=["text", "voice"],
    response_type="json",
    max_retries=5,
    timeout=None,
    deployed=False,
    status="active",
    priority=None,
    failure_strategies=["retry", "escalate"],
    session_id=None,
    last_active=datetime.now(),
    collaboration_mode="single",
)


data_agent = DataAgent(
    agent_id=uuid.uuid4(),
    name="DataAgent",
    system_prompt=data_agent_system_prompt,
    persona="Helper",
    functions=[tool_schemas["get_customer_order"], tool_schemas["add_customer"], tool_schemas["get_customer_location"]],
    routing_options={
        "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
        "respond": "If you think you have the answer, you can stop here.",
        "give_up": "If you think you can't answer the query, you can give up and let the user know.",
    },
    short_term_memory=True,
    long_term_memory=False,
    reasoning=False,
    input_type=["text", "voice"],
    output_type=["text", "voice"],
    response_type="json",
    max_retries=5,
    timeout=None,
    deployed=False,
    status="active",
    priority=None,
    failure_strategies=["retry", "escalate"],
    session_id=None,
    last_active=datetime.now(),
    collaboration_mode="single",
)


agent_store = {
    "WebAgent": web_agent.execute,
    "DataAgent": data_agent.execute,
    "APIAgent": api_agent.execute,
}


agent_schemas = {
    "WebAgent": web_agent.openai_schema,
    "DataAgent": data_agent.openai_schema,
    "APIAgent": api_agent.openai_schema,
}


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
                        messages.append({"role": "tool", "tool_call_id": tool_id, "content": str(result)})

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
                        {"role": "assistant", "tool_calls": cast(List[ChatCompletionMessageToolCallParam], tool_calls)},
                    )
                    for tool in tool_calls:
                        yield f"Agent Called: {tool.function.name}\n"
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        result = agent_store[function_name](**arguments)
                        print(result)
                        messages.append({"role": "tool", "tool_call_id": tool_id, "content": str(result)})
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
