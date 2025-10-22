import pytest
from unittest.mock import Mock, patch
import json
import uuid
from datetime import datetime

from agents.toshiba_agent import ToshibaAgent, create_toshiba_agent
from data_classes import PromptObject


def create_test_prompt_object(prompt_text="You are a Toshiba expert"):
    return PromptObject(
        pid=uuid.uuid4(),
        prompt_label="test_toshiba_prompt",
        prompt=prompt_text,
        sha_hash="test_hash",
        uniqueLabel="test_unique_label",
        appName="agent_studio",
        version="1.0",
        createdTime=datetime.now(),
        deployedTime=None,
        last_deployed=None,
        modelProvider="openai",
        modelName="gpt-4o",
        isDeployed=False,
        tags=["test"],
        hyper_parameters={"temperature": "0.7"},
        variables={},
    )


@pytest.mark.unit
class TestToshibaAgent:
    def test_toshiba_agent_initialization(self):
        system_prompt = create_test_prompt_object()

        functions = [{"type": "function", "function": {"name": "test_tool"}}]
        routing_options = {
            "continue": "Continue processing",
            "respond": "Respond to user",
        }

        agent = ToshibaAgent(
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

        assert agent.name == "ToshibaAgent"
        assert agent.persona == "Toshiba Expert"
        assert agent.functions == functions
        assert agent.routing_options == routing_options
        assert agent.max_retries == 3
        assert agent.response_type == "json"

    def test_create_toshiba_agent_factory(self):
        system_prompt = create_test_prompt_object()
        functions = []

        agent = create_toshiba_agent(system_prompt, functions)

        assert isinstance(agent, ToshibaAgent)
        assert agent.name == "ToshibaAgent"
        assert agent.persona == "Toshiba Expert"
        assert "ask" in agent.routing_options
        assert "continue" in agent.routing_options
        assert "give_up" in agent.routing_options

    def test_openai_schema_property(self):
        system_prompt = create_test_prompt_object()

        agent = create_toshiba_agent(system_prompt, [])
        schema = agent.openai_schema

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "ToshibaAgent"
        assert "description" in schema["function"]
        assert "parameters" in schema["function"]
        assert "query" in schema["function"]["parameters"]["properties"]
        assert "chat_history" in schema["function"]["parameters"]["properties"]
        assert "query" in schema["function"]["parameters"]["required"]

    @patch("agents.toshiba_agent.client")
    def test_execute_success_no_tools(self, mock_client):
        system_prompt = create_test_prompt_object()

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].finish_reason = "stop"
        mock_response.choices[0].message.content = (
            '{"routing": "respond", "content": "Test response"}'
        )
        mock_client.chat.completions.create.return_value = mock_response

        agent = create_toshiba_agent(system_prompt, [])
        result = agent.execute("What is a Toshiba elevator?")

        assert result == '{"routing": "respond", "content": "Test response"}'
        mock_client.chat.completions.create.assert_called_once()

    @patch("agents.toshiba_agent.client")
    @patch("agents.toshiba_agent.tool_store")
    def test_execute_with_tool_calls(self, mock_tool_store, mock_client):
        system_prompt = create_test_prompt_object()

        mock_tool_call = Mock()
        mock_tool_call.id = "tool_123"
        mock_tool_call.function.name = "search_parts"
        mock_tool_call.function.arguments = '{"query": "elevator motor"}'

        mock_response1 = Mock()
        mock_response1.choices = [Mock()]
        mock_response1.choices[0].finish_reason = "tool_calls"
        mock_response1.choices[0].message.tool_calls = [mock_tool_call]

        mock_response2 = Mock()
        mock_response2.choices = [Mock()]
        mock_response2.choices[0].finish_reason = "stop"
        mock_response2.choices[0].message.content = (
            '{"routing": "respond", "content": "Found motor info"}'
        )

        mock_client.chat.completions.create.side_effect = [
            mock_response1,
            mock_response2,
        ]
        mock_tool_store.__contains__.return_value = True
        mock_tool_store.__getitem__.return_value = lambda query: "Motor search results"

        agent = create_toshiba_agent(system_prompt, [])
        result = agent.execute("Find elevator motor")

        assert result == '{"routing": "respond", "content": "Found motor info"}'
        assert mock_client.chat.completions.create.call_count == 2

    @patch("agents.toshiba_agent.client")
    def test_execute_failure_max_retries(self, mock_client):
        system_prompt = create_test_prompt_object()

        mock_client.chat.completions.create.side_effect = Exception("API Error")

        agent = create_toshiba_agent(system_prompt, [])
        result = agent.execute("Test query")

        result_json = json.loads(result)
        assert result_json["routing"] == "failed"
        assert "Couldn't find the answer" in result_json["content"]
        assert mock_client.chat.completions.create.call_count == 3

    def test_chat_history_formatting(self):
        system_prompt = create_test_prompt_object()

        chat_history = [
            {"actor": "user", "content": "Hello"},
            {"actor": "assistant", "content": "Hi there"},
            {"actor": "user", "content": "What is Toshiba?"},
        ]

        with patch("agents.toshiba_agent.client") as mock_client:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].finish_reason = "stop"
            mock_response.choices[0].message.content = (
                '{"routing": "respond", "content": "Test"}'
            )
            mock_client.chat.completions.create.return_value = mock_response

            agent = create_toshiba_agent(system_prompt, [])
            agent.execute("New query", chat_history=chat_history)

            call_args = mock_client.chat.completions.create.call_args
            messages = call_args[1]["messages"]

            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            assistant_messages = [
                msg for msg in messages if msg.get("role") == "assistant"
            ]

            assert len(user_messages) >= 2
            assert len(assistant_messages) >= 1
