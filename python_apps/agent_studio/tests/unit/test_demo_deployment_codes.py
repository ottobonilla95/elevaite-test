
from services.demo_service import DemoInitializationService
from db.fixtures import DEFAULT_AGENTS, DEFAULT_PROMPTS, AGENT_CODES
from db import models, crud


class TestDemoDeploymentCodes:
    """Test deployment code functionality in demo service."""

    def test_agent_codes_mapping(self):
        """Test that AGENT_CODES contains all expected agents."""
        expected_agents = {
            "WebAgent", "DataAgent", "APIAgent", 
            "CommandAgent", "HelloWorldAgent", "ToshibaAgent"
        }
        
        assert set(AGENT_CODES.keys()) == expected_agents
        assert len(AGENT_CODES) == 6
        
        # Verify all codes are single characters
        for agent_name, code in AGENT_CODES.items():
            assert len(code) == 1
            assert isinstance(code, str)

    def test_default_agents_have_corresponding_codes(self):
        """Test that all DEFAULT_AGENTS have corresponding codes in AGENT_CODES."""
        for agent in DEFAULT_AGENTS:
            assert agent.name in AGENT_CODES, f"Agent {agent.name} missing from AGENT_CODES"

    def test_deployment_code_assignment_logic(self, test_db_session):
        """Test that deployment codes are properly assigned during agent creation."""
        # Initialize prompts first
        service = DemoInitializationService(test_db_session)
        prompts_success, _, _ = service.initialize_prompts()
        assert prompts_success
        
        # Initialize agents
        agents_success, message, details = service.initialize_agents()
        assert agents_success
        
        # Verify each agent has the correct deployment code
        for agent_data in DEFAULT_AGENTS:
            db_agent = test_db_session.query(models.Agent).filter(
                models.Agent.name == agent_data.name
            ).first()
            
            assert db_agent is not None, f"Agent {agent_data.name} not found in database"
            
            expected_code = AGENT_CODES.get(agent_data.name)
            assert db_agent.deployment_code == expected_code, \
                f"Agent {agent_data.name} has code {db_agent.deployment_code}, expected {expected_code}"
            assert db_agent.available_for_deployment is True

    def test_get_available_agents_returns_agents_with_codes(self, test_db_session):
        """Test that get_available_agents returns agents with deployment codes."""
        # Initialize demo data
        service = DemoInitializationService(test_db_session)
        service.initialize_all()
        
        # Get available agents
        available_agents = crud.get_available_agents(test_db_session)
        
        # Should return all agents since they all have deployment codes
        assert len(available_agents) == len(DEFAULT_AGENTS)
        
        # Each agent should have a deployment code
        for agent in available_agents:
            assert agent.deployment_code is not None
            assert agent.deployment_code in AGENT_CODES.values()
            assert agent.available_for_deployment is True

    def test_deployment_code_uniqueness(self):
        """Test that all deployment codes are unique."""
        codes = list(AGENT_CODES.values())
        assert len(codes) == len(set(codes)), "Deployment codes are not unique"

    def test_agent_creation_with_deployment_code(self, test_db_session):
        """Test creating a single agent with deployment code."""
        # Create a prompt first
        from db.schemas import PromptCreate
        prompt_data = DEFAULT_PROMPTS[0]
        prompt_create = PromptCreate(
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
        
        # Create an agent with deployment code
        from db.schemas import AgentCreate
        import uuid
        
        agent_create = AgentCreate(
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
        
        assert db_agent.deployment_code == "x"
        assert db_agent.available_for_deployment is True
        
        # Test retrieval by deployment code
        found_agent = crud.get_agent_by_deployment_code(test_db_session, "x")
        assert found_agent is not None
        assert found_agent.name == "TestAgent"

    def test_idempotent_agent_initialization(self, test_db_session):
        """Test that running agent initialization twice doesn't create duplicates."""
        service = DemoInitializationService(test_db_session)
        
        # Initialize prompts
        service.initialize_prompts()
        
        # Initialize agents first time
        success1, message1, details1 = service.initialize_agents()
        assert success1
        assert details1["added_count"] == len(DEFAULT_AGENTS)
        assert details1["skipped_count"] == 0
        
        # Initialize agents second time
        success2, message2, details2 = service.initialize_agents()
        assert success2
        assert details2["added_count"] == 0
        assert details2["skipped_count"] == len(DEFAULT_AGENTS)
        
        # Verify total count is still correct
        total_agents = test_db_session.query(models.Agent).count()
        assert total_agents == len(DEFAULT_AGENTS)
