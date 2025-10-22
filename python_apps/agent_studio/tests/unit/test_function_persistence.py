import pytest
import uuid
from sqlalchemy.orm import Session

from db.database import SessionLocal, engine, Base
from db import crud, schemas
from agents.tools import tool_schemas
from prompts import data_agent_system_prompt


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_prompt(db_session: Session):
    prompt_data = schemas.PromptCreate(
        prompt_label="test_prompt",
        prompt=data_agent_system_prompt.prompt,
        unique_label=f"test_prompt_{uuid.uuid4()}",
        app_name="test_app",
        version="1.0.0",
        ai_model_provider="openai",
        ai_model_name="gpt-4o-mini",
    )

    prompt = crud.create_prompt(db_session, prompt_data)
    yield prompt

    crud.delete_prompt(db_session, prompt.pid)


class TestFunctionValidation:
    def test_validate_known_functions(self):
        functions = [
            tool_schemas["web_search"],
            tool_schemas["get_customer_order"],
            tool_schemas["add_customer"],
        ]

        validated = crud.validate_agent_functions(functions)

        assert len(validated) == 3
        for func in validated:
            assert isinstance(func, dict)
            assert "function" in func
            assert "name" in func["function"]
            assert func["function"]["name"] in [
                "web_search",
                "get_customer_order",
                "add_customer",
            ]

    def test_validate_unknown_functions(self):
        functions = [
            {
                "type": "function",
                "function": {
                    "name": "custom_function",
                    "description": "A custom function",
                    "parameters": {"type": "object", "properties": {}},
                },
            }
        ]

        validated = crud.validate_agent_functions(functions)

        assert len(validated) == 1
        assert validated[0]["function"]["name"] == "custom_function"

    def test_validate_mixed_functions(self):
        functions = [
            tool_schemas["web_search"],  # Known
            {
                "type": "function",
                "function": {
                    "name": "custom_function",
                    "description": "Custom",
                    "parameters": {"type": "object", "properties": {}},
                },
            },  # Unknown but valid
            {"invalid": "schema"},  # Invalid but preserved
        ]

        validated = crud.validate_agent_functions(functions)

        assert len(validated) == 3
        assert validated[0]["function"]["name"] == "web_search"
        assert validated[1]["function"]["name"] == "custom_function"
        assert "invalid" in validated[2]


class TestAgentCreation:
    def test_create_agent_with_functions(self, db_session: Session, test_prompt):
        functions = [tool_schemas["get_customer_order"], tool_schemas["web_search"]]

        agent_data = schemas.AgentCreate(
            name="TestAgent",
            system_prompt_id=test_prompt.pid,
            persona="Test Agent",
            functions=functions,
            routing_options={"continue": "Continue", "respond": "Respond"},
            deployment_code="test_a",
        )

        agent = crud.create_agent(db_session, agent_data)

        assert agent.name == "TestAgent"
        assert len(agent.functions) == 2

        function_names = []
        for func in agent.functions:
            if isinstance(func, dict) and "function" in func:
                function_names.append(func["function"]["name"])

        assert "get_customer_order" in function_names
        assert "web_search" in function_names

        crud.delete_agent(db_session, agent.agent_id)

    def test_create_agent_validates_functions(self, db_session: Session, test_prompt):
        functions = [
            tool_schemas["web_search"],  # Valid
            {"invalid": "function"},  # Invalid but should be preserved
        ]

        agent_data = schemas.AgentCreate(
            name="TestValidationAgent",
            system_prompt_id=test_prompt.pid,
            persona="Test Agent",
            functions=functions,
            routing_options={"continue": "Continue"},
            deployment_code="test_v",
        )

        agent = crud.create_agent(db_session, agent_data)

        assert len(agent.functions) == 2

        assert agent.functions[0]["function"]["name"] == "web_search"
        assert "invalid" in agent.functions[1]

        crud.delete_agent(db_session, agent.agent_id)


class TestFunctionReconstruction:
    def test_get_agent_with_functions(self, db_session: Session, test_prompt):
        functions = [tool_schemas["get_customer_order"], tool_schemas["add_customer"]]

        agent_data = schemas.AgentCreate(
            name="ReconstructionTestAgent",
            system_prompt_id=test_prompt.pid,
            persona="Test Agent",
            functions=functions,
            routing_options={"continue": "Continue"},
            deployment_code="test_r",
        )

        created_agent = crud.create_agent(db_session, agent_data)

        retrieved_agent = crud.get_agent_with_functions(
            db_session, created_agent.agent_id
        )

        assert retrieved_agent is not None
        assert retrieved_agent.name == "ReconstructionTestAgent"
        assert len(retrieved_agent.functions) == 2

        function_names = []
        for func in retrieved_agent.functions:
            if isinstance(func, dict) and "function" in func:
                function_names.append(func["function"]["name"])

        assert "get_customer_order" in function_names
        assert "add_customer" in function_names

        crud.delete_agent(db_session, created_agent.agent_id)

    def test_get_agent_by_name_with_functions(self, db_session: Session, test_prompt):
        functions = [tool_schemas["web_search"]]

        agent_data = schemas.AgentCreate(
            name="NameRetrievalAgent",
            system_prompt_id=test_prompt.pid,
            persona="Test Agent",
            functions=functions,
            routing_options={"continue": "Continue"},
            deployment_code="test_n",
        )

        created_agent = crud.create_agent(db_session, agent_data)

        retrieved_agent = crud.get_agent_by_name_with_functions(
            db_session, "NameRetrievalAgent"
        )

        assert retrieved_agent is not None
        assert retrieved_agent.name == "NameRetrievalAgent"
        assert len(retrieved_agent.functions) == 1
        assert retrieved_agent.functions[0]["function"]["name"] == "web_search"

        crud.delete_agent(db_session, created_agent.agent_id)

    def test_nonexistent_agent_returns_none(self, db_session: Session):
        fake_id = uuid.uuid4()

        result = crud.get_agent_with_functions(db_session, fake_id)
        assert result is None

        result = crud.get_agent_by_name_with_functions(db_session, "NonexistentAgent")
        assert result is None


class TestFunctionPersistenceIntegration:
    def test_complete_workflow(self, db_session: Session, test_prompt):
        original_functions = [
            tool_schemas["web_search"],
            tool_schemas["get_customer_order"],
            tool_schemas["weather_forecast"],
        ]

        agent_data = schemas.AgentCreate(
            name="WorkflowTestAgent",
            system_prompt_id=test_prompt.pid,
            persona="Workflow Test Agent",
            functions=original_functions,
            routing_options={
                "continue": "Continue to next tool",
                "respond": "Provide response",
                "give_up": "Give up",
            },
            deployment_code="test_w",
            available_for_deployment=True,
        )

        created_agent = crud.create_agent(db_session, agent_data)
        assert created_agent.name == "WorkflowTestAgent"
        assert len(created_agent.functions) == 3

        raw_agent = crud.get_agent(db_session, created_agent.agent_id)
        assert raw_agent is not None
        assert len(raw_agent.functions) == 3

        reconstructed_agent = crud.get_agent_with_functions(
            db_session, created_agent.agent_id
        )
        assert reconstructed_agent is not None
        assert len(reconstructed_agent.functions) == 3

        function_names = []
        for func in reconstructed_agent.functions:
            if isinstance(func, dict) and "function" in func:
                function_names.append(func["function"]["name"])

        expected_names = ["web_search", "get_customer_order", "weather_forecast"]
        for name in expected_names:
            assert name in function_names

        by_name_agent = crud.get_agent_by_name_with_functions(
            db_session, "WorkflowTestAgent"
        )
        assert by_name_agent is not None
        assert by_name_agent.agent_id == created_agent.agent_id
        assert len(by_name_agent.functions) == 3

        crud.delete_agent(db_session, created_agent.agent_id)

    def test_deployment_code_retrieval(self, db_session: Session, test_prompt):
        functions = [tool_schemas["add_customer"]]

        agent_data = schemas.AgentCreate(
            name="DeploymentCodeAgent",
            system_prompt_id=test_prompt.pid,
            persona="Test Agent",
            functions=functions,
            routing_options={"continue": "Continue"},
            deployment_code="deploy_test",
            available_for_deployment=True,
        )

        created_agent = crud.create_agent(db_session, agent_data)

        retrieved_agent = crud.get_agent_by_deployment_code(db_session, "deploy_test")
        assert retrieved_agent is not None
        assert retrieved_agent.name == "DeploymentCodeAgent"

        agent_with_functions = crud.get_agent_with_functions(
            db_session, retrieved_agent.agent_id
        )
        assert agent_with_functions is not None
        assert len(agent_with_functions.functions) == 1
        assert agent_with_functions.functions[0]["function"]["name"] == "add_customer"

        crud.delete_agent(db_session, created_agent.agent_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
