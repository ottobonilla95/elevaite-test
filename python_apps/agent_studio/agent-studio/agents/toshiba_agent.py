"""
Migrated ToshibaAgent from elevaite_backend/toshiba_backend
Adapted for the agent_studio workflow system with streaming support
"""

import json
import uuid
import asyncio
from typing import Any, List, Dict, Optional, AsyncGenerator
from datetime import datetime

from utils import client
from .agent_base import Agent
from .tools import tool_store


class ToshibaAgent(Agent):
    """
    Toshiba agent to answer questions related to Toshiba parts, assemblies, and general information.
    Supports both synchronous and asynchronous execution with streaming capabilities.
    """

    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        enable_analytics: bool = False,
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

    async def execute_async(
        self, query: str, chat_history: Optional[List[Dict[str, str]]] = None, user_id: Optional[str] = None, **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronous execution with streaming support
        """
        tries = 0
        max_tries = self.max_retries
        start_time = datetime.now()

        # Convert chat_history format
        formatted_chat_history = []
        if chat_history:
            for msg in chat_history:
                if msg.get("actor") == "user":
                    formatted_chat_history.append({"role": "user", "content": msg.get("content", "")})
                elif msg.get("actor") == "assistant":
                    formatted_chat_history.append({"role": "assistant", "content": msg.get("content", "")})

        system_prompt = self.system_prompt.prompt
        messages = [
            {"role": "user", "content": system_prompt},
            {"role": "user", "content": f"Here is the chat history: {str(formatted_chat_history)}"},
            {"role": "user", "content": f"Answer this query: {query}"},
        ]

        while tries < max_tries:
            try:
                print(f"\nToshiba Agent Tries: {tries}")
                yield json.dumps({"status": "processing", "message": "Calling LLM..."})

                # Initial call to the LLM
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=self.functions,
                    tool_choice="auto",
                    temperature=0.6,
                    max_tokens=2000,
                    stream=False,
                )

                assistant_message = response.choices[0].message

                if hasattr(assistant_message, "tool_calls") and assistant_message.tool_calls:
                    tool_calls = assistant_message.tool_calls[:1]
                    messages += [{"role": "assistant", "content": None, "tool_calls": tool_calls}]

                    for tool in tool_calls:
                        tool_id = tool.id
                        function_name = tool.function.name
                        try:
                            arguments = json.loads(tool.function.arguments)
                            yield json.dumps({"status": "searching", "message": f"Searching: {arguments.get('query', query)}"})

                            if function_name in tool_store:
                                result = tool_store[function_name](**arguments)
                                if isinstance(result, (list, tuple)) and len(result) > 0:
                                    result = result[0]
                            else:
                                result = f"Tool {function_name} not found in tool_store"

                            messages.append({"role": "tool", "tool_call_id": tool_id, "content": str(result)})
                        except Exception as tool_error:
                            error_message = f"Error executing tool {function_name}: {str(tool_error)}"
                            messages.append({"role": "tool", "tool_call_id": tool_id, "content": error_message})

                    # Get final response with streaming
                    try:
                        yield json.dumps({"status": "generating", "message": "Generating Response..."})
                        final_response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=messages,
                            temperature=0.6,
                            response_format={"type": "text"},
                            max_tokens=2000,
                            stream=True,
                        )

                        collected_content = ""
                        for chunk in final_response:
                            if hasattr(chunk.choices[0].delta, "content") and chunk.choices[0].delta.content is not None:
                                content_chunk = chunk.choices[0].delta.content
                                collected_content += content_chunk
                                yield content_chunk

                        if not collected_content:
                            fallback = "The information has been processed, but no direct response was generated."
                            yield fallback

                        return

                    except Exception as streaming_error:
                        print(f"Error during response streaming: {streaming_error}")
                        tries += 1
                        continue
                else:
                    # No tool calls, return content directly
                    if hasattr(assistant_message, "content") and assistant_message.content:
                        yield assistant_message.content
                    else:
                        yield "Processed your query, but no direct response was generated."
                    return

            except Exception as e:
                print(f"Error in ToshibaAgent execution: {e}")
                tries += 1
                await asyncio.sleep(1)

        # Return failure message if max retries reached
        yield "Couldn't find the answer to your query. Please try again with a different query."

    @property
    def openai_schema(self):
        """OpenAI function schema for this agent"""
        return {
            "type": "function",
            "function": {
                "name": "ToshibaAgent",
                "description": "Specialized agent for Toshiba parts, assemblies, and technical information. Use this agent for questions about Toshiba elevator parts, components, specifications, and technical details.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The query about Toshiba parts or technical information"},
                        "chat_history": {
                            "type": "array",
                            "description": "Optional chat history for context",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "actor": {"type": "string", "enum": ["user", "assistant"]},
                                    "content": {"type": "string"},
                                },
                            },
                        },
                    },
                    "required": ["query"],
                },
            },
        }


# Create ToshibaAgent instance (will be configured when imported)
def create_toshiba_agent(system_prompt, functions, routing_options=None):
    """Factory function to create ToshibaAgent with proper configuration"""
    if routing_options is None:
        routing_options = {
            "ask": "If you think you need to ask more information or context from the user to answer the question.",
            "continue": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        }

    return ToshibaAgent(
        name="ToshibaAgent",
        agent_id=uuid.uuid4(),
        system_prompt=system_prompt,
        persona="Toshiba Expert",
        functions=functions,
        routing_options=routing_options,
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
