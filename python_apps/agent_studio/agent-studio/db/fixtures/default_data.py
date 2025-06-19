from dataclasses import dataclass
from typing import Dict, List, Optional, Literal, Any

from db.schemas import AgentFunction, AgentFunctionInner


@dataclass
class DefaultPrompt:
    prompt_label: str
    prompt: str
    unique_label: str
    app_name: str
    version: str
    ai_model_provider: str
    ai_model_name: str
    tags: List[str]
    hyper_parameters: Dict[str, str]
    variables: Dict[str, str]


@dataclass
class DefaultAgent:
    name: str
    agent_type: Optional[Literal["router", "web_search", "data", "troubleshooting", "api", "weather", "toshiba"]]
    description: Optional[str]
    prompt_label: str
    persona: str
    functions: List[AgentFunction]
    routing_options: Dict[str, str]
    short_term_memory: bool
    long_term_memory: bool
    reasoning: bool
    input_type: List[Literal["text", "voice", "image"]]
    output_type: List[Literal["text", "voice", "image"]]
    response_type: Literal["json", "yaml", "markdown", "HTML", "None"]
    max_retries: int
    timeout: Optional[int]
    deployed: bool
    status: Literal["active", "paused", "terminated"]
    priority: Optional[int]
    failure_strategies: List[str]
    collaboration_mode: Literal["single", "team", "parallel", "sequential"]


AGENT_CODES = {
    "WebAgent": "w",
    "DataAgent": "d",
    "APIAgent": "a",
    "CommandAgent": "r",
    "HelloWorldAgent": "h",
    "ToshibaAgent": "t",
}


DEFAULT_PROMPTS: List[DefaultPrompt] = [
    DefaultPrompt(
        prompt_label="Web Agent Prompt",
        prompt="You are a web agent that can search the web for information.",
        unique_label="WebAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["web", "search"],
        hyper_parameters={"temperature": "0.7"},
        variables={"search_engine": "google"},
    ),
    DefaultPrompt(
        prompt_label="Data Agent Prompt",
        prompt="You are a data agent that can query databases and analyze data.",
        unique_label="DataAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["data", "database"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    ),
    DefaultPrompt(
        prompt_label="API Agent Prompt",
        prompt="You are an API agent that can make API calls to external services.",
        unique_label="APIAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["api", "integration"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    ),
    DefaultPrompt(
        prompt_label="Command Agent Prompt",
        prompt="You are a command agent that can coordinate other agents.",
        unique_label="CommandAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["command", "coordination"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    ),
    DefaultPrompt(
        prompt_label="Hello World Agent Prompt",
        prompt="You are a simple Hello World agent. Your only job is to greet users and respond with a friendly hello world message.",
        unique_label="HelloWorldAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o-mini",
        tags=["hello", "demo"],
        hyper_parameters={"temperature": "0.7"},
        variables={"greeting": "Hello, World!"},
    ),
    DefaultPrompt(
        prompt_label="Toshiba Agent Prompt",
        prompt="""You are a specialized Toshiba agent designed to answer questions related to Toshiba parts, assemblies, and general information.

Your primary responsibilities include:
- Providing accurate information about Toshiba elevator parts and components
- Helping users find specific part numbers and specifications
- Assisting with assembly information and technical details
- Offering guidance on Toshiba product compatibility and usage

When responding:
- Use the available tools to search for relevant information
- Provide detailed and accurate responses based on the retrieved data
- If you cannot find specific information, clearly state this and suggest alternative approaches
- Always maintain a helpful and professional tone

Your response should be in JSON format with the following structure:
{
    "routing": "continue" | "respond" | "give_up",
    "content": "Your detailed response here"
}

Use "continue" if you need more information, "respond" when you have a complete answer, and "give_up" if you cannot help with the query.""",
        unique_label="ToshibaAgentPrompt",
        app_name="agent_studio",
        version="1.0",
        ai_model_provider="OpenAI",
        ai_model_name="GPT-4o",
        tags=["toshiba", "parts", "elevator", "technical"],
        hyper_parameters={"temperature": "0.6"},
        variables={"domain": "toshiba_parts"},
    ),
]


DEFAULT_AGENTS: List[DefaultAgent] = [
    DefaultAgent(
        name="WebAgent",
        agent_type="web_search",
        description="Searches the web for information and provides relevant results",
        prompt_label="WebAgentPrompt",
        persona="Helper",
        functions=[AgentFunction(function=AgentFunctionInner(name="web_search"))],
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
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="DataAgent",
        agent_type="data",
        description="Processes and analyzes data from various sources",
        prompt_label="DataAgentPrompt",
        persona="Helper",
        functions=[AgentFunction(function=AgentFunctionInner(name="web_search"))],
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
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="APIAgent",
        agent_type="api",
        description="Connects to external APIs and services to retrieve data",
        prompt_label="APIAgentPrompt",
        persona="Helper",
        functions=[],
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
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="CommandAgent",
        agent_type="router",
        description="Coordinates and routes requests to appropriate agents",
        prompt_label="CommandAgentPrompt",
        persona="Coordinator",
        functions=[],
        routing_options={
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        short_term_memory=True,
        long_term_memory=False,
        reasoning=True,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=3,
        timeout=None,
        deployed=False,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="HelloWorldAgent",
        agent_type=None,  # This is a demo agent, no specific type
        description="A simple demo agent that greets users with hello world messages",
        prompt_label="HelloWorldAgentPrompt",
        persona="Greeter",
        functions=[],
        routing_options={
            "respond": "Respond with a friendly hello world greeting.",
        },
        short_term_memory=False,
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
        failure_strategies=["retry"],
        collaboration_mode="single",
    ),
    DefaultAgent(
        name="ToshibaAgent",
        agent_type="toshiba",
        description="Specialized agent for Toshiba parts, assemblies, and technical information",
        prompt_label="ToshibaAgentPrompt",
        persona="Toshiba Expert",
        functions=[AgentFunction(function=AgentFunctionInner(name="query_retriever2"))],
        routing_options={
            "ask": "If you think you need to ask more information or context from the user to answer the question.",
            "continue": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
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
        collaboration_mode="single",
    ),
]
