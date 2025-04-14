from agent_studio_backend.tools import weather_forecast
from data_classes import Agent
from utils import agent_schema
from typing import Any
import json
from tools import tool_store
from utils import client
from datetime import datetime
import uuid
from data_classes import PromptObject
from tools import web_search, add_numbers, get_customer_order, tool_schemas, get_customer_location, add_customer, get_knowledge
from prompts import web_agent_system_prompt, api_agent_system_prompt, data_agent_system_prompt, toshiba_agent_system_prompt

@agent_schema
class WebAgent(Agent):
    def execute(self, query: Any) -> Any:
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
        system_prompt = self.system_prompt.prompt + f"""
        Here are the routing options:
        {"\n".join([f"{k}: {v}" for k, v in self.routing_options.items()])}

        Your response should be in the format:
        {{ "routing": "respond", "content": "The answer to the query."}}
        """
        messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": query}]

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
                if response.choices[0].finish_reason=="tool_calls":
                    tool_calls = response.choices[0].message.tool_calls
                    messages+=[{"role": "assistant", "tool_calls": tool_calls},]
                    for tool in tool_calls:
                        print(tool.function.name)
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        result = tool_store[function_name](**arguments)
                        print(result)
                        messages+= [{"role": "tool", "tool_call_id": tool_id, "content": str(result)}]

                else:
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
            tries += 1

@agent_schema
class ToshibaAgent(Agent):
    def execute(self, query: Any) -> Any:
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
        start_time = datetime.now()
        system_prompt = self.system_prompt.prompt + f"""
        Here are the routing options:
        {"\n".join([f"{k}: {v}" for k, v in self.routing_options.items()])}

        Your response should be in the format:
        {{ "routing": "routing type", "content": "The relevant response."}}
        """
        messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": query}]

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
                if response.choices[0].finish_reason=="tool_calls":
                    tool_calls = response.choices[0].message.tool_calls
                    messages+=[{"role": "assistant", "tool_calls": tool_calls},]
                    for tool in tool_calls:
                        print(tool.function.name)
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        result = tool_store[function_name](**arguments)
                        print(arguments)

                        # print(result)
                        messages+= [{"role": "tool", "tool_call_id": tool_id, "content": str(result)}]

                else:
                    print("Time taken by the agent: ",datetime.now()-start_time)
                    return response.choices[0].message.content
            except Exception as e:
                print("Time taken by the agent: ", datetime.now() - start_time)
                print(f"Error: {e}")
            tries += 1
        print("Time taken by the agent: ", datetime.now() - start_time)
        return json.dumps({"routing": "failed",
                           "content": "Couldn't find the answer to your query. Please try again with a different query."})

@agent_schema
class DataAgent(Agent):
    def execute(self, query: Any) -> Any:
        """
        Ask the agent anything related to the database. It can fetch data from the database, or update the database. It can also do some reasoning based on the data in the database.
        The data contains customer ID, Order numbers and location in each row.
        """
        tries = 0
        system_prompt = self.system_prompt.prompt + f"""
        Here are the routing options:
        {"\n".join([f"{k}: {v}" for k, v in self.routing_options.items()])}

        Your response should be in the format:
        {{ "routing": "respond", "content": "The answer to the query."}}

        """
        messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": query}]

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
                if response.choices[0].finish_reason=="tool_calls":
                    tool_calls = response.choices[0].message.tool_calls
                    messages+=[{"role": "assistant", "tool_calls": tool_calls},]
                    for tool in tool_calls:
                        print(tool.function.name)
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        result = tool_store[function_name](**arguments)
                        print(result)
                        messages+= [{"role": "tool", "tool_call_id": tool_id, "content": str(result)}]

                else:
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
            tries += 1


@agent_schema
class APIAgent(Agent):
    def execute(self, query: Any) -> Any:
        """
        Ask the agent anything related to the APIs. It can call any of the following APIs and get the results for you.

        Valid APIs:
        1. Weather API - to answer any weather related queries for a city.
        """
        tries = 0
        system_prompt = self.system_prompt.prompt + f"""
        Here are the routing options:
        {"\n".join([f"{k}: {v}" for k, v in self.routing_options.items()])}

        Your response should be in the format:
        {{ "routing": "respond", "content": "The answer to the query."}}

        """
        messages=[{"role": "system", "content": system_prompt},{"role": "user", "content": query}]

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
                if response.choices[0].finish_reason=="tool_calls":
                    tool_calls = response.choices[0].message.tool_calls
                    messages+=[{"role": "assistant", "tool_calls": tool_calls},]
                    for tool in tool_calls:
                        print(tool.function.name)
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        result = tool_store[function_name](**arguments)
                        print(result)
                        messages+= [{"role": "tool", "tool_call_id": tool_id, "content": str(result)}]

                else:
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
            tries += 1


web_agent = WebAgent(name="WebSearchAgent",
                agent_id=uuid.uuid4(),
                system_prompt=web_agent_system_prompt,
                persona="Helper",
                functions=[web_search.openai_schema],
                routing_options={"continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
                                 "respond": "If you think you have the answer, you can stop here.",
                                 "give_up": "If you think you can't answer the query, you can give up and let the user know."
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

api_agent = APIAgent(agent_id=uuid.uuid4(),
                  name="APIAgent",
                  system_prompt=api_agent_system_prompt,
                  persona="Helper",
                  functions=[weather_forecast.openai_schema],
                  routing_options={
                      "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
                      "respond": "If you think you have the answer, you can stop here.",
                      "give_up": "If you think you can't answer the query, you can give up and let the user know."
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


data_agent = DataAgent(agent_id=uuid.uuid4(),
                  name="DataAgent",
                  system_prompt=data_agent_system_prompt,
                  persona="Helper",
                  functions=[tool_schemas["get_customer_order"], tool_schemas["add_customer"],tool_schemas["get_customer_location"]],
                  routing_options={
                      "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
                      "respond": "If you think you have the answer, you can stop here.",
                      "give_up": "If you think you can't answer the query, you can give up and let the user know."
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





class CommandAgent(Agent):
    def execute(self, query: str) -> str:
        """
        This agent can call any agent, tool, or component. It can also call a router agent to call multiple agents.
        """
        tries = 0
        system_prompt = self.system_prompt.prompt

        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": query}]


        while tries < self.max_retries:
            print("\n\nCommand Agent Tries: ", tries)
            try:
                if self.active_agents:
                    print("\n\nActive Agents: ", self.active_agents)
                    new_agents = []
                    messages += [{"role": "assistant", "tool_calls": self.active_agents}, ]
                    for agent in self.active_agents:
                        print("\n\nAgent Called: ", agent)
                        tool_id = agent.id
                        arguments = json.loads(agent.function.arguments)
                        arguments["query"] = query
                        function_name = agent.function.name
                        result = agent_store[function_name](**arguments)
                        print(result)
                        messages += [{"role": "tool", "tool_call_id": tool_id, "content": str(result)}]
                        if result["routing"] == "continue":
                            new_agents.append(agent)
                    self.active_agents = new_agents
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
                if response.choices[0].finish_reason == "tool_calls":
                    tool_calls = response.choices[0].message.tool_calls
                    print("\n\nTool Calls: ", tool_calls)
                    messages += [{"role": "assistant", "tool_calls": tool_calls},]
                    for tool in tool_calls:
                        print("\n\nAgent Called: ", tool)
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        if function_name in agent_store:
                            result = agent_store[function_name](**arguments)
                        else:
                            result = tool_store[function_name](**arguments)
                        print(result)
                        messages += [{"role": "tool", "tool_call_id": tool_id, "content": str(result)}]
                        if result["routing"] == "continue":
                            self.active_agents.append(tool)

                else:
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
            tries += 1


toshiba_agent = ToshibaAgent(name="ToshibaAgent",
                agent_id=uuid.uuid4(),
                system_prompt=toshiba_agent_system_prompt,
                persona="Helper",
                functions=[get_knowledge.openai_schema],
                routing_options={"ask": "If you think you need to ask more information or context from the user to answer the question.",
                                 "continue": "If you think you have the answer, you can stop here.",
                                 "give_up": "If you think you can't answer the query, you can give up and let the user know."
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
    "ToshibaAgent": toshiba_agent.execute,
}

agent_schemas = {"WebAgent": web_agent.openai_schema, "DataAgent": data_agent.openai_schema, "APIAgent": api_agent.openai_schema, "ToshibaAgent": toshiba_agent.openai_schema}


