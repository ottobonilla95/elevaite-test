"""
Unit tests for ResponseAdapter to verify workflow_agents and workflow_connections
are properly populated with agent data from the database.
"""

import uuid
from datetime import datetime
from typing import Optional
from sqlmodel import Session, create_engine, SQLModel
from sqlmodel.pool import StaticPool

import pytest

from adapters.response_adapter import ResponseAdapter
from workflow_core_sdk.db.models import Agent as SDKAgent


@pytest.fixture
def test_db():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def sample_agents(test_db: Session):
    """Create sample agents in the test database"""
    agent1_id = uuid.uuid4()
    agent2_id = uuid.uuid4()
    prompt_id = uuid.uuid4()

    agent1 = SDKAgent(
        id=agent1_id,
        name="Test Agent 1",
        description="First test agent",
        system_prompt_id=prompt_id,
        provider_type="openai",
        status="active",
    )
    agent2 = SDKAgent(
        id=agent2_id,
        name="Test Agent 2",
        description="Second test agent",
        system_prompt_id=prompt_id,
        provider_type="openai",
        status="active",
    )

    test_db.add(agent1)
    test_db.add(agent2)
    test_db.commit()

    return {
        "agent1_id": str(agent1_id),
        "agent2_id": str(agent2_id),
        "agent1": agent1,
        "agent2": agent2,
    }


def test_get_agent_response_with_db(test_db: Session, sample_agents):
    """Test that _get_agent_response fetches real agent data from database"""
    agent_id = sample_agents["agent1_id"]

    response = ResponseAdapter._get_agent_response(agent_id, test_db)

    assert response is not None
    assert response["name"] == "Test Agent 1"
    assert response["description"] == "First test agent"
    assert response["status"] == "active"


def test_get_agent_response_without_db(sample_agents):
    """Test that _get_agent_response returns None when db is None"""
    agent_id = sample_agents["agent1_id"]

    response = ResponseAdapter._get_agent_response(agent_id, None)

    # Should return None when db is not provided
    assert response is None


def test_get_agent_response_nonexistent_agent(test_db: Session):
    """Test that _get_agent_response returns None for nonexistent agent"""
    nonexistent_id = str(uuid.uuid4())

    response = ResponseAdapter._get_agent_response(nonexistent_id, test_db)

    # Should return None when agent doesn't exist in database
    assert response is None


def test_adapt_workflow_response_with_agents(test_db: Session, sample_agents):
    """Test that adapt_workflow_response populates workflow_agents with real data"""
    workflow_id = uuid.uuid4()
    agent1_id = sample_agents["agent1_id"]
    agent2_id = sample_agents["agent2_id"]

    sdk_workflow = {
        "id": str(workflow_id),
        "name": "Test Workflow",
        "description": "A test workflow",
        "version": "1.0.0",
        "status": "active",
        "editable": True,
        "created_at": datetime.now().isoformat(),
        "configuration": {
            "steps": [
                {
                    "step_id": agent1_id,  # SDK uses step_id
                    "step_type": "agent",
                    "name": "Agent 1",
                    "config": {"agent_id": agent1_id},
                    "position": {"x": 100, "y": 100},
                },
                {
                    "step_id": agent2_id,  # SDK uses step_id
                    "step_type": "agent",
                    "name": "Agent 2",
                    "config": {"agent_id": agent2_id},
                    "position": {"x": 300, "y": 100},
                },
            ],
            "connections": [
                {
                    "source_step_id": agent1_id,
                    "target_step_id": agent2_id,
                    "connection_type": "default",
                    "priority": 0,
                }
            ],
        },
    }

    response = ResponseAdapter.adapt_workflow_response(sdk_workflow, test_db)

    # Verify workflow_agents are populated
    assert "workflow_agents" in response
    assert len(response["workflow_agents"]) == 2

    # Verify first agent has real data
    agent1_response = response["workflow_agents"][0]
    assert agent1_response["agent_id"] == agent1_id
    assert agent1_response["agent"]["name"] == "Test Agent 1"
    assert agent1_response["agent"]["description"] == "First test agent"
    assert agent1_response["position_x"] == 100
    assert agent1_response["position_y"] == 100

    # Verify second agent has real data
    agent2_response = response["workflow_agents"][1]
    assert agent2_response["agent_id"] == agent2_id
    assert agent2_response["agent"]["name"] == "Test Agent 2"
    assert agent2_response["agent"]["description"] == "Second test agent"


def test_adapt_workflow_response_with_connections(test_db: Session, sample_agents):
    """Test that adapt_workflow_response populates workflow_connections with real agent data"""
    workflow_id = uuid.uuid4()
    agent1_id = sample_agents["agent1_id"]
    agent2_id = sample_agents["agent2_id"]

    sdk_workflow = {
        "id": str(workflow_id),
        "name": "Test Workflow",
        "version": "1.0.0",
        "status": "active",
        "editable": True,
        "created_at": datetime.now().isoformat(),
        "configuration": {
            "steps": [
                {
                    "step_id": agent1_id,  # SDK uses step_id
                    "step_type": "agent",
                    "config": {},
                },
                {
                    "step_id": agent2_id,  # SDK uses step_id
                    "step_type": "agent",
                    "config": {},
                },
            ],
            "connections": [
                {
                    "source_step_id": agent1_id,
                    "target_step_id": agent2_id,
                    "connection_type": "default",
                    "priority": 1,
                }
            ],
        },
    }

    response = ResponseAdapter.adapt_workflow_response(sdk_workflow, test_db)

    # Verify workflow_connections are populated
    assert "workflow_connections" in response
    assert len(response["workflow_connections"]) == 1

    # Verify connection has real agent data
    connection = response["workflow_connections"][0]
    assert connection["source_agent_id"] == agent1_id
    assert connection["target_agent_id"] == agent2_id
    assert connection["source_agent"]["name"] == "Test Agent 1"
    assert connection["target_agent"]["name"] == "Test Agent 2"
    assert connection["priority"] == 1
