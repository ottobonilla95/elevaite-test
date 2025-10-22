# Testing Guide for Workflow Engine PoC

This document describes the testing strategy, setup, and best practices for the Workflow Engine PoC.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [CI/CD Integration](#cicd-integration)
- [Coverage Requirements](#coverage-requirements)
- [Troubleshooting](#troubleshooting)

## Overview

The Workflow Engine PoC uses **pytest** for testing with the following test categories:

- **Unit Tests**: Fast, isolated tests with no external dependencies
- **Integration Tests**: Tests that interact with database, Redis, or other services
- **E2E Tests**: End-to-end tests that require a running server
- **Smoke Tests**: Quick validation tests for critical paths

### Current Test Coverage

- **44 tests** total
- **Unit tests**: Error handling, conditional execution, monitoring
- **Integration tests**: API endpoints, workflow execution
- **E2E tests**: Streaming, approvals, multi-agent workflows

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── e2e_fixtures.py          # E2E-specific fixtures
├── test_api.py              # API endpoint tests
├── test_conditional_execution.py  # Conditional logic tests
├── test_error_handling.py   # Error handling and retry tests
├── test_monitoring.py       # Monitoring and tracing tests
├── test_ingest_e2e.py       # File ingestion E2E tests
├── test_rag_e2e.py          # RAG workflow E2E tests
└── e2e/                     # End-to-end tests
    ├── test_approvals_e2e.py
    ├── test_dbos_api.py
    ├── test_interactive_e2e.py
    ├── test_megaflow.py
    ├── test_smoke_live_api.py
    └── test_streaming.py
```

## Running Tests

### Prerequisites

1. **Install dependencies**:
   ```bash
   cd python_apps/workflow-engine-poc
   uv pip install -e ".[dev]"
   ```

2. **Set up environment** (optional for unit tests):
   ```bash
   cp .env.example .env.test
   # Edit .env.test with test configuration
   ```

### Run All Tests (Except E2E)

```bash
pytest tests/ -m "not e2e" --ignore=tests/e2e/
```

### Run Unit Tests Only

```bash
pytest tests/ -m "unit"
```

### Run Integration Tests

```bash
pytest tests/ -m "integration"
```

### Run Specific Test File

```bash
pytest tests/test_error_handling.py -v
```

### Run Specific Test Function

```bash
pytest tests/test_error_handling.py::test_retry_mechanisms -v
```

### Run with Coverage

```bash
pytest tests/ \
  -m "not e2e" \
  --ignore=tests/e2e/ \
  --cov=workflow_engine_poc \
  --cov-report=term-missing \
  --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run E2E Tests

E2E tests require a running server:

```bash
# Terminal 1: Start the server
python -m uvicorn workflow_engine_poc.main:app --host 127.0.0.1 --port 8006

# Terminal 2: Run E2E tests
pytest tests/e2e/ -v
```

Or use the smoke test script:
```bash
BASE_URL=http://127.0.0.1:8006 pytest tests/e2e/test_smoke_live_api.py -v
```

## Writing Tests

### Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_something_fast():
    """Unit test - fast, no external dependencies."""
    assert 1 + 1 == 2

@pytest.mark.integration
def test_database_interaction(session):
    """Integration test - uses database."""
    # Test code here
    pass

@pytest.mark.e2e
def test_full_workflow():
    """E2E test - requires running server."""
    # Test code here
    pass

@pytest.mark.slow
def test_long_running_operation():
    """Slow test - may take >5 seconds."""
    # Test code here
    pass
```

### Using Fixtures

Common fixtures available in `conftest.py`:

```python
def test_api_endpoint(test_client):
    """Use test_client fixture for API testing."""
    response = test_client.get("/health")
    assert response.status_code == 200

def test_database_operation(session):
    """Use session fixture for database testing."""
    # session is automatically rolled back after test
    pass

def test_with_mock_openai(mock_openai_client):
    """Use mock_openai_client to prevent real API calls."""
    # OpenAI calls are automatically mocked
    pass

def test_workflow_creation(sample_workflow_data):
    """Use sample data fixtures."""
    workflow = create_workflow(sample_workflow_data)
    assert workflow.name == "Test Workflow"
```

### Best Practices

1. **Isolate tests**: Each test should be independent
2. **Use fixtures**: Leverage shared fixtures for common setup
3. **Mock external services**: Don't make real API calls in tests
4. **Test edge cases**: Test error conditions, not just happy paths
5. **Keep tests fast**: Unit tests should run in milliseconds
6. **Use descriptive names**: Test names should describe what they test
7. **Add docstrings**: Explain what the test validates

### Example Test

```python
import pytest
from fastapi.testclient import TestClient

@pytest.mark.integration
def test_create_workflow_success(test_client: TestClient, sample_workflow_data):
    """
    Test creating a workflow via API.
    
    Validates:
    - 200 status code
    - Workflow is created with correct data
    - Response includes workflow_id
    """
    response = test_client.post("/workflows/", json=sample_workflow_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == sample_workflow_data["name"]
    assert "workflow_id" in data
    assert len(data["steps"]) == len(sample_workflow_data["steps"])

@pytest.mark.integration
def test_create_workflow_invalid_data(test_client: TestClient):
    """Test creating a workflow with invalid data returns 422."""
    invalid_data = {"name": ""}  # Missing required fields
    
    response = test_client.post("/workflows/", json=invalid_data)
    
    assert response.status_code == 422
```

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- **Pull Requests** to `main` or `testing` branches
- **Pushes** to `main` or `testing` branches
- Changes to `python_apps/workflow-engine-poc/**` or `packages/workflow-core-sdk/**`

See `.github/workflows/test-workflow-engine-poc.yml` for configuration.

### What Runs in CI

1. **Unit & Integration Tests**: All non-E2E tests with coverage reporting
2. **Linting**: Ruff for code quality
3. **Type Checking**: MyPy for type safety
4. **E2E Tests** (optional): Only on push or with `run-e2e` label

### Coverage Requirements

- **Minimum coverage**: 70% (green)
- **Warning threshold**: 50% (orange)
- Coverage reports are posted as PR comments

## Coverage Requirements

### Current Coverage Gaps

Based on the test evaluation, the following areas need more tests:

#### Critical Gaps (Must Fix)

1. **RBAC/Security**
   - [ ] Authentication tests (JWT validation, API key validation)
   - [ ] Authorization tests (resource ownership, permissions)
   - [ ] Tenant isolation tests

2. **Router/API Tests**
   - [ ] Agents router (`routers/agents.py`)
   - [ ] Tools router (`routers/tools.py`)
   - [ ] Prompts router (`routers/prompts.py`)
   - [ ] Messages router (`routers/messages.py`)
   - [ ] Approvals router (`routers/approvals.py`)

3. **Error Handling**
   - [ ] Input validation tests (malformed JSON, invalid UUIDs)
   - [ ] Database failure tests
   - [ ] External service failure tests
   - [ ] Timeout tests

#### High Priority

4. **Services**
   - [ ] WorkflowsService tests
   - [ ] ExecutionsService tests
   - [ ] AgentsService tests
   - [ ] ToolsService tests

5. **Business Logic**
   - [ ] Scheduler tests
   - [ ] Streaming tests (comprehensive)
   - [ ] DBOS integration tests

#### Medium Priority

6. **Data Integrity**
   - [ ] Transaction rollback tests
   - [ ] Foreign key constraint tests
   - [ ] Cascade delete tests

7. **Performance**
   - [ ] Load tests
   - [ ] Concurrent execution tests
   - [ ] Memory leak tests

## Troubleshooting

### Tests Fail with Database Errors

**Problem**: `sqlalchemy.exc.OperationalError: no such table`

**Solution**: Ensure database is initialized:
```python
# In conftest.py or test setup
SQLModel.metadata.create_all(engine)
```

### Tests Fail with Import Errors

**Problem**: `ModuleNotFoundError: No module named 'workflow_engine_poc'`

**Solution**: Install package in editable mode:
```bash
cd python_apps/workflow-engine-poc
uv pip install -e .
```

### E2E Tests Fail with Connection Refused

**Problem**: `httpx.ConnectError: [Errno 111] Connection refused`

**Solution**: Start the server before running E2E tests:
```bash
python -m uvicorn workflow_engine_poc.main:app --host 127.0.0.1 --port 8006
```

### Tests Are Slow

**Problem**: Tests take too long to run

**Solutions**:
1. Run only unit tests: `pytest -m unit`
2. Run in parallel: `pytest -n auto` (requires pytest-xdist)
3. Skip slow tests: `pytest -m "not slow"`

### Mock Not Working

**Problem**: Tests are making real API calls

**Solution**: Ensure mocks are applied before imports:
```python
@pytest.fixture(autouse=True)
def mock_openai():
    with patch("openai.AsyncOpenAI") as mock:
        yield mock
```

## Contributing

When adding new features:

1. **Write tests first** (TDD approach)
2. **Aim for >80% coverage** for new code
3. **Add integration tests** for API endpoints
4. **Add unit tests** for business logic
5. **Update this guide** if adding new test patterns

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLModel Testing](https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/)
- [Conventional Commits](https://www.conventionalcommits.org/)

