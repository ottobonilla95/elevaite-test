import pytest
from db.fixtures import DEFAULT_AGENTS, DEFAULT_PROMPTS, AGENT_CODES


class TestSimpleDeploymentCodes:
    """Simple tests for deployment code functionality."""

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

    def test_deployment_code_uniqueness(self):
        """Test that all deployment codes are unique."""
        codes = list(AGENT_CODES.values())
        assert len(codes) == len(set(codes)), "Deployment codes are not unique"

    def test_agent_codes_values(self):
        """Test specific agent code values."""
        expected_codes = {
            "WebAgent": "w",
            "DataAgent": "d", 
            "APIAgent": "a",
            "CommandAgent": "r",
            "HelloWorldAgent": "h",
            "ToshibaAgent": "t"
        }
        
        assert AGENT_CODES == expected_codes
