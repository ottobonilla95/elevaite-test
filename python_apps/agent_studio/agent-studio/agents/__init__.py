import uuid
from datetime import datetime

from prompts import (
    web_agent_system_prompt,
    api_agent_system_prompt,
    data_agent_system_prompt,
    hello_world_agent_system_prompt,
    console_printer_agent_system_prompt,
    toshiba_agent_system_prompt,
    mitie_agent_system_prompt,
)

from .tools import weather_forecast
from .tools import web_search, tool_schemas
from .data_agent import DataAgent
from .api_agent import APIAgent
from .web_agent import WebAgent
from .hello_world_agent import HelloWorldAgent
from .console_printer_agent import ConsolePrinterAgent
from .toshiba_agent import create_toshiba_agent
from .mitie_agent import get_mitie_agent


# Lazy initialization functions for all agents
def get_web_agent():
    return WebAgent(
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


def get_api_agent():
    return APIAgent(
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


def get_data_agent():
    return DataAgent(
        agent_id=uuid.uuid4(),
        name="DataAgent",
        system_prompt=data_agent_system_prompt,
        persona="Helper",
        functions=[
            tool_schemas["get_customer_order"],
            tool_schemas["add_customer"],
            tool_schemas["get_customer_location"],
        ],
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


# Lazy initialization - create agents only when needed
def get_hello_world_agent():
    return HelloWorldAgent(
        agent_id=uuid.uuid4(),
        name="HelloWorldAgent",
        system_prompt=hello_world_agent_system_prompt,
        persona="Greeter",
        functions=[],  # No functions needed for this simple agent
        routing_options={"respond": "Respond with a friendly hello world greeting."},
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
        session_id=None,
        last_active=datetime.now(),
        collaboration_mode="single",
    )


def get_console_printer_agent():
    return ConsolePrinterAgent(
        agent_id=uuid.uuid4(),
        name="ConsolePrinterAgent",
        system_prompt=console_printer_agent_system_prompt,
        persona="Helper",
        functions=[tool_schemas["print_to_console"]],
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


def get_toshiba_agent():
    """Create ToshibaAgent with proper configuration"""
    # Note: Functions will be populated during database registration
    return create_toshiba_agent(
        system_prompt=toshiba_agent_system_prompt,
        functions=[],  # Will be populated with tool_schemas during registration
    )


def get_agent_store():
    """Lazy initialization of agent store to avoid Redis connection at import time"""
    web_agent = get_web_agent()
    data_agent = get_data_agent()
    api_agent = get_api_agent()
    hello_world_agent = get_hello_world_agent()
    console_printer_agent = get_console_printer_agent()
    toshiba_agent = get_toshiba_agent()
    mitie_agent = get_mitie_agent()

    return {
        "WebAgent": web_agent.execute,
        "DataAgent": data_agent.execute,
        "APIAgent": api_agent.execute,
        "HelloWorldAgent": hello_world_agent.execute,
        "ConsolePrinterAgent": console_printer_agent.execute,
        "ToshibaAgent": toshiba_agent.execute,
        "MitieAgent": mitie_agent.execute,
    }


def get_agent_schemas():
    """Lazy initialization of agent schemas to avoid Redis connection at import time"""
    web_agent = get_web_agent()
    data_agent = get_data_agent()
    api_agent = get_api_agent()
    hello_world_agent = get_hello_world_agent()
    console_printer_agent = get_console_printer_agent()
    toshiba_agent = get_toshiba_agent()
    mitie_agent = get_mitie_agent()

    return {
        "WebAgent": web_agent.openai_schema,
        "DataAgent": data_agent.openai_schema,
        "APIAgent": api_agent.openai_schema,
        "HelloWorldAgent": hello_world_agent.openai_schema,
        "ConsolePrinterAgent": console_printer_agent.openai_schema,
        "ToshibaAgent": toshiba_agent.openai_schema,
        "MitieAgent": mitie_agent.openai_schema,
    }


# For backward compatibility, create the stores when accessed
agent_store = None
agent_schemas = None


def _ensure_agent_store():
    global agent_store
    if agent_store is None:
        agent_store = get_agent_store()
    return agent_store


def _ensure_agent_schemas():
    global agent_schemas
    if agent_schemas is None:
        agent_schemas = get_agent_schemas()
    return agent_schemas
