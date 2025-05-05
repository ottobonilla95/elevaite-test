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
from prompts import TOSHIBA_AGENT_PROMPT2,TOSHIBA_AGENT_PROMPT3,TOSHIBA_AGENT_PROMPT4,TOSHIBA_AGENT_PROMPT
import time
from shared_state import session_status, update_status
import asyncio




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
        messages=chat_history+[{"role": "system", "content": system_prompt}]+[{"role": "user", "content": query}]

        while tries < self.max_retries:
            # print(tries)
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
                           "content": "Couldn't find the answer to your query. Can you please provide some more context?"})

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
        # retrieval_result = tool_store["query_retriever2"](query)
        # context = retrieval_result[0]
        # sources = retrieval_result[1]
        # print("Time taken by the agent to retrieve the data: ",datetime.now()-start_time)

        # Initialize messages with chat history and system prompt
        messages = [{"role": "user", "content": system_prompt}]+chat_history + \
                   [{"role": "user", "content": "Answer this query: "+query},]
            # {"role": "user", "content": context},

        # Main loop for retries
        while tries < self.max_retries:
            try:
                print("\nToshiba Agent Tries: ", tries)
                start_time = datetime.now()
                # Call the LLM
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=self.functions,
                    tool_choice="auto",
                    temperature=0.6,
                    response_format={"type": "json_object"},
                )

                # Handle tool calls
                if response.choices[0].finish_reason == "tool_calls":
                    tool_calls = response.choices[0].message.tool_calls[:1]
                    messages.append({"role": "assistant", "tool_calls": tool_calls})
                    # print("\n\nTool Calls: ", tool_calls)

                    # Process all tool calls
                    for tool in tool_calls:
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        retriever_time = datetime.now()

                        # Execute the tool and get results
                        print(arguments)
                        result = tool_store["query_retriever2"](**arguments)[0]
                        print("Time taken by the agent to retrieve the data: ", datetime.now() - retriever_time)

                        # Add tool response to messages
                        messages.append({"role": "tool", "tool_call_id": tool_id, "content": str(result)})
                        print("Time taken by the tool calling: ", datetime.now() - start_time)
                else:
                    # Return final response
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")

            tries += 1

        # Return failure message if max retries reached
        return json.dumps({
            "routing": "failed",
            "content": {"Answer": "Couldn't find the answer to your query. Please try again with a different query."}
        })

    async def execute3(self, query: Any, chat_history: Any, user_id: str) -> Any:
        """
        Toshiba agent to answer any question related to Toshiba parts, assemblies, general information, etc.
        Optimized for performance with proper streaming support.
        """
        tries = 0
        max_tries = self.max_retries
        start_time = datetime.now()
        system_prompt = TOSHIBA_AGENT_PROMPT4

        # Initialize messages with chat history and system prompt
        messages = [
            {"role": "user", "content": system_prompt},
            {"role": "user", "content": "Here is the chat history: " + str(chat_history)},
            {"role": "user", "content": "Answer this query: " + query}
        ]

        # Main loop for retries
        while tries < max_tries:
            try:
                print(f"\nToshiba Agent Tries: {tries}")
                await update_status(user_id, "Calling LLM...")
                yield session_status
                start_time = datetime.now()

                # Initial call to the LLM
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=self.functions,
                    tool_choice="auto",
                    temperature=0.6,
                    # response_format={"type": "json_object"},
                    max_tokens=2000,
                    stream=False
                )

                # Handle tool calls if present
                assistant_message = response.choices[0].message

                if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                    # session_status[user_id] = "Calling Tools..."
                    # await update_status(user_id, "Searching Knowledge Base...")
                    # yield session_status
                    tool_calls = assistant_message.tool_calls[:1]
                    messages += [{"role": "assistant", "content": None, "tool_calls": tool_calls},]
                    print(f"Tool Calls: {tool_calls}")

                    # Process all tool calls
                    for tool in tool_calls:
                        tool_id = tool.id
                        function_name = tool.function.name
                        try:
                            arguments = json.loads(tool.function.arguments)
                            await update_status(user_id, "Searching: "+arguments.get("query", query))
                            yield session_status
                            retriever_time = datetime.now()

                            if function_name in tool_store:
                                result = tool_store[function_name](**arguments)[0]
                                if isinstance(result, list) and len(result) > 0:
                                    result = result[0]
                            else:
                                result = f"Tool {function_name} not found in tool_store"

                            print(f"Time taken by the agent to retrieve the data: {datetime.now() - retriever_time}")
                            # session_status[user_id] = arguments.get("query", query)

                            # Add tool response to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "content": str(result)
                            })
                        except Exception as tool_error:
                            # Handle errors in tool execution
                            error_message = f"Error executing tool {function_name}: {str(tool_error)}"
                            print(error_message)
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_id,
                                "content": error_message
                            })

                    print(f"Time taken for all tool calls: {datetime.now() - start_time}")

                    # Now get the final response with streaming enabled
                    try:
                        # session_status[user_id] = "Generating Response..."
                        await update_status(user_id, "Generating Response...")
                        yield session_status
                        final_response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=messages,
                            temperature=0.6,
                            response_format={"type": "text"},
                            max_tokens=2000,
                            stream=True  # Enable streaming for the final response
                        )

                        # Stream the response chunks
                        collected_content = ""
                        for chunk in final_response:
                            if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[
                                0].delta.content is not None:
                                content_chunk = chunk.choices[0].delta.content
                                collected_content += content_chunk
                                yield content_chunk

                        # If we received no content, provide a fallback
                        if not collected_content:
                            fallback = json.dumps({
                                "routing": "success",
                                "content": {
                                    "Answer": "The information has been processed, but no direct response was generated."}
                            })
                            yield fallback

                        # Success, exit the retry loop
                        return

                    except Exception as streaming_error:
                        print(f"Error during response streaming: {streaming_error}")
                        tries += 1
                        continue
                else:
                    # No tool calls, just return the content directly
                    await update_status(user_id, "Generating Response...")
                    if hasattr(assistant_message, 'content') and assistant_message.content:
                        yield assistant_message.content
                    else:
                        yield json.dumps({
                            "routing": "success",
                            "content": {"Answer": "Processed your query, but no direct response was generated."}
                        })
                    return  # Success, exit function

            except Exception as e:
                print(f"Error in main execution loop: {e}")
                tries += 1
                # Short delay before retry
                time.sleep(1)

        # Return failure message if max retries reached
        failure_response = "Couldn't find the answer to your query. Please try again with a different query."
        yield failure_response

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
                    model="gpt-4.1-nano",
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
                        # print(tool.function.name)
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        result = tool_store[function_name](**arguments)
                        # print(result)
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
                functions=[tool_schemas["query_retriever2"]],
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


