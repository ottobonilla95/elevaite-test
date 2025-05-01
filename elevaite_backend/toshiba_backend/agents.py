from tools import weather_forecast
from data_classes import Agent
from utils import agent_schema
from typing import Any
import json
from tools import tool_store
from utils import client
from datetime import datetime
import uuid
from data_classes import PromptObject
from tools import web_search, add_numbers, get_customer_order, tool_schemas, get_customer_location, add_customer, get_knowledge, get_part_description, get_part_number
from prompts import web_agent_system_prompt, api_agent_system_prompt, data_agent_system_prompt, toshiba_agent_system_prompt
from prompts import TOSHIBA_AGENT_PROMPT2

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
        routing_options = '\n'.join([f"{k}: {v}" for k, v in self.routing_options.items()])
        system_prompt = self.system_prompt.prompt + f"""
        Here are the routing options:
        {routing_options}

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
    def execute(self, query: Any, chat_history: Any) -> Any:
        """
        Toshiba agent to answer any question related to Toshiba parts, assemblies, general information, etc.
        """
        tries = 0
        start_time = datetime.now()
        routing_options = '\n'.join([f"{k}: {v}" for k, v in self.routing_options.items()])
        system_prompt = self.system_prompt.prompt + f"""\n\n
        Here are the routing options:
        {routing_options}
        """
        messages=chat_history+[{"role": "user", "content": system_prompt}]+[{"role": "user", "content": query}]

        while tries < self.max_retries:
            print(tries)
            # print("\n\nMessage: ",messages)
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=self.functions,
                    tool_choice="auto",
                    temperature=0,
                    response_format={"type": "json_object"},
                )
                begin_chat_time = datetime.now()
                # print("\n\nResponse: ",response)
                if response.choices[0].finish_reason=="tool_calls":
                    tool_call_time = datetime.now()
                    # print("Time taken by the agent to call the tool: ",begin_chat_time - tool_call_time)
                    tool_calls = response.choices[0].message.tool_calls
                    messages+=[{"role": "assistant", "tool_calls": tool_calls},]
                    # print(tool_calls)
                    for tool in tool_calls:
                        print(tool.function.name)
                        tool_id = tool.id
                        print(tool.id)
                        arguments = json.loads(tool.function.arguments)
                        # arguments["query"] = 'for 6800, what is part number for a module'
                        print(arguments)
                        function_name = tool.function.name
                        result = tool_store[function_name](**arguments)
                        retrieve_time = datetime.now()
                        print("Time taken by the agent to retrieve the data: ",retrieve_time - begin_chat_time)
                        # print(result)
                        messages+= [{"role": "tool", "tool_call_id": tool_id, "content": str(result)}]

                else:
                    print("Time taken by the agent: ",datetime.now()-start_time)
                    # print(response.choices[0].message.content)
                    return response.choices[0].message.content
                # print(messages)
            except Exception as e:
                print("Time taken by the agent: ", datetime.now() - start_time)
                print(f"Error: {e}")
            tries += 1
        print("Time taken by the agent: ", datetime.now() - start_time)
        return json.dumps({"routing": "failed",
                           "content": "Couldn't find the answer to your query. Please try again with a different query."})

    def execute2(self, query: Any, chat_history: Any) -> Any:
        """
        Toshiba agent to answer any question related to Toshiba parts, assemblies, general information, etc.
        Optimized for performance.
        """
        tries = 0
        start_time = datetime.now()

        # Prepare system prompt with routing options
        # routing_options = '\n'.join([f"{k}: {v}" for k, v in self.routing_options.items()])
        system_prompt = TOSHIBA_AGENT_PROMPT2
        #                  + f"""\n\n
        # Here are the routing options:
        # {routing_options}
        # """)



        # Make a single call to query_retriever2 and store both context and sources
        retrieval_result = tool_store["query_retriever2"](query)
        context = retrieval_result[0]
        sources = retrieval_result[1]

        # Initialize messages with chat history and system prompt
        messages = chat_history + [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": context},
            {"role": "user", "content": query}
        ]

        # Main loop for retries
        while tries < self.max_retries:
            try:
                # Call the LLM
                response = client.chat.completions.create(
                    model="gpt-4.1-nano",
                    messages=messages,
                    tools=self.functions,
                    tool_choice="auto",
                    temperature=0,
                    response_format={"type": "json_object"},
                )

                # Handle tool calls
                if response.choices[0].finish_reason == "tool_calls":
                    tool_calls = response.choices[0].message.tool_calls[:1]
                    messages.append({"role": "assistant", "tool_calls": tool_calls})

                    # Process all tool calls
                    for tool in tool_calls:
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name

                        # Execute the tool and get results
                        result = tool_store["query_retriever2"](**arguments)[0]

                        # Add tool response to messages
                        messages.append({"role": "tool", "tool_call_id": tool_id, "content": str(result)})
                else:
                    # Return final response
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")

            tries += 1

        # Return failure message if max retries reached
        return json.dumps({
            "routing": "failed",
            "content": "Couldn't find the answer to your query. Please try again with a different query."
        })

@agent_schema
class DataAgent(Agent):
    def execute(self, query: Any) -> Any:
        """
        Ask the agent anything related to the database. It can fetch data from the database, or update the database. It can also do some reasoning based on the data in the database.
        The data contains customer ID, Order numbers and location in each row.
        """
        tries = 0
        routing_options = '\n'.join([f"{k}: {v}" for k, v in self.routing_options.items()])
        system_prompt = self.system_prompt.prompt + f"""
        Here are the routing options:
        {routing_options}

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
        routing_options = '\n'.join([f"{k}: {v}" for k, v in self.routing_options.items()])
        system_prompt = self.system_prompt.prompt + f"""
        Here are the routing options:
        {routing_options}

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
                functions=[tool_schemas["query_retriever"]],
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
                max_retries=3,
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


