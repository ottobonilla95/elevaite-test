from data_classes import Agent, AgentFlow
from utils import agent_schema
from typing import Any
import json
from tools import tool_store
from utils import client, convert_openai_to_gemini_schema
from datetime import datetime
import uuid
from tools import tool_schemas
from prompts import toshiba_agent_system_prompt
from prompts import TOSHIBA_AGENT_PROMPT6,TOSHIBA_AGENT_PROMPT_VIDEO
import time
from shared_state import session_status, update_status, update_sources
from shared_state import database_connection
from extract_sources import extract_only_aws_links
import os
import google.generativeai as genai

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

@agent_schema
class ToshibaAgent(Agent):
    async def execute3(self, query: Any,qid: str, session_id: str, chat_history: Any, user_id: str, agent_flow_id: str) -> Any:
        """
        Toshiba agent to answer any question related to Toshiba parts, assemblies, general information, etc.
        Optimized for performance with proper streaming support.
        """
        tries = 0
        max_tries = self.max_retries
        start_time = datetime.now()
        system_prompt = TOSHIBA_AGENT_PROMPT6
        final_response = ""
        tool_call_data = []
        sources = []


        # Initialize messages with chat history and system prompt
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": "Consider the chat history in the context and Answer this query: " + query})

        # Main loop for retries
        while tries < max_tries:
            try:
                print(f"\nToshiba Agent Tries: {tries}")
                await update_status(user_id, "Reformulated Query: " + query)
                yield session_status
                start_time = datetime.now()

                # Initial call to the LLM
                response = client.chat.completions.create(
                    model="gpt-4.1",
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
                            print(f"Arguments: {arguments}")
                            collection_id = " | "+ arguments.get("collection_id", "")
                            await update_status(user_id, "Searching: "+arguments.get("query", query)+collection_id)
                            yield session_status
                            retriever_time = datetime.now()

                            if function_name in tool_store:
                                result, sources = tool_store[function_name](**arguments)
                                # if tool_calls[0].function.name=="sql_database":
                                #     await update_logs(user_id,
                                #                       f"SQL AGENT LOGS ONLY FOR TESTING\n\nTool Call: {tool_calls[0].function.name} with arguments {tool_calls[0].function.arguments}")
                                #     await update_logs(user_id, f"Tool Response: {result}")

                                print("Tool Sources: ", sources)
                                sources = await extract_only_aws_links(result)
                                print("Unique Sources: ", sources)
                                await update_sources(user_id, sources)
                                if isinstance(result, list) and len(result) > 0:
                                    result = result[0]
                            else:
                                result = f"Tool {function_name} not found in tool_store"

                            # await update_logs(user_id, f"Tool Call: {tool_calls[0].function.name} with arguments {tool_calls[0].function.arguments}")
                            # await update_logs(user_id, f"Tool Response: {result}")

                            tool_call_data.append({
                                "name": tool_calls[0].function.name,
                                "arguments": tool_calls[0].function.arguments,
                                "result": result
                            })

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
                        print("-" * 100)
                        for message in messages:
                            print(message)
                        print("-" * 100)
                        yield session_status
                        final_response = client.chat.completions.create(
                            model="gpt-4.1",
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
                        final_response = collected_content

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
                    final_response = assistant_message.content
                    return  # Success, exit function


            except Exception as e:
                print(f"Error in main execution loop: {e}")
                tries += 1
                # Short delay before retry
                time.sleep(1)
            finally:
                # yield "\n\nReferences: \n\n"
                # yield "\n".join(list(set(sources)))
                # print(final_response)
                # print(sources)
                data_log = AgentFlow(
                    agent_flow_id=uuid.UUID(agent_flow_id) if type(agent_flow_id) == str else agent_flow_id,
                    session_id=uuid.UUID(session_id) if type(session_id) == str else session_id,
                    qid=uuid.UUID(qid) if type(qid) == str else qid,
                    user_id=user_id,
                    request=query,
                    response=final_response,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    tries=tries,
                    tool_calls=json.dumps(tool_call_data),
                    chat_history=json.dumps(chat_history),
                )

                print("Data Log: ", data_log)
                await database_connection.save_agent_flow(data_log)

        # Return failure message if max retries reached
        failure_response = "Couldn't find the answer to your query. Please try again with a different query."
        yield failure_response
        return

    def execute(self, query: Any, qid: str, session_id: str, chat_history: Any, user_id: str, agent_flow_id: str) -> Any:
        """
        Toshiba agent to answer any question related to Toshiba parts, assemblies, general information, etc.
        Non-streaming version that returns a complete response.
        """
        tries = 0
        max_tries = self.max_retries
        start_time = datetime.now()
        system_prompt = TOSHIBA_AGENT_PROMPT6
        final_response = ""
        tool_call_data = []
        sources = []

        # Initialize messages with chat history and system prompt
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": "Use the chat history as context and answer this query by the field service engineer: " + query})

        # Main loop for retries
        while tries < max_tries:
            try:
                print(f"\nToshiba Agent Tries: {tries}")
                # update_status(user_id, "Reformulated Query: " + query)
                start_time = datetime.now()

                # Initial call to the LLM
                response = client.chat.completions.create(
                    model="gpt-4.1",
                    messages=messages,
                    tools=self.functions,
                    tool_choice="auto",
                    temperature=0.6,
                    max_tokens=2000,
                    stream=False
                )

                # Handle tool calls if present
                assistant_message = response.choices[0].message

                if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
                    tool_calls = assistant_message.tool_calls[:1]
                    messages += [{"role": "assistant", "content": None, "tool_calls": tool_calls},]
                    print(f"Tool Calls: {tool_calls}")

                    # Process all tool calls
                    for tool in tool_calls:
                        tool_id = tool.id
                        function_name = tool.function.name
                        try:
                            arguments = json.loads(tool.function.arguments)
                            print(f"Arguments: {arguments}")
                            # update_status(user_id, "Searching: "+arguments.get("query", query))
                            retriever_time = datetime.now()

                            if function_name in tool_store:
                                result, sources = tool_store[function_name](**arguments)
                                if isinstance(result, list) and len(result) > 0:
                                    result = result[0]
                            else:
                                result = f"Tool {function_name} not found in tool_store"

                            tool_call_data.append({
                                "name": tool_calls[0].function.name,
                                "arguments": tool_calls[0].function.arguments,
                                "result": result
                            })

                            print(f"Time taken by the agent to retrieve the data: {datetime.now() - retriever_time}")

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

                    # Now get the final response without streaming
                    try:
                        # update_status(user_id, "Generating Response...")
                        print("-" * 100)
                        for message in messages:
                            print(message)
                        print("-" * 100)
                        
                        final_response_obj = client.chat.completions.create(
                            model="gpt-4.1",
                            messages=messages,
                            temperature=0.6,
                            response_format={"type": "text"},
                            max_tokens=2000,
                            stream=False
                        )

                        final_response = final_response_obj.choices[0].message.content
                        print(final_response)
                        print(sources)
                        print(
                            f"Time taken for final response: {datetime.now() - start_time}"
                        )
                        
                        # If we received no content, provide a fallback
                        if not final_response:
                            final_response = json.dumps({
                                "routing": "success",
                                "content": {
                                    "Answer": "The information has been processed, but no direct response was generated."
                                }
                            })
                        
                        # Save to database and return response
                        # self._save_agent_flow(agent_flow_id, session_id, qid, user_id, query,
                        #                      final_response, tries, tool_call_data, chat_history)
                        return final_response

                    except Exception as response_error:
                        print(f"Error generating final response: {response_error}")
                        tries += 1
                        continue
                else:
                    # No tool calls, just return the content directly
                    # update_status(user_id, "Generating Response...")
                    if hasattr(assistant_message, 'content') and assistant_message.content:
                        final_response = assistant_message.content
                    else:
                        final_response = json.dumps({
                            "routing": "success",
                            "content": {"Answer": "Processed your query, but no direct response was generated."}
                        })
                    
                    # Save to database and return response
                    # self._save_agent_flow(agent_flow_id, session_id, qid, user_id, query,
                    #                      final_response, tries, tool_call_data, chat_history)
                    return final_response

            except Exception as e:
                print(f"Error in main execution loop: {e}")
                tries += 1
                # Short delay before retry
                time.sleep(1)

        # Return failure message if max retries reached
        failure_response = "Couldn't find the answer to your query. Please try again with a different query."
        self._save_agent_flow(agent_flow_id, session_id, qid, user_id, query, 
                             failure_response, tries, tool_call_data, chat_history)
        return failure_response

    # def _save_agent_flow(self, agent_flow_id, session_id, qid, user_id, query,
    #                      response, tries, tool_call_data, chat_history):
    #     """Helper method to save agent flow data to database"""
    #     data_log = AgentFlow(
    #         agent_flow_id=uuid.UUID(agent_flow_id),
    #         session_id=uuid.UUID(session_id),
    #         qid=uuid.UUID(qid),
    #         user_id=user_id,
    #         request=query,
    #         response=response,
    #         created_at=datetime.now(),
    #         updated_at=datetime.now(),
    #         tries=tries,
    #         tool_calls=json.dumps(tool_call_data),
    #         chat_history=json.dumps(chat_history),
    #     )
    #     print(data_log)
    #     database_connection.save_agent_flow(data_log)

    async def execute_gemini(self, query: Any, qid: str, session_id: str, chat_history: Any, user_id: str, agent_flow_id: str) -> Any:
        """
        Toshiba agent using Google Gemini model to answer questions related to Toshiba parts, assemblies, etc.
        """
        tries = 0
        max_tries = self.max_retries
        start_time = datetime.now()
        system_prompt = TOSHIBA_AGENT_PROMPT6
        final_response = ""
        tool_call_data = []
        sources = []

        # Get Gemini model from environment
        gemini_model_name = os.getenv("GEMINI_MODEL", "gemini-pro-latest")
        
        # Convert tools to Gemini format
        gemini_tools = []
        for tool_schema in self.functions:
            if tool_schema.get("type") == "function":
                func_def = tool_schema["function"]
                gemini_params = convert_openai_to_gemini_schema(func_def.get("parameters", {}))
                gemini_tool = genai.protos.FunctionDeclaration(
                    name=func_def["name"],
                    description=func_def.get("description", ""),
                    parameters=gemini_params
                )
                gemini_tools.append(gemini_tool)

        model = genai.GenerativeModel(
            model_name=gemini_model_name,
            tools=gemini_tools if gemini_tools else None
        )

        # Convert chat history to Gemini format
        gemini_messages = []
        for msg in chat_history:
            if msg["role"] == "user":
                gemini_messages.append(genai.protos.Content(
                    role="user",
                    parts=[genai.protos.Part(text=msg["content"])]
                ))
            elif msg["role"] == "assistant":
                gemini_messages.append(genai.protos.Content(
                    role="model", 
                    parts=[genai.protos.Part(text=msg["content"])]
                ))

        # Main loop for retries
        while tries < max_tries:
            try:
                print(f"\nToshiba Agent Gemini Tries: {tries}")
                await update_status(user_id, "Reformulated Query: " + query)
                yield session_status
                start_time = datetime.now()

                # Create chat with history and system prompt
                chat = model.start_chat(history=gemini_messages)
                
                # Send message with system prompt context
                full_query = f"{system_prompt}\n\nConsider the chat history in the context and Answer this query: {query}"
                
                response = chat.send_message(
                    full_query,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.6,
                        max_output_tokens=2000,
                    )
                )

                # Handle function calls if present
                if response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            # Process function call
                            function_call = part.function_call
                            function_name = function_call.name
                            arguments = dict(function_call.args)
                            
                            print(f"Gemini Function Call: {function_name}, Args: {arguments}")
                            
                            collection_id = " | " + arguments.get("collection_id", "")
                            await update_status(user_id, "Searching: " + arguments.get("query", query) + collection_id)
                            yield session_status
                            
                            retriever_time = datetime.now()
                            
                            if function_name in tool_store:
                                result, sources = tool_store[function_name](**arguments)
                                sources = await extract_only_aws_links(result)
                                await update_sources(user_id, sources)
                                if isinstance(result, list) and len(result) > 0:
                                    result = result[0]
                            else:
                                result = f"Tool {function_name} not found in tool_store"
                            
                            tool_call_data.append({
                                "name": function_name,
                                "arguments": json.dumps(arguments),
                                "result": result
                            })
                            
                            print(f"Time taken by retriever: {datetime.now() - retriever_time}")
                            
                            # Send function response back to Gemini
                            function_response = genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": str(result)}
                                )
                            )
                            
                            final_response_obj = chat.send_message(
                                genai.protos.Content(parts=[function_response]),
                                generation_config=genai.types.GenerationConfig(
                                    temperature=0.6,
                                    max_output_tokens=2000,
                                )
                            )
                            
                            await update_status(user_id, "Generating Response...")
                            yield session_status
                            
                            # Stream the final response
                            if final_response_obj.text:
                                for char in final_response_obj.text:
                                    yield char
                                final_response = final_response_obj.text
                            else:
                                fallback = "The information has been processed, but no direct response was generated."
                                yield fallback
                                final_response = fallback
                        
                        elif hasattr(part, 'text') and part.text:
                            # Direct text response
                            await update_status(user_id, "Generating Response...")
                            yield session_status
                            
                            for char in part.text:
                                yield char
                            final_response = part.text

                return  # Success, exit function

            except Exception as e:
                print(f"Error in Gemini execution loop: {e}")
                tries += 1
                time.sleep(1)
            finally:
                data_log = AgentFlow(
                    agent_flow_id=uuid.UUID(agent_flow_id) if type(agent_flow_id) == str else agent_flow_id,
                    session_id=uuid.UUID(session_id) if type(session_id) == str else session_id,
                    qid=uuid.UUID(qid) if type(qid) == str else qid,
                    user_id=user_id,
                    request=query,
                    response=final_response,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    tries=tries,
                    tool_calls=json.dumps(tool_call_data),
                    chat_history=json.dumps(chat_history),
                )
                await database_connection.save_agent_flow(data_log)  # Save the log for Gemini execution

        # Return failure message if max retries reached
        failure_response = "Couldn't find the answer to your query. Please try again with a different query."
        yield failure_response
        return


@agent_schema
class ToshibaVideoAgent(Agent):
    async def execute3(self, query: Any, qid: str, session_id: str, chat_history: Any, user_id: str,
                       agent_flow_id: str) -> Any:
        """
        Toshiba agent to answer any question related to Toshiba parts, assemblies, general information, etc.
        Optimized for performance with proper streaming support.
        """
        tries = 0
        max_tries = self.max_retries
        start_time = datetime.now()
        system_prompt = TOSHIBA_AGENT_PROMPT_VIDEO
        final_response = ""
        tool_call_data = []
        sources = []

        # Initialize messages with chat history and system prompt
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append(
            {"role": "user", "content": "Consider the chat history in the context and Answer this query: " + query})

        # Main loop for retries
        while tries < max_tries:
            try:
                print(f"\nToshiba Agent Tries: {tries}")
                await update_status(user_id, "Finding Videos for: " + query)
                yield session_status
                start_time = datetime.now()

                # Initial call to the LLM
                response = client.chat.completions.create(
                    model="gpt-4.1",
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
                    messages += [{"role": "assistant", "content": None, "tool_calls": tool_calls}, ]
                    print(f"Tool Calls: {tool_calls}")

                    # Process all tool calls
                    for tool in tool_calls:
                        tool_id = tool.id
                        function_name = tool.function.name
                        try:
                            arguments = json.loads(tool.function.arguments)
                            print(f"Arguments: {arguments}")
                            collection_id = " | " + "video_collection"
                            await update_status(user_id, "Searching: " + arguments.get("query", query) + collection_id)
                            yield session_status
                            retriever_time = datetime.now()

                            if function_name in tool_store:
                                result, sources = tool_store[function_name](**arguments)
                                if isinstance(result, list) and len(result) > 0:
                                    result = result[0]
                            else:
                                result = f"Tool {function_name} not found in tool_store"

                            tool_call_data.append({
                                "name": tool_calls[0].function.name,
                                "arguments": tool_calls[0].function.arguments,
                                "result": result
                            })

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
                        print("-" * 100)
                        for message in messages:
                            print(message)
                        print("-" * 100)
                        yield session_status
                        final_response = client.chat.completions.create(
                            model="gpt-4.1",
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
                        final_response = collected_content

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
                    final_response = assistant_message.content
                    return  # Success, exit function


            except Exception as e:
                print(f"Error in main execution loop: {e}")
                tries += 1
                # Short delay before retry
                time.sleep(1)
            finally:
                # yield "\n\nReferences: \n\n"
                # yield "\n".join(list(set(sources)))
                # print(final_response)
                # print(sources)
                data_log = AgentFlow(
                    agent_flow_id=uuid.UUID(agent_flow_id) if type(agent_flow_id) == str else agent_flow_id,
                    session_id=uuid.UUID(session_id) if type(session_id) == str else session_id,
                    qid=uuid.UUID(qid) if type(qid) == str else qid,
                    user_id=user_id,
                    request=query,
                    response=final_response,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    tries=tries,
                    tool_calls=json.dumps(tool_call_data),
                    chat_history=json.dumps(chat_history),
                )

                print("Data Log: ", data_log)
                await database_connection.save_agent_flow(data_log)
                pass

        # Return failure message if max retries reached
        failure_response = "Couldn't find the answer to your query. Please try again with a different query."
        yield failure_response
        return


toshiba_agent = ToshibaAgent(name="ToshibaAgent",
                agent_id=uuid.uuid4(),
                system_prompt=toshiba_agent_system_prompt,
                persona="Helper",
                functions=[tool_schemas["query_retriever"], tool_schemas["customer_query_retriever"], tool_schemas["sql_database"], tool_schemas["multi_customer_query_retriever"]],
                routing_options={"ask": "If you think you need to ask more information or context from the user to answer the question.",
                                 "continue": "If you think you have the answer, you can stop here.",
                                 "give_up": "If you think you can't answer the query, you can give up and let the user know."
                                 },

                short_term_memory=True,
                long_term_memory=False,
                reasoning=False,
                # input_type=["text", "voice"],
                # output_type=["text", "voice"],
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

toshiba_video_agent = ToshibaVideoAgent(name="ToshibaVIdeoAgent",
                agent_id=uuid.uuid4(),
                system_prompt=toshiba_agent_system_prompt,
                persona="Helper",
                functions=[tool_schemas["video_retriever"]],
                routing_options={"ask": "If you think you need to ask more information or context from the user to answer the question.",
                                 "continue": "If you think you have the answer, you can stop here.",
                                 "give_up": "If you think you can't answer the query, you can give up and let the user know."
                                 },

                short_term_memory=True,
                long_term_memory=False,
                reasoning=False,
                # input_type=["text", "voice"],
                # output_type=["text", "voice"],
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
    "ToshibaAgent": toshiba_agent.execute,
}

agent_schemas = {"ToshibaAgent": toshiba_agent.openai_schema}


