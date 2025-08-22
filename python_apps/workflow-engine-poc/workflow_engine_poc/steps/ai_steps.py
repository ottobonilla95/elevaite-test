"""
AI and LLM Processing Steps

Steps that integrate with AI models and language models for
intelligent processing, agent execution, and AI-powered workflows.
"""

import uuid
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Union
import logging

# Import tools system
from ..tools import (
    BASIC_TOOL_STORE,
    BASIC_TOOL_SCHEMAS,
    get_tool_by_name,
    get_tool_schema,
    function_schema,
    tool_handler,
)

from ..execution_context import ExecutionContext

# Initialize logger first
logger = logging.getLogger(__name__)

# Import llm-gateway components
try:
    from llm_gateway.services import (
        TextGenerationService,
        RequestType,
        UniversalService,
    )
    from llm_gateway.models.text_generation.core.interfaces import (
        TextGenerationType,
        TextGenerationModelName,
    )

    LLM_GATEWAY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"llm-gateway not available: {e}, falling back to simulation mode")
    LLM_GATEWAY_AVAILABLE = False
except Exception as e:
    logger.warning(
        f"llm-gateway configuration error: {e}, falling back to simulation mode"
    )
    LLM_GATEWAY_AVAILABLE = False


class SimpleAgent:
    """
    Simplified agent that can execute queries with optional tools.
    Uses llm-gateway for real LLM integration when available.
    """

    def __init__(
        self,
        name: str = "Assistant",
        system_prompt: str = "You are a helpful assistant.",
        tools: Optional[List[Dict[str, Any]]] = None,
        force_real_llm: bool = False,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.force_real_llm = force_real_llm
        self.agent_id = str(uuid.uuid4())

        # Initialize LLM service if available
        self.llm_service = None
        if LLM_GATEWAY_AVAILABLE and (force_real_llm or self._has_llm_config()):
            try:
                self.llm_service = TextGenerationService()
                logger.info(f"Agent {name} created with LLM gateway")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM service: {e}")
                self.llm_service = None
        else:
            logger.info(f"Agent {name} created without LLM gateway - will use simulation")

    def _has_llm_config(self) -> bool:
        """Check if we have any LLM configuration available"""
        import os
        
        # Check for OpenAI API key as a fallback
        return bool(os.getenv("OPENAI_API_KEY"))

    async def execute(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a query with the agent"""
        start_time = datetime.now()

        try:
            if self.llm_service and (self.force_real_llm or self._has_llm_config()):
                result = await self._execute_with_llm(query, context)
            else:
                result = await self._execute_simulation(query, context)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "query": query,
                "response": result.get("response", ""),
                "tool_calls": result.get("tool_calls", []),
                "execution_time_seconds": execution_time,
                "timestamp": end_time.isoformat(),
                "success": True,
                "mode": result.get("mode", "simulation"),
            }

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "query": query,
                "error": str(e),
                "execution_time_seconds": execution_time,
                "timestamp": end_time.isoformat(),
                "success": False,
                "mode": "error",
            }

    async def _execute_with_llm(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute query using real LLM through llm-gateway"""
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": query},
            ]

            # Add context if provided
            if context:
                context_str = f"Context: {json.dumps(context, indent=2)}\n\nQuery: {query}"
                messages[-1]["content"] = context_str

            # Prepare tools for LLM if any
            llm_tools = []
            if self.tools:
                for tool in self.tools:
                    if "function" in tool:
                        llm_tools.append(tool)

            # Make LLM request
            if llm_tools:
                response = await self.llm_service.generate_text_with_tools(
                    messages=messages,
                    tools=llm_tools,
                    model_name=TextGenerationModelName.GPT_4O_MINI,
                    generation_type=TextGenerationType.CHAT,
                )
            else:
                response = await self.llm_service.generate_text(
                    messages=messages,
                    model_name=TextGenerationModelName.GPT_4O_MINI,
                    generation_type=TextGenerationType.CHAT,
                )

            # Process tool calls if any
            tool_calls = []
            if hasattr(response, "tool_calls") and response.tool_calls:
                for tool_call in response.tool_calls:
                    try:
                        tool_result = await self._execute_tool_call(tool_call)
                        tool_calls.append(tool_result)
                    except Exception as e:
                        logger.error(f"Tool call failed: {e}")
                        tool_calls.append({
                            "tool_name": getattr(tool_call, "function", {}).get("name", "unknown"),
                            "error": str(e),
                            "success": False,
                        })

            return {
                "response": response.content if hasattr(response, "content") else str(response),
                "tool_calls": tool_calls,
                "mode": "llm",
            }

        except Exception as e:
            logger.error(f"LLM execution failed: {e}")
            # Fallback to simulation
            return await self._execute_simulation(query, context)

    async def _execute_simulation(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Simulate agent execution for testing/development"""
        await asyncio.sleep(0.1)  # Simulate processing time

        # Simple response generation based on query content
        query_lower = query.lower()
        
        if "hello" in query_lower or "hi" in query_lower:
            response = f"Hello! I'm {self.name}. How can I help you today?"
        elif "weather" in query_lower:
            response = "I don't have access to real weather data, but I can help you with other tasks!"
        elif "calculate" in query_lower or "math" in query_lower:
            response = "I can help with calculations! Please provide the specific math problem."
        elif "time" in query_lower:
            response = f"The current time is {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            response = f"I understand you're asking about: {query}. This is a simulated response from {self.name}."

        # Add context information if provided
        if context:
            response += f"\n\nI also see you've provided this context: {json.dumps(context, indent=2)}"

        return {
            "response": response,
            "tool_calls": [],
            "mode": "simulation",
        }

    async def _execute_tool_call(self, tool_call) -> Dict[str, Any]:
        """Execute a tool call"""
        try:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            # Get tool function
            tool_function = get_tool_by_name(function_name)
            if not tool_function:
                raise ValueError(f"Tool function not found: {function_name}")

            # Execute tool
            result = await tool_function(**function_args)

            return {
                "tool_name": function_name,
                "arguments": function_args,
                "result": result,
                "success": True,
            }

        except Exception as e:
            return {
                "tool_name": getattr(tool_call.function, "name", "unknown"),
                "error": str(e),
                "success": False,
            }


async def agent_execution_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Agent execution step that runs an AI agent with a query.
    
    Config options:
    - agent_name: Name of the agent
    - system_prompt: System prompt for the agent
    - query: Query to execute (can use template variables)
    - tools: List of tools available to the agent
    - force_real_llm: Force use of real LLM even without full config
    """
    
    config = step_config.get("config", {})
    
    # Get agent configuration
    agent_name = config.get("agent_name", "Assistant")
    system_prompt = config.get("system_prompt", "You are a helpful assistant.")
    query_template = config.get("query", "")
    tools = config.get("tools", [])
    force_real_llm = config.get("force_real_llm", False)
    
    # Process query template with input data
    query = query_template
    if isinstance(query_template, str) and "{" in query_template:
        try:
            query = query_template.format(**input_data)
        except KeyError as e:
            logger.warning(f"Template variable not found: {e}")
    
    # Create agent
    agent = SimpleAgent(
        name=agent_name,
        system_prompt=system_prompt,
        tools=tools,
        force_real_llm=force_real_llm,
    )
    
    # Execute query
    result = await agent.execute(query, context=input_data)
    
    return result
