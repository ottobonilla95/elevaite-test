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
import uuid
from typing import AsyncGenerator, Generator, Dict, Any
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from fastapi import Request
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["SKIP_EXTERNAL_SERVICES"] = "true"

# Import RBAC SDK constants first
from rbac_sdk import (
    HDR_API_KEY,
    HDR_USER_ID,
    HDR_ORG_ID,
    HDR_ACCOUNT_ID,
    HDR_PROJECT_ID,
)


# Mock RBAC guard before importing app (so routers use the mock)
async def _mock_rbac_guard_allow(request: Request):
    """Mock guard that always allows access for testing."""
    pass


def _mock_guard_factory(action: str):
    """Factory that returns the mock guard."""
    return _mock_rbac_guard_allow


# Patch before importing the app
_rbac_patcher = patch("workflow_engine_poc.util.api_key_or_user_guard", side_effect=_mock_guard_factory)
_rbac_patcher.start()

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
    """Create a database session for testing."""
    session = Session(bind=engine)
    yield session
    session.close()


@pytest.fixture(name="test_client")
def test_client_fixture(engine) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with database session override.

    Uses a single session per test to ensure data persists across requests.
    """
    # Create one session for the entire test
    test_session = Session(bind=engine)

    def get_session_override():
        return test_session

    app.dependency_overrides[get_db_session] = get_session_override

    with TestClient(app) as client:
        yield client

    test_session.close()
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
# Authentication and Authorization Fixtures
# ============================================================================


@pytest.fixture(name="test_user_id")
def test_user_id_fixture():
    """Provide a test user ID."""
    return str(uuid.uuid4())


@pytest.fixture(name="test_org_id")
def test_org_id_fixture():
    """Provide a test organization ID."""
    return str(uuid.uuid4())


@pytest.fixture(name="test_account_id")
def test_account_id_fixture():
    """Provide a test account ID."""
    return str(uuid.uuid4())


@pytest.fixture(name="test_project_id")
def test_project_id_fixture():
    """Provide a test project ID."""
    return str(uuid.uuid4())


@pytest.fixture(name="test_api_key")
def test_api_key_fixture():
    """Provide a test API key."""
    return "test-api-key-12345678"


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(
    test_user_id: str,
    test_org_id: str,
    test_account_id: str,
    test_project_id: str,
) -> Dict[str, str]:
    """Provide valid auth headers for user-based authentication."""
    return {
        HDR_USER_ID: test_user_id,
        HDR_ORG_ID: test_org_id,
        HDR_ACCOUNT_ID: test_account_id,
        HDR_PROJECT_ID: test_project_id,
    }


@pytest.fixture(name="api_key_headers")
def api_key_headers_fixture(
    test_api_key: str,
    test_org_id: str,
    test_account_id: str,
    test_project_id: str,
) -> Dict[str, str]:
    """Provide valid auth headers for API key-based authentication."""
    return {
        HDR_API_KEY: test_api_key,
        HDR_ORG_ID: test_org_id,
        HDR_ACCOUNT_ID: test_account_id,
        HDR_PROJECT_ID: test_project_id,
    }


@pytest.fixture(name="mock_rbac_allow")
def mock_rbac_allow_fixture():
    """Mock RBAC to allow all requests (for testing business logic without auth)."""

    async def mock_guard(request: Request):
        """Mock guard that always allows access."""
        pass

    # Mock the guard factory to return our mock guard
    def mock_guard_factory(action: str):
        return mock_guard

    # Patch the guard factory function
    with patch("workflow_engine_poc.util.api_key_or_user_guard", side_effect=mock_guard_factory):
        yield


@pytest.fixture(name="mock_rbac_deny")
def mock_rbac_deny_fixture():
    """Mock RBAC to deny all requests (for testing auth failures)."""
    from fastapi import HTTPException

    async def mock_guard(request: Request):
        """Mock guard that always denies access."""
        raise HTTPException(status_code=403, detail="Access denied")

    # Mock the guard factory to return our mock guard
    def mock_guard_factory(action: str):
        return mock_guard

    # Patch the guard factory function
    with patch("workflow_engine_poc.util.api_key_or_user_guard", side_effect=mock_guard_factory):
        yield


@pytest.fixture(name="authenticated_client")
def authenticated_client_fixture(
    test_client: TestClient,
    auth_headers: Dict[str, str],
    mock_rbac_allow,
) -> TestClient:
    """Provide a test client with authentication headers pre-configured."""
    # Add default headers to the client
    test_client.headers.update(auth_headers)
    return test_client


@pytest.fixture(name="async_client")
async def async_client_fixture(engine, auth_headers: Dict[str, str], mock_rbac_allow):
    """Create an async test client for tests that need true async execution.

    Uses httpx.AsyncClient with ASGITransport for proper async background task execution.
    This is needed for tests that require background tasks to run while the test is executing,
    such as approval flow tests that poll for approval records created by background workflows.

    Uses LifespanManager to ensure lifespan events are triggered, so app.state
    will be initialized with workflow_engine, step_registry, etc.
    """
    from httpx import ASGITransport, AsyncClient
    from asgi_lifespan import LifespanManager

    # Create one session for the entire test
    test_session = Session(bind=engine)

    def get_session_override():
        return test_session

    app.dependency_overrides[get_db_session] = get_session_override

    # Use LifespanManager to trigger lifespan events
    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://test",
            headers=auth_headers,
        ) as client:
            yield client

    test_session.close()
    app.dependency_overrides.clear()


@pytest.fixture(name="api_key_client")
def api_key_client_fixture(
    test_client: TestClient,
    api_key_headers: Dict[str, str],
    mock_rbac_allow,
) -> TestClient:
    """Provide a test client with API key authentication headers pre-configured."""
    # Add default headers to the client
    test_client.headers.update(api_key_headers)
    return test_client


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
