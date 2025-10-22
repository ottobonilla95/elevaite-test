import pytest
import uuid
import json
from datetime import datetime
from unittest.mock import Mock, patch

from data_classes import PromptObject
from agents.agent_base import Agent
from agents.command_agent import CommandAgent
from agents.web_agent import WebAgent


@pytest.mark.unit
def test_agent_base_simplified_execution():
    agent_id = uuid.uuid4()
    
    system_prompt = PromptObject(
        pid=uuid.uuid4(),
        prompt_label="TestPrompt",
        prompt="You are a test agent.",
        sha_hash="dummy_hash",
        uniqueLabel="test_prompt",
        appName="agent_studio",
        version="1.0.0",
        createdTime=datetime.now(),
        deployedTime=None,
        last_deployed=None,
        modelProvider="OpenAI",
        modelName="gpt-4o-mini",
        isDeployed=True,
        tags=["test"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    )
    
    agent = Agent(
        agent_id=agent_id,
        name="TestAgent",
        system_prompt=system_prompt,
        persona="Test",
        functions=[],
        routing_options={"respond": "Respond to the user"},
        failure_strategies=["retry"],
    )
    
    with patch('utils.client') as mock_client:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].finish_reason = "stop"
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.tool_calls = None
        mock_client.chat.completions.create.return_value = mock_response
        
        result = agent.execute("Test query")
        
        assert result == "Test response"
        mock_client.chat.completions.create.assert_called_once()
        
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == agent.model
        assert call_args[1]['temperature'] == agent.temperature
        assert len(call_args[1]['messages']) == 2


@pytest.mark.unit
def test_command_agent_uses_base_execution():
    agent_id = uuid.uuid4()
    
    system_prompt = PromptObject(
        pid=uuid.uuid4(),
        prompt_label="CommandPrompt",
        prompt="You are a command agent.",
        sha_hash="dummy_hash",
        uniqueLabel="command_prompt",
        appName="agent_studio",
        version="1.0.0",
        createdTime=datetime.now(),
        deployedTime=None,
        last_deployed=None,
        modelProvider="OpenAI",
        modelName="gpt-4o-mini",
        isDeployed=True,
        tags=["command"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    )
    
    command_agent = CommandAgent(
        agent_id=agent_id,
        name="CommandAgent",
        system_prompt=system_prompt,
        persona="Commander",
        functions=[],
        routing_options={"respond": "Respond to the user"},
        model="gpt-4o-mini",
        temperature=0.7,
        failure_strategies=["retry"],
    )
    
    with patch('utils.client') as mock_client:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].finish_reason = "stop"
        mock_response.choices[0].message.content = "Command response"
        mock_response.choices[0].message.tool_calls = None
        mock_client.chat.completions.create.return_value = mock_response
        
        result = command_agent.execute("Test command")
        
        assert result == "Command response"
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.unit
def test_web_agent_uses_base_execution():
    agent_id = uuid.uuid4()
    
    system_prompt = PromptObject(
        pid=uuid.uuid4(),
        prompt_label="WebPrompt",
        prompt="You are a web search agent.",
        sha_hash="dummy_hash",
        uniqueLabel="web_prompt",
        appName="agent_studio",
        version="1.0.0",
        createdTime=datetime.now(),
        deployedTime=None,
        last_deployed=None,
        modelProvider="OpenAI",
        modelName="gpt-4o-mini",
        isDeployed=True,
        tags=["web"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    )
    
    web_agent = WebAgent(
        agent_id=agent_id,
        name="WebAgent",
        system_prompt=system_prompt,
        persona="Web Searcher",
        functions=[],
        routing_options={"respond": "Respond to the user"},
        failure_strategies=["retry"],
    )
    
    with patch('utils.client') as mock_client:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].finish_reason = "stop"
        mock_response.choices[0].message.content = "Web search response"
        mock_response.choices[0].message.tool_calls = None
        mock_client.chat.completions.create.return_value = mock_response
        
        result = web_agent.execute("Search for something")
        
        assert result == "Web search response"
        mock_client.chat.completions.create.assert_called_once()


@pytest.mark.unit
def test_agent_with_tools():
    agent_id = uuid.uuid4()
    
    system_prompt = PromptObject(
        pid=uuid.uuid4(),
        prompt_label="ToolPrompt",
        prompt="You are an agent with tools.",
        sha_hash="dummy_hash",
        uniqueLabel="tool_prompt",
        appName="agent_studio",
        version="1.0.0",
        createdTime=datetime.now(),
        deployedTime=None,
        last_deployed=None,
        modelProvider="OpenAI",
        modelName="gpt-4o-mini",
        isDeployed=True,
        tags=["tools"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    )
    
    mock_tool_schema = {
        "type": "function",
        "function": {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Test input"}
                },
                "required": ["input"]
            }
        }
    }
    
    agent = Agent(
        agent_id=agent_id,
        name="ToolAgent",
        system_prompt=system_prompt,
        persona="Tool User",
        functions=[mock_tool_schema],
        routing_options={"respond": "Respond to the user"},
        failure_strategies=["retry"],
    )
    
    with patch('utils.client') as mock_client, \
         patch('agents.tools.tool_store', {'test_tool': lambda input: "Tool result"}) as mock_tool_store:
        
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_tool"
        mock_tool_call.function.arguments = '{"input": "test"}'
        
        mock_first_response = Mock()
        mock_first_response.choices = [Mock()]
        mock_first_response.choices[0].finish_reason = "tool_calls"
        mock_first_response.choices[0].message.tool_calls = [mock_tool_call]
        
        mock_second_response = Mock()
        mock_second_response.choices = [Mock()]
        mock_second_response.choices[0].finish_reason = "stop"
        mock_second_response.choices[0].message.content = "Final response with tool result"
        mock_second_response.choices[0].message.tool_calls = None
        
        mock_client.chat.completions.create.side_effect = [mock_first_response, mock_second_response]
        
        result = agent.execute("Use the tool")
        
        assert result == "Final response with tool result"
        assert mock_client.chat.completions.create.call_count == 2


@pytest.mark.unit
def test_agent_analytics_integration():
    agent_id = uuid.uuid4()
    
    system_prompt = PromptObject(
        pid=uuid.uuid4(),
        prompt_label="AnalyticsPrompt",
        prompt="You are an agent with analytics.",
        sha_hash="dummy_hash",
        uniqueLabel="analytics_prompt",
        appName="agent_studio",
        version="1.0.0",
        createdTime=datetime.now(),
        deployedTime=None,
        last_deployed=None,
        modelProvider="OpenAI",
        modelName="gpt-4o-mini",
        isDeployed=True,
        tags=["analytics"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    )
    
    agent = Agent(
        agent_id=agent_id,
        name="AnalyticsAgent",
        system_prompt=system_prompt,
        persona="Analytics User",
        functions=[],
        routing_options={"respond": "Respond to the user"},
        failure_strategies=["retry"],
    )
    
    with patch('utils.client') as mock_client, \
         patch('services.analytics_service.analytics_service') as mock_analytics, \
         patch('db.database.get_db') as mock_get_db:
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].finish_reason = "stop"
        mock_response.choices[0].message.content = "Analytics response"
        mock_response.choices[0].message.tool_calls = None
        mock_client.chat.completions.create.return_value = mock_response
        
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value="execution_id_123")
        mock_context.__exit__ = Mock(return_value=None)
        mock_analytics.track_agent_execution.return_value = mock_context
        
        mock_get_db.return_value = iter([Mock()]) 
        
        result = agent.execute("Test with analytics", enable_analytics=True)
        
        assert result == "Analytics response"
        mock_analytics.track_agent_execution.assert_called_once()
