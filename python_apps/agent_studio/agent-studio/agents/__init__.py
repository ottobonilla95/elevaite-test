import uuid
from datetime import datetime

from prompts import (
    web_agent_system_prompt,
    api_agent_system_prompt,
    data_agent_system_prompt,
)

from tools import weather_forecast
from tools import web_search, tool_schemas
from .data_agent import DataAgent
from .api_agent import APIAgent
from .web_agent import WebAgent


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
