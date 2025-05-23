import pytest
import uuid
from datetime import datetime

from data_classes import PromptObject
from agents.hello_world_agent import HelloWorldAgent


@pytest.mark.unit
def test_hello_world_agent_creation():
    agent_id = uuid.uuid4()

    system_prompt = PromptObject(
        pid=uuid.uuid4(),
        prompt_label="HelloWorldPrompt",
        prompt="You are a friendly HelloWorld agent that greets users with enthusiasm and positivity.",
        sha_hash="dummy_hash",
        uniqueLabel="hello_world_prompt",
        appName="agent_studio",
        version="1.0.0",
        createdTime=datetime.now(),
        deployedTime=None,
        last_deployed=None,
        modelProvider="OpenAI",
        modelName="gpt-4o-mini",
        isDeployed=True,
        tags=["hello", "world"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    )

    agent = HelloWorldAgent(
        agent_id=agent_id,
        name="HelloWorld",
        system_prompt=system_prompt,
        persona="Friendly and enthusiastic",
        failure_strategies=["retry"],
        functions=[],
        routing_options={"respond": "Respond directly to the user"},
        stream_name="agent:hello_world_test",
        timeout=10,
    )

    assert agent is not None
    assert agent.name == "HelloWorld"
    assert agent.agent_id == agent_id
    assert agent.persona == "Friendly and enthusiastic"
    assert agent.stream_name == "agent:hello_world_test"
    assert agent.timeout == 10
