"""Pytest configuration and fixtures for code execution service tests."""

import pytest
from fastapi.testclient import TestClient

from code_execution_service.main import app
from code_execution_service.services.executor import CodeExecutor
from code_execution_service.services.sandbox import SandboxExecutor
from code_execution_service.services.validator import CodeValidator


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def validator():
    """Create a CodeValidator instance."""
    return CodeValidator()


@pytest.fixture
def sandbox():
    """Create a SandboxExecutor instance."""
    return SandboxExecutor()


@pytest.fixture
def executor(validator, sandbox):
    """Create a CodeExecutor instance with injected dependencies."""
    return CodeExecutor(validator=validator, sandbox=sandbox)

