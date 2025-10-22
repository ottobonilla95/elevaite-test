import pytest
from fastapi.testclient import TestClient

from db.fixtures import DEFAULT_PROMPTS, DEFAULT_AGENTS, AGENT_CODES


@pytest.mark.functional
class TestDemoEndpoints:
    def test_demo_info_endpoint(self, test_client: TestClient):
        """Test the /demo/info endpoint returns correct information."""
        response = test_client.get("/demo/info")

        assert response.status_code == 200
        data = response.json()

        assert "available_prompts" in data
        assert "available_agents" in data
        assert "deployment_codes" in data

        assert len(data["available_prompts"]) == len(DEFAULT_PROMPTS)
        assert len(data["available_agents"]) == len(DEFAULT_AGENTS)
        assert data["deployment_codes"] == AGENT_CODES

        for prompt in data["available_prompts"]:
            assert "label" in prompt
            assert "unique_label" in prompt
            assert "description" in prompt

        for agent in data["available_agents"]:
            assert "name" in agent
            assert "persona" in agent
            assert "deployment_code" in agent
            assert "capabilities" in agent
            assert "short_term_memory" in agent["capabilities"]
            assert "long_term_memory" in agent["capabilities"]
            assert "reasoning" in agent["capabilities"]

    def test_demo_status_endpoint_empty(self, test_client: TestClient):
        response = test_client.get("/demo/status")

        assert response.status_code == 200
        data = response.json()

        assert data["prompts_initialized"] is False
        assert data["agents_initialized"] is False
        assert data["total_prompts"] == 0
        assert data["total_agents"] == 0
        assert data["available_deployment_codes"] == {}

    def test_demo_initialize_prompts_endpoint(self, test_client: TestClient):
        response = test_client.post("/demo/initialize/prompts")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "Successfully processed" in data["message"]
        assert "details" in data
        assert "prompts" in data["details"]

        prompts_details = data["details"]["prompts"]
        assert prompts_details["added_count"] == len(DEFAULT_PROMPTS)
        assert prompts_details["skipped_count"] == 0
        assert len(prompts_details["added_prompts"]) == len(DEFAULT_PROMPTS)

    def test_demo_initialize_agents_endpoint(
        self, test_client: TestClient, test_db_session
    ):
        test_client.post("/demo/initialize/prompts")

        response = test_client.post("/demo/initialize/agents")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "Successfully processed" in data["message"]
        assert "details" in data
        assert "agents" in data["details"]

        agents_details = data["details"]["agents"]
        assert agents_details["added_count"] == len(DEFAULT_AGENTS)
        assert agents_details["skipped_count"] == 0
        assert len(agents_details["added_agents"]) == len(DEFAULT_AGENTS)

    def test_demo_initialize_all_endpoint(self, test_client: TestClient):
        response = test_client.post("/demo/initialize")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["message"] == "Successfully initialized demo data."
        assert "details" in data
        assert "prompts" in data["details"]
        assert "agents" in data["details"]

        prompts_details = data["details"]["prompts"]
        assert prompts_details["added_count"] == len(DEFAULT_PROMPTS)

        agents_details = data["details"]["agents"]
        assert agents_details["added_count"] == len(DEFAULT_AGENTS)

    def test_demo_status_after_initialization(self, test_client: TestClient):
        test_client.post("/demo/initialize")

        response = test_client.get("/demo/status")

        assert response.status_code == 200
        data = response.json()

        assert data["prompts_initialized"] is True
        assert data["agents_initialized"] is True
        assert data["total_prompts"] == len(DEFAULT_PROMPTS)
        assert data["total_agents"] == len(DEFAULT_AGENTS)
        assert len(data["available_deployment_codes"]) == len(AGENT_CODES)

        for agent_name, code in AGENT_CODES.items():
            assert code in data["available_deployment_codes"]
            assert data["available_deployment_codes"][code] == agent_name

    def test_demo_initialize_idempotent(self, test_client: TestClient):
        response1 = test_client.post("/demo/initialize")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["success"] is True

        response2 = test_client.post("/demo/initialize")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["success"] is True

        prompts_details = data2["details"]["prompts"]
        agents_details = data2["details"]["agents"]

        assert prompts_details["added_count"] == 0
        assert prompts_details["skipped_count"] == len(DEFAULT_PROMPTS)
        assert agents_details["added_count"] == 0
        assert agents_details["skipped_count"] == len(DEFAULT_AGENTS)

    def test_demo_agents_without_prompts_fails(self, test_client: TestClient):
        response = test_client.post("/demo/initialize/agents")

        assert response.status_code == 500
