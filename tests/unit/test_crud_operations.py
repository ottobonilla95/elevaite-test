import pytest
import uuid
from unittest.mock import Mock
from sqlalchemy.orm import Session

from db import crud, models, schemas
from db.fixtures import DEFAULT_PROMPTS


class TestCrudOperations:
    """Test CRUD operations for better coverage."""

    def test_create_prompt(self, test_db_session):
        """Test creating a prompt."""
        prompt_data = DEFAULT_PROMPTS[0]
        prompt_create = schemas.PromptCreate(
            prompt_label=prompt_data.prompt_label,
            prompt=prompt_data.prompt,
            unique_label=prompt_data.unique_label,
            app_name=prompt_data.app_name,
            version=prompt_data.version,
            ai_model_provider=prompt_data.ai_model_provider,
            ai_model_name=prompt_data.ai_model_name,
            tags=prompt_data.tags,
            hyper_parameters=prompt_data.hyper_parameters,
            variables=prompt_data.variables,
        )

        db_prompt = crud.create_prompt(db=test_db_session, prompt=prompt_create)

        assert db_prompt.prompt_label == prompt_data.prompt_label
        assert db_prompt.unique_label == prompt_data.unique_label
        assert db_prompt.app_name == prompt_data.app_name

    def test_get_prompt_by_id(self, test_db_session):
        """Test retrieving a prompt by ID."""
        prompt_data = DEFAULT_PROMPTS[0]
        prompt_create = schemas.PromptCreate(
            prompt_label=prompt_data.prompt_label,
            prompt=prompt_data.prompt,
            unique_label=prompt_data.unique_label,
            app_name=prompt_data.app_name,
            version=prompt_data.version,
            ai_model_provider=prompt_data.ai_model_provider,
            ai_model_name=prompt_data.ai_model_name,
            tags=prompt_data.tags,
            hyper_parameters=prompt_data.hyper_parameters,
            variables=prompt_data.variables,
        )

        db_prompt = crud.create_prompt(db=test_db_session, prompt=prompt_create)

        # Test retrieval
        retrieved_prompt = crud.get_prompt(db=test_db_session, prompt_id=db_prompt.pid)
        assert retrieved_prompt is not None
        assert retrieved_prompt.pid == db_prompt.pid
        assert retrieved_prompt.prompt_label == prompt_data.prompt_label

    def test_get_prompt_by_app_and_label(self, test_db_session):
        """Test retrieving a prompt by app and label."""
        prompt_data = DEFAULT_PROMPTS[0]
        prompt_create = schemas.PromptCreate(
            prompt_label=prompt_data.prompt_label,
            prompt=prompt_data.prompt,
            unique_label=prompt_data.unique_label,
            app_name=prompt_data.app_name,
            version=prompt_data.version,
            ai_model_provider=prompt_data.ai_model_provider,
            ai_model_name=prompt_data.ai_model_name,
            tags=prompt_data.tags,
            hyper_parameters=prompt_data.hyper_parameters,
            variables=prompt_data.variables,
        )

        db_prompt = crud.create_prompt(db=test_db_session, prompt=prompt_create)

        # Test retrieval by app and label
        retrieved_prompts = crud.get_prompt_by_app_and_label(
            db=test_db_session,
            app_name=prompt_data.app_name,
            prompt_label=prompt_data.prompt_label,
        )
        assert len(retrieved_prompts) > 0
        assert retrieved_prompts[0].app_name == prompt_data.app_name

    def test_get_prompts_list(self, test_db_session):
        """Test retrieving a list of prompts."""
        # Create multiple prompts
        for i, prompt_data in enumerate(DEFAULT_PROMPTS[:3]):
            prompt_create = schemas.PromptCreate(
                prompt_label=f"{prompt_data.prompt_label}_{i}",
                prompt=prompt_data.prompt,
                unique_label=f"{prompt_data.unique_label}_{i}",
                app_name=prompt_data.app_name,
                version=prompt_data.version,
                ai_model_provider=prompt_data.ai_model_provider,
                ai_model_name=prompt_data.ai_model_name,
                tags=prompt_data.tags,
                hyper_parameters=prompt_data.hyper_parameters,
                variables=prompt_data.variables,
            )
            crud.create_prompt(db=test_db_session, prompt=prompt_create)

        # Test retrieval
        prompts = crud.get_prompts(db=test_db_session, skip=0, limit=10)
        assert len(prompts) == 3

    def test_update_prompt(self, test_db_session):
        """Test updating a prompt."""
        prompt_data = DEFAULT_PROMPTS[0]
        prompt_create = schemas.PromptCreate(
            prompt_label=prompt_data.prompt_label,
            prompt=prompt_data.prompt,
            unique_label=prompt_data.unique_label,
            app_name=prompt_data.app_name,
            version=prompt_data.version,
            ai_model_provider=prompt_data.ai_model_provider,
            ai_model_name=prompt_data.ai_model_name,
            tags=prompt_data.tags,
            hyper_parameters=prompt_data.hyper_parameters,
            variables=prompt_data.variables,
        )

        db_prompt = crud.create_prompt(db=test_db_session, prompt=prompt_create)

        # Update the prompt
        prompt_update = schemas.PromptUpdate(
            prompt_label="Updated Label", prompt="Updated prompt text"
        )

        updated_prompt = crud.update_prompt(
            db=test_db_session, prompt_id=db_prompt.pid, prompt_update=prompt_update
        )

        assert updated_prompt is not None
        assert updated_prompt.prompt_label == "Updated Label"
        assert updated_prompt.prompt == "Updated prompt text"

    def test_delete_prompt(self, test_db_session):
        """Test deleting a prompt."""
        prompt_data = DEFAULT_PROMPTS[0]
        prompt_create = schemas.PromptCreate(
            prompt_label=prompt_data.prompt_label,
            prompt=prompt_data.prompt,
            unique_label=prompt_data.unique_label,
            app_name=prompt_data.app_name,
            version=prompt_data.version,
            ai_model_provider=prompt_data.ai_model_provider,
            ai_model_name=prompt_data.ai_model_name,
            tags=prompt_data.tags,
            hyper_parameters=prompt_data.hyper_parameters,
            variables=prompt_data.variables,
        )

        db_prompt = crud.create_prompt(db=test_db_session, prompt=prompt_create)
        prompt_id = db_prompt.pid

        # Delete the prompt
        result = crud.delete_prompt(db=test_db_session, prompt_id=prompt_id)
        assert result is True

        # Verify it's deleted
        deleted_prompt = crud.get_prompt(db=test_db_session, prompt_id=prompt_id)
        assert deleted_prompt is None

    def test_get_agent_by_name(self, test_db_session):
        """Test retrieving an agent by name."""
        # Create a prompt first
        prompt_data = DEFAULT_PROMPTS[0]
        prompt_create = schemas.PromptCreate(
            prompt_label=prompt_data.prompt_label,
            prompt=prompt_data.prompt,
            unique_label=prompt_data.unique_label,
            app_name=prompt_data.app_name,
            version=prompt_data.version,
            ai_model_provider=prompt_data.ai_model_provider,
            ai_model_name=prompt_data.ai_model_name,
            tags=prompt_data.tags,
            hyper_parameters=prompt_data.hyper_parameters,
            variables=prompt_data.variables,
        )

        db_prompt = crud.create_prompt(db=test_db_session, prompt=prompt_create)

        # Create an agent
        agent_create = schemas.AgentCreate(
            name="TestAgent",
            system_prompt_id=uuid.UUID(str(db_prompt.pid)),
            persona="Test",
            functions=[],
            routing_options={"respond": "Test response"},
            short_term_memory=False,
            long_term_memory=False,
            reasoning=False,
            input_type=["text"],
            output_type=["text"],
            response_type="json",
            max_retries=3,
            timeout=None,
            deployed=False,
            status="active",
            priority=None,
            failure_strategies=["retry"],
            collaboration_mode="single",
            deployment_code="x",
            available_for_deployment=True,
        )

        db_agent = crud.create_agent(db=test_db_session, agent=agent_create)

        # Test retrieval by name
        found_agent = crud.get_agent_by_name(db=test_db_session, name="TestAgent")
        assert found_agent is not None
        assert found_agent.name == "TestAgent"
        assert found_agent.deployment_code == "x"

    def test_get_agents_with_filters(self, test_db_session):
        """Test retrieving agents with filters."""
        # Create a prompt first
        prompt_data = DEFAULT_PROMPTS[0]
        prompt_create = schemas.PromptCreate(
            prompt_label=prompt_data.prompt_label,
            prompt=prompt_data.prompt,
            unique_label=prompt_data.unique_label,
            app_name=prompt_data.app_name,
            version=prompt_data.version,
            ai_model_provider=prompt_data.ai_model_provider,
            ai_model_name=prompt_data.ai_model_name,
            tags=prompt_data.tags,
            hyper_parameters=prompt_data.hyper_parameters,
            variables=prompt_data.variables,
        )

        db_prompt = crud.create_prompt(db=test_db_session, prompt=prompt_create)

        # Create multiple agents with different deployment status
        for i, deployed in enumerate([True, False, True]):
            agent_create = schemas.AgentCreate(
                name=f"TestAgent{i}",
                system_prompt_id=uuid.UUID(str(db_prompt.pid)),
                persona="Test",
                functions=[],
                routing_options={"respond": "Test response"},
                short_term_memory=False,
                long_term_memory=False,
                reasoning=False,
                input_type=["text"],
                output_type=["text"],
                response_type="json",
                max_retries=3,
                timeout=None,
                deployed=deployed,
                status="active",
                priority=None,
                failure_strategies=["retry"],
                collaboration_mode="single",
                deployment_code=f"x{i}",
                available_for_deployment=True,
            )
            crud.create_agent(db=test_db_session, agent=agent_create)

        # Test filtering by deployed status
        deployed_agents = crud.get_agents(db=test_db_session, deployed=True)
        assert len(deployed_agents) == 2

        non_deployed_agents = crud.get_agents(db=test_db_session, deployed=False)
        assert len(non_deployed_agents) == 1

    def test_update_agent(self, test_db_session):
        """Test updating an agent."""
        # Create a prompt first
        prompt_data = DEFAULT_PROMPTS[0]
        prompt_create = schemas.PromptCreate(
            prompt_label=prompt_data.prompt_label,
            prompt=prompt_data.prompt,
            unique_label=prompt_data.unique_label,
            app_name=prompt_data.app_name,
            version=prompt_data.version,
            ai_model_provider=prompt_data.ai_model_provider,
            ai_model_name=prompt_data.ai_model_name,
            tags=prompt_data.tags,
            hyper_parameters=prompt_data.hyper_parameters,
            variables=prompt_data.variables,
        )

        db_prompt = crud.create_prompt(db=test_db_session, prompt=prompt_create)

        # Create an agent
        agent_create = schemas.AgentCreate(
            name="TestAgent",
            system_prompt_id=uuid.UUID(str(db_prompt.pid)),
            persona="Test",
            functions=[],
            routing_options={"respond": "Test response"},
            short_term_memory=False,
            long_term_memory=False,
            reasoning=False,
            input_type=["text"],
            output_type=["text"],
            response_type="json",
            max_retries=3,
            timeout=None,
            deployed=False,
            status="active",
            priority=None,
            failure_strategies=["retry"],
            collaboration_mode="single",
            deployment_code="x",
            available_for_deployment=True,
        )

        db_agent = crud.create_agent(db=test_db_session, agent=agent_create)

        # Update the agent
        agent_update = schemas.AgentUpdate(persona="Updated Persona", deployed=True)

        updated_agent = crud.update_agent(
            db=test_db_session, agent_id=db_agent.agent_id, agent_update=agent_update
        )

        assert updated_agent is not None
        assert updated_agent.persona == "Updated Persona"
        assert updated_agent.deployed is True
