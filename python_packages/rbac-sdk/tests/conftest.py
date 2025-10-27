"""Pytest configuration and fixtures for RBAC SDK tests."""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import Request
from typing import Dict, Any


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object."""
    request = Mock(spec=Request)
    request.headers = {}
    return request


@pytest.fixture
def mock_request_with_user():
    """Create a mock request with user ID header."""
    request = Mock(spec=Request)
    request.headers = {"X-elevAIte-UserId": "123"}
    return request


@pytest.fixture
def mock_request_with_api_key():
    """Create a mock request with API key header."""
    request = Mock(spec=Request)
    request.headers = {"X-elevAIte-apikey": "test-api-key-123"}
    return request


@pytest.fixture
def mock_request_with_project_headers():
    """Create a mock request with all project-related headers."""
    request = Mock(spec=Request)
    request.headers = {
        "X-elevAIte-UserId": "123",
        "X-elevAIte-OrganizationId": "org-456",
        "X-elevAIte-AccountId": "acc-789",
        "X-elevAIte-ProjectId": "proj-101",
    }
    return request


@pytest.fixture
def sample_resource() -> Dict[str, Any]:
    """Sample resource dictionary for testing."""
    return {
        "type": "project",
        "id": "proj-101",
        "organization_id": "org-456",
        "account_id": "acc-789",
    }


@pytest.fixture
def sample_user_id() -> int:
    """Sample user ID for testing."""
    return 123


@pytest.fixture
def sample_action() -> str:
    """Sample action for testing."""
    return "view_project"

