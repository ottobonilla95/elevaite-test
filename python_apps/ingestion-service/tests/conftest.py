"""
Pytest configuration and fixtures for ingestion-service tests.

Provides shared fixtures for:
- Database sessions with automatic cleanup
- Test client for API testing with FastAPI dependency overrides
- Mock DBOS for unit tests
"""

import os
import pytest
from typing import Generator
from unittest.mock import MagicMock, AsyncMock, patch

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

# Set test environment variables before importing app
os.environ["TESTING"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture(name="engine")
def engine_fixture(tmp_path):
    """Create a file-based SQLite engine for testing.

    Uses a temporary file-based database for test isolation.
    """
    db_path = tmp_path / "test_ingestion.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
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


# ============================================================================
# Mock DBOS Fixtures
# ============================================================================


@pytest.fixture(name="mock_dbos")
def mock_dbos_fixture():
    """Mock DBOS to prevent real workflow starts.

    The DBOS.workflow() decorator wraps the function and checks if DBOS is launched
    when the function is called. We need to mock the internal executor check.
    """
    mock_handle = MagicMock()
    mock_handle.workflow_id = "test-dbos-wf-123"

    mock_dbos = MagicMock()
    mock_dbos.start_workflow_async = AsyncMock(return_value=mock_handle)
    mock_dbos.send_async = AsyncMock()
    mock_dbos.launch = MagicMock()

    # Mock the DBOS executor to prevent "Executor accessed before DBOS was launched" error
    # The DBOS._executor is checked when decorated functions are called
    mock_executor = MagicMock()
    mock_executor.workflow_id = "test-dbos-wf-123"

    # Patch DBOS in both main and workflows modules
    # Also patch the internal _executor to prevent the launch check
    with (
        patch("ingestion_service.main.DBOS", mock_dbos),
        patch("ingestion_service.workflows.DBOS", mock_dbos),
        patch("dbos.DBOS._executor", mock_executor, create=True),
        patch("dbos._dbos.DBOS._executor", mock_executor, create=True),
    ):
        yield mock_dbos


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================


@pytest.fixture(name="client")
def client_fixture(engine, mock_dbos) -> Generator[TestClient, None, None]:
    """Create a FastAPI test client with database session override.

    Uses FastAPI's dependency_overrides to inject the test database session,
    and mocks DBOS to prevent real workflow execution.
    """
    from ingestion_service.main import app
    from ingestion_service.database import get_session

    # Create one session for the entire test
    test_session = Session(bind=engine)

    def get_session_override():
        yield test_session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client

    test_session.close()
    app.dependency_overrides.clear()


# ============================================================================
# Mock Session Fixtures (for workflow unit tests)
# ============================================================================


@pytest.fixture(name="mock_session")
def mock_session_fixture():
    """Create a mock database session for unit tests."""
    session = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.add = MagicMock()
    return session


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture(name="sample_job_request")
def sample_job_request_fixture():
    """Provide sample job creation request data."""
    return {
        "config": {
            "source": "s3",
            "bucket": "test-bucket",
            "files": ["doc1.pdf", "doc2.pdf"],
        },
        "metadata": {
            "tenant_id": "org-123",
            "execution_id": "exec-456",
            "step_id": "step-789",
            "callback_topic": "wf:exec-456:step-789:ingestion_done",
        },
    }


@pytest.fixture(name="sample_job_config")
def sample_job_config_fixture():
    """Provide sample ingestion configuration."""
    return {
        "source": "s3",
        "bucket": "test-bucket",
        "files": ["test.pdf"],
    }
