import pytest
from fastapi.testclient import TestClient

from db import models, crud
from db.fixtures import DEFAULT_PROMPTS, DEFAULT_AGENTS, AGENT_CODES
from services.demo_service import DemoInitializationService


@pytest.mark.integration
class TestDemoIntegration:
    def test_full_demo_workflow(self, test_client: TestClient, test_db_session):
        response = test_client.get("/demo/status")
        assert response.status_code == 200
        data = response.json()
        assert data["prompts_initialized"] is False
        assert data["agents_initialized"] is False

        response = test_client.post("/demo/initialize")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        response = test_client.get("/demo/status")
        assert response.status_code == 200
        data = response.json()
        assert data["prompts_initialized"] is True
        assert data["agents_initialized"] is True
        assert data["total_prompts"] == len(DEFAULT_PROMPTS)
        assert data["total_agents"] == len(DEFAULT_AGENTS)

        prompts_count = test_db_session.query(models.Prompt).count()
        agents_count = test_db_session.query(models.Agent).count()
        assert prompts_count == len(DEFAULT_PROMPTS)
        assert agents_count == len(DEFAULT_AGENTS)

        agents_with_codes = (
            test_db_session.query(models.Agent)
            .filter(models.Agent.deployment_code.isnot(None))
            .all()
        )
        assert len(agents_with_codes) == len(DEFAULT_AGENTS)

        response = test_client.get("/api/prompts/")
        assert response.status_code == 200
        prompts_data = response.json()
        assert len(prompts_data) == len(DEFAULT_PROMPTS)

        response = test_client.get("/api/agents/")
        assert response.status_code == 200
        agents_data = response.json()
        assert len(agents_data) == len(DEFAULT_AGENTS)

        response = test_client.get("/api/agents/deployment/codes")
        assert response.status_code == 200
        codes_data = response.json()
        assert len(codes_data) == len(AGENT_CODES)

    def test_service_layer_integration(self, test_db_session):
        service = DemoInitializationService(test_db_session)

        success, message, details = service.initialize_prompts()
        assert success is True
        assert details["added_count"] == len(DEFAULT_PROMPTS)

        prompts_count = test_db_session.query(models.Prompt).count()
        assert prompts_count == len(DEFAULT_PROMPTS)

        success, message, details = service.initialize_agents()
        assert success is True
        assert details["added_count"] == len(DEFAULT_AGENTS)

        agents_count = test_db_session.query(models.Agent).count()
        assert agents_count == len(DEFAULT_AGENTS)

        for agent_name, expected_code in AGENT_CODES.items():
            agent = (
                test_db_session.query(models.Agent)
                .filter(models.Agent.name == agent_name)
                .first()
            )
            assert agent is not None
            assert agent.deployment_code == expected_code

    def test_crud_operations_integration(
        self, test_db_session, sample_prompt_data, sample_agent_data
    ):
        from db.schemas import PromptCreate

        prompt_create = PromptCreate(**sample_prompt_data)
        created_prompt = crud.create_prompt(test_db_session, prompt_create)

        assert created_prompt.prompt_label == sample_prompt_data["prompt_label"]
        assert created_prompt.unique_label == sample_prompt_data["unique_label"]

        from db.schemas import AgentCreate

        sample_agent_data["system_prompt_id"] = created_prompt.pid
        agent_create = AgentCreate(**sample_agent_data)
        created_agent = crud.create_agent(test_db_session, agent_create)

        assert created_agent.name == sample_agent_data["name"]
        assert created_agent.deployment_code == sample_agent_data["deployment_code"]

        retrieved_prompt = crud.get_prompt(test_db_session, created_prompt.id)
        assert retrieved_prompt.id == created_prompt.id

        retrieved_agent = crud.get_agent(test_db_session, created_agent.id)
        assert retrieved_agent.id == created_agent.id

    def test_error_handling_integration(self, test_client: TestClient):
        response = test_client.post("/demo/initialize/agents")
        assert response.status_code == 500

        response = test_client.post("/demo/initialize/prompts")
        assert response.status_code == 200

        response = test_client.post("/demo/initialize/agents")
        assert response.status_code == 200

    def test_concurrent_initialization(self, test_client: TestClient):
        response1 = test_client.post("/demo/initialize")
        assert response1.status_code == 200

        response2 = test_client.post("/demo/initialize")
        assert response2.status_code == 200

        data1 = response1.json()
        data2 = response2.json()

        assert data1["success"] is True
        assert data2["success"] is True

        assert data2["details"]["prompts"]["skipped_count"] > 0
        assert data2["details"]["agents"]["skipped_count"] > 0

    def test_api_consistency_after_demo_init(self, test_client: TestClient):
        response = test_client.post("/demo/initialize")
        assert response.status_code == 200

        demo_status = test_client.get("/demo/status").json()
        api_prompts = test_client.get("/api/prompts/").json()
        api_agents = test_client.get("/api/agents/").json()
        deployment_codes = test_client.get("/api/agents/deployment/codes").json()

        assert demo_status["total_prompts"] == len(api_prompts)
        assert demo_status["total_agents"] == len(api_agents)
        assert len(demo_status["available_deployment_codes"]) == len(deployment_codes)

        for code, agent_name in demo_status["available_deployment_codes"].items():
            assert code in deployment_codes
            assert deployment_codes[code] == agent_name
