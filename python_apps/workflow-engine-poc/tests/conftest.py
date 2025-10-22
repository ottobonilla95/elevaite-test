"""
Pytest configuration and fixtures for workflow-engine-poc tests.

Provides shared fixtures for:
- Database sessions with automatic cleanup
- Test client for API testing
- Mock external services (OpenAI, Anthropic, etc.)
- Test data factories
"""

import os
import asyncio
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["SKIP_EXTERNAL_SERVICES"] = "true"

from workflow_engine_poc.main import app
from workflow_engine_poc.db.database import get_db_session


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(name="engine")
def engine_fixture():
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(name="session")
def session_fixture(engine) -> Generator[Session, None, None]:
    """Create a database session for testing with automatic rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="test_client")
def test_client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with database session override."""
    
    def get_session_override():
        return session
    
    app.dependency_overrides[get_db_session] = get_session_override
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


# ============================================================================
# Mock External Services
# ============================================================================

@pytest.fixture(name="mock_openai_client")
def mock_openai_client_fixture():
    """Mock OpenAI client to prevent real API calls."""
    mock_response = Mock()
    mock_response.choices = [
        Mock(
            message=Mock(
                content="This is a mocked response from OpenAI.",
                role="assistant",
                tool_calls=None,
            ),
            finish_reason="stop",
        )
    ]
    mock_response.usage = Mock(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )
    
    mock_client = Mock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    with patch("openai.AsyncOpenAI", return_value=mock_client):
        yield mock_client


@pytest.fixture(name="mock_anthropic_client")
def mock_anthropic_client_fixture():
    """Mock Anthropic client to prevent real API calls."""
    mock_response = Mock()
    mock_response.content = [
        Mock(
            type="text",
            text="This is a mocked response from Anthropic.",
        )
    ]
    mock_response.usage = Mock(
        input_tokens=10,
        output_tokens=20,
    )
    
    mock_client = Mock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    
    with patch("anthropic.AsyncAnthropic", return_value=mock_client):
        yield mock_client


@pytest.fixture(name="mock_redis")
def mock_redis_fixture():
    """Mock Redis client for tests that don't need real Redis."""
    mock_redis = AsyncMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=0)
    
    with patch("redis.asyncio.Redis", return_value=mock_redis):
        yield mock_redis


# ============================================================================
# Test Data Factories
# ============================================================================

@pytest.fixture(name="sample_workflow_data")
def sample_workflow_data_fixture():
    """Provide sample workflow data for testing."""
    return {
        "workflow_id": "test-workflow-001",
        "name": "Test Workflow",
        "description": "A test workflow for unit testing",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "step1",
                "step_name": "Input Step",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "input_type": "static",
                    "data": {"message": "Hello, World!"},
                },
            },
            {
                "step_id": "step2",
                "step_name": "Processing Step",
                "step_type": "data_processing",
                "step_order": 2,
                "dependencies": ["step1"],
                "config": {
                    "processing_type": "passthrough",
                },
            },
        ],
    }


@pytest.fixture(name="sample_agent_data")
def sample_agent_data_fixture():
    """Provide sample agent data for testing."""
    return {
        "name": "Test Agent",
        "description": "A test agent for unit testing",
        "provider_type": "openai_textgen",
        "provider_config": {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 1000,
        },
        "system_prompt_id": None,
    }


@pytest.fixture(name="sample_prompt_data")
def sample_prompt_data_fixture():
    """Provide sample prompt data for testing."""
    return {
        "prompt_label": "Test System Prompt",
        "prompt": "You are a helpful test assistant.",
        "unique_label": "test-prompt-001",
        "app_name": "test_app",
        "version": "1.0.0",
        "ai_model_provider": "openai",
        "ai_model_name": "gpt-4o-mini",
        "tags": ["test", "assistant"],
        "hyper_parameters": {
            "temperature": "0.7",
            "max_tokens": "1000",
        },
    }


@pytest.fixture(name="sample_tool_data")
def sample_tool_data_fixture():
    """Provide sample tool data for testing."""
    return {
        "name": "test_calculator",
        "description": "A test calculator tool",
        "category_id": None,
        "schema": {
            "type": "function",
            "function": {
                "name": "test_calculator",
                "description": "Perform basic arithmetic operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                        },
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["operation", "a", "b"],
                },
            },
        },
        "source_type": "local",
    }


# ============================================================================
# Environment and Configuration
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables for the entire test session."""
    # Store original environment
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        "TESTING": "true",
        "ENVIRONMENT": "test",
        "DATABASE_URL": "sqlite:///:memory:",
        "OTEL_SDK_DISABLED": "true",
        "SKIP_EXTERNAL_SERVICES": "true",
        "OPENAI_API_KEY": "sk-test-mock-key",
        "ANTHROPIC_API_KEY": "sk-ant-test-mock-key",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
    }
    
    os.environ.update(test_env)
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def reset_app_state():
    """Reset app state between tests."""
    # Clear any cached state in the app
    if hasattr(app.state, "workflow_engine"):
        delattr(app.state, "workflow_engine")
    if hasattr(app.state, "step_registry"):
        delattr(app.state, "step_registry")
    if hasattr(app.state, "database"):
        delattr(app.state, "database")
    
    yield
    
    # Clean up after test
    app.dependency_overrides.clear()


# ============================================================================
# Async Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture(name="clean_database")
def clean_database_fixture(session: Session):
    """Ensure database is clean before and after test."""
    # Clean before test
    SQLModel.metadata.drop_all(session.get_bind())
    SQLModel.metadata.create_all(session.get_bind())
    
    yield session
    
    # Clean after test
    SQLModel.metadata.drop_all(session.get_bind())

