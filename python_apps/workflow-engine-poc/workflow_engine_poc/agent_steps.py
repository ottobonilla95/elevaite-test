"""
Simplified Agent Execution Steps

Clean, simplified agent execution without unnecessary complexity.
Focuses on core functionality: create agent, execute query, return result.
Now uses the llm-gateway for real LLM integration with multiple providers.
"""

import uuid
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Union
import logging

# Import tools system
from .tools import (
    BASIC_TOOL_STORE,
    BASIC_TOOL_SCHEMAS,
    get_tool_by_name,
    get_tool_schema,
    function_schema,
    tool_handler,
)

from .execution_context import ExecutionContext

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
    Simplified agent implementation focused on core functionality.

    Removes complex edge case handling and focuses on:
    - Clean agent creation
    - Simple query execution
    - Straightforward result handling
    """

    def __init__(
        self,
        name: str,
        model: str,
        system_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_handlers: Optional[Dict[str, Callable]] = None,
        tool_names: Optional[List[str]] = None,
        provider_type: str = "openai_textgen",
    ):
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider_type = provider_type
        self.agent_id = str(uuid.uuid4())

        # Initialize tools and handlers
        self.tools = []
        self.tool_handlers = {}

        # If tool_names provided, load from basic tool store
        if tool_names:
            for tool_name in tool_names:
                tool_func = get_tool_by_name(tool_name)
                tool_schema = get_tool_schema(tool_name)
                if tool_func and tool_schema:
                    self.tools.append(tool_schema)
                    self.tool_handlers[tool_name] = tool_func
                else:
                    logging.warning(f"Tool '{tool_name}' not found in basic tool store")

        # Add any explicitly provided tools and handlers
        if tools:
            self.tools.extend(tools)
        if tool_handlers:
            self.tool_handlers.update(tool_handlers)

        # Initialize LLM service if available
        if LLM_GATEWAY_AVAILABLE:
            try:
                self.llm_service = UniversalService()
                logger.info(f"Agent {self.name} initialized with LLM gateway")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize LLM service for agent {self.name}: {e}"
                )
                self.llm_service = None
        else:
            self.llm_service = None
            logger.info(
                f"Agent {self.name} created without LLM gateway - will use simulation"
            )

    async def execute(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a query with the agent.

        Simplified execution that focuses on the core task without
        complex error handling or edge cases.
        """
        start_time = datetime.now()

        try:
            if self.llm_service and LLM_GATEWAY_AVAILABLE:
                # Use real LLM via llm-gateway
                response = await self._execute_with_llm_gateway(query, context)
            else:
                # Fallback to simulation
                logger.info(f"Using simulation for agent {self.name}")
                await asyncio.sleep(0.1)  # Simulate processing time
                response = await self._simulate_agent_response(query, context)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return {
                "response": response,
                "agent_name": self.name,
                "agent_id": self.agent_id,
                "model": self.model,
                "provider_type": self.provider_type,
                "execution_time": execution_time,
                "tools_used": self.tools,
                "timestamp": end_time.isoformat(),
                "success": True,
            }

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            logger.error(f"Agent execution failed: {e}")

            return {
                "response": None,
                "error": str(e),
                "agent_name": self.name,
                "agent_id": self.agent_id,
                "execution_time": execution_time,
                "success": False,
            }

    async def _execute_with_llm_gateway(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute query using the llm-gateway for real LLM calls.

        Supports multiple providers: OpenAI, Gemini, Bedrock, On-Prem
        """
        if self.llm_service is None:
            raise Exception("LLM service not available")

        try:
            # Prepare the configuration for llm-gateway
            config = {
                "model": self.model,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "role": "assistant",
            }

            # Add any additional context to the system message
            system_message = self.system_prompt
            if context:
                system_message += f"\n\nAdditional context: {context}"

            # Prepare tools for the LLM call
            tools_param = None
            tool_choice = None
            if self.tools and self.provider_type == "openai_textgen":
                tools_param = self.tools
                tool_choice = "auto"

            # Make the LLM call using llm-gateway
            response = self.llm_service.handle_request(
                request_type=RequestType.TEXT_GENERATION,
                provider_type=self.provider_type,
                prompt=query,
                sys_msg=system_message,
                config=config,
                model_name=self.model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                retries=3,
                tools=tools_param,
                tool_choice=tool_choice,
            )

            if response and hasattr(response, "text"):
                logger.info(
                    f"LLM response received: {len(response.text)} chars, "
                    f"{response.tokens_in} tokens in, {response.tokens_out} tokens out, "
                    f"{response.latency:.3f}s latency"
                )

                # Handle tool calls if present
                if hasattr(response, "tool_calls") and response.tool_calls:
                    logger.info(f"Processing {len(response.tool_calls)} tool calls")
                    tool_results = await self._handle_tool_calls(response.tool_calls)

                    # If we have tool results, we might need to make another LLM call
                    # For now, just return the original response with tool info
                    if tool_results:
                        return f"{response.text}\n\nTool Results: {json.dumps(tool_results, indent=2)}"

                return response.text
            else:
                logger.error("Invalid response from LLM gateway")
                return "Error: Invalid response from LLM service"

        except Exception as e:
            logger.error(f"LLM gateway execution failed: {e}")
            # Fallback to simulation on error
            logger.info("Falling back to simulation due to LLM error")
            return await self._simulate_agent_response(query, context)

    async def _handle_tool_calls(self, tool_calls: List[Any]) -> Dict[str, Any]:
        """
        Handle tool calls from the LLM.

        This is where the actual tool execution happens in the API layer,
        not in the LLM Gateway.
        """
        results = {}

        for tool_call in tool_calls:
            tool_name = tool_call.name
            tool_args = tool_call.arguments
            tool_id = tool_call.id

            logger.info(f"Executing tool: {tool_name} with args: {tool_args}")

            try:
                if tool_name in self.tool_handlers:
                    # Execute the tool handler
                    result = await self.tool_handlers[tool_name](**tool_args)
                    results[tool_id] = {
                        "tool_name": tool_name,
                        "result": result,
                        "success": True,
                    }
                else:
                    # Tool not implemented
                    logger.warning(f"Tool {tool_name} not implemented")
                    results[tool_id] = {
                        "tool_name": tool_name,
                        "result": f"Tool {tool_name} is not implemented",
                        "success": False,
                    }

            except Exception as e:
                logger.error(f"Tool execution failed for {tool_name}: {e}")
                results[tool_id] = {
                    "tool_name": tool_name,
                    "result": f"Tool execution failed: {str(e)}",
                    "success": False,
                }

        return results

    async def _simulate_agent_response(
        self, query: str, context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Simulate agent response for PoC.
        In real implementation, this would call the actual LLM API.
        """

        # Simple response simulation based on query content
        query_lower = query.lower()

        if "analyze" in query_lower or "analysis" in query_lower:
            return f"Based on my analysis using the {self.model} model, I can provide the following insights: [Simulated analysis response for PoC]"

        elif "summarize" in query_lower or "summary" in query_lower:
            return (
                f"Here's a summary of the content: [Simulated summary response for PoC]"
            )

        elif "question" in query_lower or "what" in query_lower:
            return f"To answer your question: [Simulated answer response for PoC]"

        else:
            return f"I understand your request. Here's my response using {self.model}: [Simulated general response for PoC]"


async def agent_execution_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Simplified agent execution step function.

    This is the main entry point for agent execution in workflows.
    Much simpler than the original implementation.
    """

    try:
        # Extract configuration
        config = step_config.get("config", {})
        agent_config = config.get("agent_config", {})

        # Validate required fields
        if not agent_config:
            raise ValueError("agent_config is required")

        required_fields = ["agent_name", "model", "system_prompt"]
        for field in required_fields:
            if field not in agent_config:
                raise ValueError(f"Missing required agent_config field: {field}")

        # Create agent
        agent = SimpleAgent(
            name=agent_config["agent_name"],
            model=agent_config["model"],
            system_prompt=agent_config["system_prompt"],
            temperature=agent_config.get("temperature", 0.1),
            max_tokens=agent_config.get("max_tokens", 1000),
            tools=agent_config.get("tools", []),
        )

        # Get query
        query = config.get("query")
        if not query:
            # Try to build query from template
            query_template = config.get("query_template")
            if query_template:
                try:
                    query = query_template.format(**input_data)
                except KeyError as e:
                    raise ValueError(f"Query template references missing data: {e}")
            else:
                raise ValueError("Either 'query' or 'query_template' must be provided")

        # Prepare context for agent
        agent_context = {
            "input_data": input_data,
            "execution_context": {
                "execution_id": execution_context.execution_id,
                "workflow_id": execution_context.workflow_id,
                "user_id": execution_context.user_context.user_id,
            },
        }

        # Add any additional context from config
        additional_context = config.get("execution_context", {})
        agent_context.update(additional_context)

        # Execute agent
        logger.info(f"Executing agent: {agent.name} with query: {query[:100]}...")
        result = await agent.execute(query, agent_context)

        # Process result based on configuration
        return_simplified = config.get("return_simplified", False)

        if return_simplified:
            # Return simplified response
            return {
                "response": result.get("response"),
                "success": result.get("success", False),
                "agent_name": result.get("agent_name"),
                "execution_time": result.get("execution_time"),
                "tools_used": result.get("tools_used", []),
                "timestamp": result.get("timestamp"),
            }
        else:
            # Return full response with agent execution details
            return {
                "agent_execution": result,
                "success": result.get("success", False),
                "response": result.get(
                    "response"
                ),  # Also include at top level for easy access
                "metadata": {
                    "agent_name": result.get("agent_name"),
                    "model": result.get("model"),
                    "execution_time": result.get("execution_time"),
                    "tools_used": result.get("tools_used", []),
                },
            }

    except Exception as e:
        logger.error(f"Agent execution step failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "agent_execution": None,
            "response": None,
        }


async def create_dynamic_agent(agent_config: Dict[str, Any]) -> SimpleAgent:
    """
    Create a dynamic agent from configuration.
    Simplified version without complex validation.
    """

    return SimpleAgent(
        name=agent_config.get("agent_name", "Dynamic Agent"),
        model=agent_config.get("model", "gpt-4o-mini"),
        system_prompt=agent_config.get(
            "system_prompt", "You are a helpful AI assistant."
        ),
        temperature=agent_config.get("temperature", 0.1),
        max_tokens=agent_config.get("max_tokens", 1000),
        tools=agent_config.get("tools", []),
        tool_handlers=agent_config.get("tool_handlers", {}),
        tool_names=agent_config.get("tool_names", []),
        provider_type=agent_config.get("provider_type", "openai_textgen"),
    )


# Example tool functions
async def get_weather(location: str, unit: str = "fahrenheit") -> str:
    """Get weather information for a location"""
    # This is a mock implementation
    return f"The weather in {location} is 72°{unit[0].upper()} and sunny."


async def search_web(query: str, num_results: int = 5) -> str:
    """Search the web for information"""
    # This is a mock implementation
    return f"Found {num_results} results for '{query}': Mock search results would appear here."


async def calculate(expression: str) -> str:
    """Perform mathematical calculations"""
    try:
        # Simple eval for demo - in production use a safe math parser
        result = eval(expression)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"


# Example tool definitions for OpenAI function calling
WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The temperature unit",
                },
            },
            "required": ["location"],
        },
    },
}

SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Search the web for information",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}

CALCULATOR_TOOL = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Perform mathematical calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate",
                }
            },
            "required": ["expression"],
        },
    },
}

# Example agent with tools using the new tools system
EXAMPLE_ASSISTANT_WITH_TOOLS = SimpleAgent(
    name="Assistant with Tools",
    model="gpt-4o-mini",
    system_prompt="You are a helpful assistant with access to tools. Use the available tools to help answer questions.",
    temperature=0.1,
    max_tokens=1000,
    tool_names=[
        "add_numbers",
        "get_current_time",
        "weather_forecast",
        "calculate",
        "web_search",
    ],
    provider_type="openai_textgen",
)

# Example agent with custom tools (backward compatibility)
EXAMPLE_ASSISTANT_WITH_CUSTOM_TOOLS = SimpleAgent(
    name="Assistant with Custom Tools",
    model="gpt-4o-mini",
    system_prompt="You are a helpful assistant with access to custom tools.",
    temperature=0.1,
    max_tokens=1000,
    tools=[WEATHER_TOOL, SEARCH_TOOL, CALCULATOR_TOOL],
    tool_handlers={
        "get_weather": get_weather,
        "search_web": search_web,
        "calculate": calculate,
    },
    provider_type="openai_textgen",
)

# Example agent configurations for testing with different providers
EXAMPLE_CONTENT_ANALYZER = {
    "agent_name": "Content Analyzer",
    "model": "gpt-4o-mini",
    "system_prompt": "You are a content analyzer. Analyze the provided content and provide insights about its structure, themes, and key points.",
    "temperature": 0.1,
    "max_tokens": 1000,
    "tools": ["document_search", "text_analysis"],
    "provider_type": "openai_textgen",
}

EXAMPLE_SUMMARIZER = {
    "agent_name": "Document Summarizer",
    "model": "gpt-4o-mini",
    "system_prompt": "You are a document summarizer. Create concise, accurate summaries of provided content while preserving key information.",
    "temperature": 0.0,
    "max_tokens": 500,
    "tools": [],
    "provider_type": "openai_textgen",
}

EXAMPLE_QA_AGENT = {
    "agent_name": "Q&A Assistant",
    "model": "gpt-4o-mini",
    "system_prompt": "You are a question-answering assistant. Answer questions based on the provided context accurately and concisely.",
    "temperature": 0.2,
    "max_tokens": 800,
    "tools": ["document_search", "fact_check"],
    "provider_type": "openai_textgen",
}

# Example configurations for other providers
EXAMPLE_GEMINI_AGENT = {
    "agent_name": "Gemini Content Analyzer",
    "model": "gemini-1.5-flash",
    "system_prompt": "You are a content analyzer using Google's Gemini model. Provide detailed analysis of the content.",
    "temperature": 0.1,
    "max_tokens": 1000,
    "tools": [],
    "provider_type": "gemini_textgen",
}

EXAMPLE_BEDROCK_AGENT = {
    "agent_name": "Claude Content Analyzer",
    "model": "anthropic.claude-instant-v1",
    "system_prompt": "You are Claude, an AI assistant by Anthropic. Analyze the provided content thoroughly.",
    "temperature": 0.1,
    "max_tokens": 1000,
    "tools": [],
    "provider_type": "bedrock_textgen",
}


# Test function for agent execution
async def test_agent_execution():
    """Test the simplified agent execution"""

    # Create test execution context
    from .execution_context import ExecutionContext, UserContext

    workflow_config = {
        "workflow_id": "test-agent",
        "name": "Test Agent Workflow",
        "steps": [],
    }

    user_context = UserContext(user_id="test_user")
    execution_context = ExecutionContext(workflow_config, user_context)

    # Test step configuration
    step_config = {
        "step_id": "test_agent_step",
        "step_type": "agent_execution",
        "config": {
            "agent_config": EXAMPLE_CONTENT_ANALYZER,
            "query": "Please analyze the following content: {content}",
            "return_simplified": True,
        },
    }

    # Test input data
    input_data = {
        "content": "This is a test document for analysis. It contains multiple sentences and should be analyzed for structure and content."
    }

    # Execute agent step
    result = await agent_execution_step(step_config, input_data, execution_context)

    print("Agent Execution Test Result:")
    print(f"Success: {result.get('success')}")
    print(f"Response: {result.get('response')}")
    print(f"Agent: {result.get('agent_name')}")
    print(f"Execution Time: {result.get('execution_time')}")

    return result


if __name__ == "__main__":
    # Run test
    asyncio.run(test_agent_execution())
