import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from db.database import SessionLocal, engine, Base
from db import crud, schemas
from agents.tools import tool_schemas
from prompts import data_agent_system_prompt, command_agent_system_prompt


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_agents(db_session: Session):
    command_prompt_data = schemas.PromptCreate(
        prompt_label="command_agent_prompt",
        prompt=command_agent_system_prompt,
        unique_label=f"command_prompt_{uuid.uuid4()}",
        app_name="test_app",
        version="1.0.0",
        ai_model_provider="openai",
        ai_model_name="gpt-4o-mini",
    )
    command_prompt = crud.create_prompt(db_session, command_prompt_data)

    data_prompt_data = schemas.PromptCreate(
        prompt_label="data_agent_prompt",
        prompt=data_agent_system_prompt,
        unique_label=f"data_prompt_{uuid.uuid4()}",
        app_name="test_app",
        version="1.0.0",
        ai_model_provider="openai",
        ai_model_name="gpt-4o-mini",
    )
    data_prompt = crud.create_prompt(db_session, data_prompt_data)

    command_agent_data = schemas.AgentCreate(
        name="CommandAgent",
        system_prompt_id=command_prompt.pid,
        persona="Command Agent",
        functions=[],  # CommandAgent typically has no functions initially
        routing_options={
            "continue": "Continue to next tool",
            "respond": "Provide response",
            "give_up": "Give up",
        },
        deployment_code="c",
        available_for_deployment=True,
    )
    command_agent = crud.create_agent(db_session, command_agent_data)

    data_agent_functions = [
        tool_schemas["get_customer_order"],
        tool_schemas["get_customer_location"],
        tool_schemas["add_customer"],
    ]

    data_agent_data = schemas.AgentCreate(
        name="DataAgent",
        system_prompt_id=data_prompt.pid,
        persona="Data Agent",
        functions=data_agent_functions,
        routing_options={
            "continue": "Continue to next tool",
            "respond": "Provide response",
            "give_up": "Give up",
        },
        deployment_code="d",
        available_for_deployment=True,
    )
    data_agent = crud.create_agent(db_session, data_agent_data)

    web_agent_functions = [tool_schemas["web_search"], tool_schemas["url_to_markdown"]]

    web_agent_data = schemas.AgentCreate(
        name="WebAgent",
        system_prompt_id=data_prompt.pid,  # Reuse data prompt for simplicity
        persona="Web Agent",
        functions=web_agent_functions,
        routing_options={
            "continue": "Continue to next tool",
            "respond": "Provide response",
            "give_up": "Give up",
        },
        deployment_code="w",
        available_for_deployment=True,
    )
    web_agent = crud.create_agent(db_session, web_agent_data)

    agents = {"command": command_agent, "data": data_agent, "web": web_agent}

    yield agents

    for agent in agents.values():
        crud.delete_agent(db_session, agent.agent_id)
    crud.delete_prompt(db_session, command_prompt.pid)
    crud.delete_prompt(db_session, data_prompt.pid)


class TestDeploymentFunctionPersistence:
    def test_deploy_with_database_functions(self, client: TestClient, test_agents):
        deploy_request = {
            "agents": [["c"], ["d"]],  # CommandAgent and DataAgent
            "connections": ["c->DataAgent"],  # CommandAgent connects to DataAgent
        }

        response = client.post("/deploy", json=deploy_request)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "response: ok"

    def test_deploy_multiple_connections(self, client: TestClient, test_agents):
        deploy_request = {
            "agents": [["c"], ["d"], ["w"]],  # CommandAgent, DataAgent, WebAgent
            "connections": ["c->DataAgent", "c->WebAgent"],
        }

        response = client.post("/deploy", json=deploy_request)

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "response: ok"

    def test_deploy_nonexistent_agent(self, client: TestClient, test_agents):
        deploy_request = {
            "agents": [["c"], ["x"]],  # x doesn't exist
            "connections": ["c->NonexistentAgent"],
        }

        response = client.post("/deploy", json=deploy_request)

        assert response.status_code == 200
        result = response.json()
        assert "Error" in result["status"]
        assert "not found" in result["status"]

    def test_run_deployed_agent(self, client: TestClient, test_agents):
        deploy_request = {"agents": [["c"], ["d"]], "connections": ["c->DataAgent"]}

        deploy_response = client.post("/deploy", json=deploy_request)
        assert deploy_response.status_code == 200

        run_request = {
            "query": "Get customer information for customer ID 123",
            "session_id": str(uuid.uuid4()),
            "user_id": "test_user",
        }

        run_response = client.post("/run", json=run_request)

        assert run_response.status_code == 200
        result = run_response.json()
        assert result["status"] == "ok"
        assert "response" in result
        assert "session_id" in result


class TestDeploymentCodeMapping:
    def test_get_deployment_codes(self, client: TestClient, test_agents):
        response = client.get("/deployment/codes")

        assert response.status_code == 200
        codes = response.json()

        assert "c" in codes
        assert "d" in codes
        assert "w" in codes

        assert codes["c"] == "CommandAgent"
        assert codes["d"] == "DataAgent"
        assert codes["w"] == "WebAgent"

    def test_get_available_agents(self, client: TestClient, test_agents):
        response = client.get("/api/agents/deployment/available")

        assert response.status_code == 200
        agents = response.json()

        assert isinstance(agents, list)
        assert len(agents) >= 3  # At least our test agents

        agent_names = [agent["name"] for agent in agents]
        assert "CommandAgent" in agent_names
        assert "DataAgent" in agent_names
        assert "WebAgent" in agent_names


class TestFunctionReconstructionInDeployment:
    def test_function_reconstruction_logging(
        self, client: TestClient, test_agents, capfd
    ):
        deploy_request = {"agents": [["c"], ["d"]], "connections": ["c->DataAgent"]}

        response = client.post("/deploy", json=deploy_request)
        assert response.status_code == 200

        captured = capfd.readouterr()

        assert (
            "Using database functions for DataAgent" in captured.out
            or "functions" in captured.out.lower()
        )

    def test_fallback_to_hardcoded_schemas(self, client: TestClient, test_agents):
        deploy_request = {
            "agents": [["c"]],
            "connections": ["c->APIAgent"],  # APIAgent might exist in hardcoded schemas
        }

        response = client.post("/deploy", json=deploy_request)

        assert response.status_code == 200
        result = response.json()
        assert "status" in result


class TestDeploymentIntegration:
    def test_end_to_end_deployment_and_execution(self, client: TestClient, test_agents):
        deploy_request = {
            "agents": [["c"], ["d"], ["w"]],
            "connections": ["c->DataAgent", "c->WebAgent"],
        }

        deploy_response = client.post("/deploy", json=deploy_request)
        assert deploy_response.status_code == 200
        assert deploy_response.json()["status"] == "response: ok"

        codes_response = client.get("/deployment/codes")
        assert codes_response.status_code == 200
        codes = codes_response.json()
        assert "c" in codes
        assert "d" in codes
        assert "w" in codes

        run_request = {
            "query": "Search for information about customer orders",
            "session_id": str(uuid.uuid4()),
            "user_id": "test_user",
        }

        run_response = client.post("/run", json=run_request)
        assert run_response.status_code == 200

        result = run_response.json()
        assert result["status"] == "ok"
        assert "response" in result
        assert "session_id" in result

        health_response = client.get("/hc")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
