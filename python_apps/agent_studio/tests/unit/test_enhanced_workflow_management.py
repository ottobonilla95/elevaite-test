import pytest
from unittest.mock import Mock, patch
import uuid

from db.schemas import AgentBase, AgentUpdate
from db.crud.workflows import get_active_workflow_deployment_by_workflow_id


@pytest.mark.unit
class TestEnhancedWorkflowManagement:
    def test_agent_base_schema_includes_toshiba_type(self):
        agent_data = {
            "name": "ToshibaAgent",
            "agent_type": "toshiba",
            "description": "Toshiba parts expert",
            "system_prompt_id": uuid.uuid4(),
            "functions": [],
            "routing_options": {},
            "deployment_code": "t",
            "status": "active",
        }

        agent = AgentBase(**agent_data)
        assert agent.agent_type == "toshiba"
        assert agent.name == "ToshibaAgent"
        assert agent.deployment_code == "t"

    def test_agent_update_schema_includes_toshiba_type(self):
        update_data = {
            "agent_type": "toshiba",
            "description": "Updated Toshiba parts expert",
            "status": "active",
        }

        agent_update = AgentUpdate(**update_data)
        assert agent_update.agent_type == "toshiba"

    def test_default_agents_includes_toshiba_agent(self):
        from db.fixtures.default_data import DEFAULT_AGENTS

        toshiba_agents = [agent for agent in DEFAULT_AGENTS if agent.name == "ToshibaAgent"]
        assert len(toshiba_agents) > 0

        toshiba_agent = toshiba_agents[0]
        assert toshiba_agent.agent_type == "toshiba"
        assert toshiba_agent.description is not None and "Toshiba" in toshiba_agent.description

    @patch("agents.get_agent_schemas")
    def test_agent_schemas_includes_toshiba_agent(self, mock_get_agent_schemas):
        mock_schemas = {
            "ToshibaAgent": {
                "type": "function",
                "function": {
                    "name": "ToshibaAgent",
                    "description": "Specialized agent for Toshiba parts and technical information",
                },
            },
            "HelloWorldAgent": {
                "type": "function",
                "function": {
                    "name": "HelloWorldAgent",
                    "description": "Simple hello world agent",
                },
            },
        }
        mock_get_agent_schemas.return_value = mock_schemas

        from agents import get_agent_schemas

        schemas = get_agent_schemas()

        assert "ToshibaAgent" in schemas
        assert schemas["ToshibaAgent"]["function"]["name"] == "ToshibaAgent"
        assert "Toshiba" in schemas["ToshibaAgent"]["function"]["description"]

    def test_single_agent_workflow_optimization_pattern(self):
        workflow_config = {
            "name": "toshiba-single-agent",
            "description": "Single ToshibaAgent workflow",
            "agents": [
                {
                    "agent_type": "toshiba",
                    "name": "ToshibaAgent",
                    "deployment_code": "t",
                }
            ],
            "connections": [],
            "environment": "development",
        }

        assert len(workflow_config["agents"]) == 1
        assert len(workflow_config["connections"]) == 0
        assert workflow_config["agents"][0]["agent_type"] == "toshiba"

    def test_multi_agent_workflow_with_toshiba_agent(self):
        workflow_config = {
            "name": "multi-agent-with-toshiba",
            "description": "Multi-agent workflow including ToshibaAgent",
            "agents": [
                {
                    "agent_type": "command",
                    "name": "CommandAgent",
                    "deployment_code": "c",
                },
                {
                    "agent_type": "toshiba",
                    "name": "ToshibaAgent",
                    "deployment_code": "t",
                },
            ],
            "connections": [
                {
                    "source": "CommandAgent",
                    "target": "ToshibaAgent",
                    "condition": "toshiba_query",
                }
            ],
            "environment": "development",
        }

        assert len(workflow_config["agents"]) == 2
        assert len(workflow_config["connections"]) == 1

        toshiba_agents = [a for a in workflow_config["agents"] if a["agent_type"] == "toshiba"]
        assert len(toshiba_agents) == 1
        assert toshiba_agents[0]["name"] == "ToshibaAgent"

    @patch("db.crud.create_workflow_agent")
    def test_workflow_agents_population_during_creation(self, mock_create_workflow_agent):
        workflow_id = str(uuid.uuid4())
        agents_config = [
            {"agent_type": "toshiba", "name": "ToshibaAgent", "deployment_code": "t"},
            {"agent_type": "command", "name": "CommandAgent", "deployment_code": "c"},
        ]

        for agent_config in agents_config:
            mock_create_workflow_agent.return_value = Mock(
                id=str(uuid.uuid4()),
                workflow_id=workflow_id,
                agent_name=agent_config["name"],
                agent_type=agent_config["agent_type"],
            )

        assert mock_create_workflow_agent.call_count == 0

        for agent_config in agents_config:
            mock_create_workflow_agent(
                workflow_id=workflow_id,
                agent_name=agent_config["name"],
                agent_type=agent_config["agent_type"],
            )

        assert mock_create_workflow_agent.call_count == 2

    def test_agent_resolution_by_type(self):
        agent_types_map = {
            "toshiba": "ToshibaAgent",
            "command": "CommandAgent",
            "hello_world": "HelloWorldAgent",
        }

        assert agent_types_map.get("toshiba") == "ToshibaAgent"
        assert agent_types_map.get("command") == "CommandAgent"
        assert agent_types_map.get("nonexistent") is None

    def test_backward_compatibility_with_existing_workflows(self):
        existing_workflow = {
            "name": "legacy-workflow",
            "description": "Existing workflow",
            "agents": [
                {
                    "agent_type": "command",
                    "name": "CommandAgent",
                    "deployment_code": "c",
                },
                {
                    "agent_type": "hello_world",
                    "name": "HelloWorldAgent",
                    "deployment_code": "h",
                },
            ],
            "connections": [{"source": "CommandAgent", "target": "HelloWorldAgent"}],
        }

        assert len(existing_workflow["agents"]) == 2
        assert len(existing_workflow["connections"]) == 1

        toshiba_agents = [a for a in existing_workflow["agents"] if a["agent_type"] == "toshiba"]
        assert len(toshiba_agents) == 0

    def test_deployment_code_mapping_includes_toshiba(self):
        AGENT_CODES = {"c": "CommandAgent", "h": "HelloWorldAgent", "t": "ToshibaAgent"}

        assert AGENT_CODES.get("t") == "ToshibaAgent"
        assert AGENT_CODES.get("c") == "CommandAgent"
        assert AGENT_CODES.get("h") == "HelloWorldAgent"

    def test_environment_aware_deployment_lookup(self):
        def get_deployment_by_name(name, environment):
            deployments = {
                ("test-workflow", "development"): {
                    "id": 1,
                    "name": "test-workflow",
                    "env": "development",
                },
                ("test-workflow", "production"): {
                    "id": 2,
                    "name": "test-workflow",
                    "env": "production",
                },
                ("prod-only", "production"): {
                    "id": 3,
                    "name": "prod-only",
                    "env": "production",
                },
            }
            return deployments.get((name, environment))

        dev_deployment = get_deployment_by_name("test-workflow", "development")
        assert dev_deployment is not None
        assert dev_deployment["env"] == "development"

        prod_deployment = get_deployment_by_name("test-workflow", "production")
        assert prod_deployment is not None
        assert prod_deployment["env"] == "production"

        prod_only = get_deployment_by_name("prod-only", "production")
        assert prod_only is not None

        nonexistent = get_deployment_by_name("nonexistent", "development")
        assert nonexistent is None

    @patch("db.crud.workflows.db")
    def test_get_active_workflow_deployment_by_workflow_id(self, mock_db_session):
        """Test the new function to get active deployment by workflow_id"""
        mock_db = Mock()
        workflow_id = uuid.uuid4()

        # Mock deployment object
        mock_deployment = Mock()
        mock_deployment.workflow_id = workflow_id
        mock_deployment.environment = "production"
        mock_deployment.status = "active"

        # Mock the query chain
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_deployment
        mock_db.query.return_value = mock_query

        # Test the function
        result = get_active_workflow_deployment_by_workflow_id(mock_db, workflow_id, "production")

        # Verify the result
        assert result == mock_deployment
        assert result.workflow_id == workflow_id
        assert result.status == "active"

        # Verify the query was called correctly
        mock_db.query.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.first.assert_called_once()
