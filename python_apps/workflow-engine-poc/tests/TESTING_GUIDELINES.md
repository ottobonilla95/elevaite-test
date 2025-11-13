# Testing Guidelines for Workflow Engine PoC

This document provides comprehensive guidelines for writing tests in the workflow-engine-poc project.

## Current Test Status

- **181 passing tests** (100% pass rate)
- **18 skipped tests** (E2E tests requiring live server)
- **49% code coverage** (2,592/5,272 lines)
- **Test breakdown**: 13 unit, 2 integration, 152 API, 14 E2E
- **All tests organized** with pytest markers for selective running

## Table of Contents

1. [Test Organization](#test-organization)
2. [Test Types and Markers](#test-types-and-markers)
3. [Fixtures and Test Data](#fixtures-and-test-data)
4. [Mocking Patterns](#mocking-patterns)
5. [Best Practices](#best-practices)
6. [Running Tests](#running-tests)
7. [Coverage Requirements](#coverage-requirements)

---

## Test Organization

### Directory Structure

```
tests/
├── unit/              # Unit tests (fast, no external dependencies)
├── integration/       # Integration tests (database, services)
├── api/              # API/Router endpoint tests (TestClient-based)
├── e2e/              # End-to-end tests (require running server)
├── archived/         # Archived/deprecated tests
├── conftest.py       # Shared fixtures
└── e2e_fixtures.py   # E2E-specific fixtures
```

### File Naming

- Test files: `test_<module_name>.py`
- Test classes: `class Test<FeatureName>:`
- Test functions: `def test_<specific_behavior>():`

**Examples:**
```python
# tests/api/test_workflows_router.py
class TestWorkflowCRUD:
    def test_create_workflow_success(self):
        ...
    
    def test_create_workflow_invalid_data(self):
        ...
```

---

## Test Types and Markers

### Available Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit          # Unit tests (fast, no external dependencies)
@pytest.mark.integration   # Integration tests (database, redis, etc.)
@pytest.mark.api           # API/Router endpoint tests
@pytest.mark.e2e           # End-to-end tests (require running server)
@pytest.mark.slow          # Slow tests (may take >5 seconds)
@pytest.mark.requires_openai      # Tests requiring OpenAI API key
@pytest.mark.requires_anthropic   # Tests requiring Anthropic API key
@pytest.mark.requires_external    # Tests requiring external services
@pytest.mark.smoke         # Smoke tests for quick validation
```

### When to Use Each Marker

#### `@pytest.mark.unit`
- Tests for pure functions, classes, utilities
- No database, no external services
- Fast execution (<100ms per test)
- Use mocks for all dependencies

**Example:**
```python
@pytest.mark.unit
def test_condition_evaluator():
    """Test condition evaluation logic"""
    result = condition_evaluator.evaluate(
        Condition(field="status", operator=ConditionOperator.EQUALS, value="active")
    )
    assert result is True
```

#### `@pytest.mark.api`
- Tests for FastAPI router endpoints
- Use `TestClient` (no live server)
- Database fixtures allowed
- Mock external services (RBAC, LLM providers)

**Example:**
```python
@pytest.mark.api
def test_create_workflow(test_client, auth_headers):
    """Test workflow creation endpoint"""
    response = test_client.post(
        "/workflows",
        json={"name": "Test Workflow", "description": "Test"},
        headers=auth_headers,
    )
    assert response.status_code == 201
```

#### `@pytest.mark.integration`
- Tests for service layer integration
- Real database operations
- Multiple services working together
- No external API calls

**Example:**
```python
@pytest.mark.integration
async def test_workflow_execution_service(session):
    """Test workflow execution with database persistence"""
    workflow = await WorkflowsService.create_workflow(session, workflow_data)
    execution = await WorkflowsService.create_execution(session, workflow.id)
    assert execution.status == ExecutionStatus.PENDING
```

#### `@pytest.mark.e2e`
- Tests requiring live server
- Real HTTP requests (httpx, requests)
- SSE streaming tests
- Full system integration

**Example:**
```python
@pytest.mark.e2e
async def test_streaming_execution(live_server_url):
    """Test SSE streaming from live server"""
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", f"{live_server_url}/stream") as response:
            async for line in response.aiter_lines():
                assert line.startswith("data:")
```

---

## Fixtures and Test Data

### Core Fixtures (from `conftest.py`)

#### Database Fixtures

```python
@pytest.fixture
def session():
    """Provides a database session for testing"""
    # Use this for tests that need database access
```

#### Test Client Fixtures

```python
@pytest.fixture
def test_client(session):
    """FastAPI TestClient with database session override"""
    # Use this for API endpoint tests
```

#### Authentication Fixtures

```python
@pytest.fixture
def auth_headers():
    """Returns authentication headers for API requests"""
    # Use this for authenticated endpoint tests
```

### Creating Test Data

#### Persisted Entities

Always persist entities to the database with all required fields:

```python
@pytest.fixture
def sample_workflow(session):
    """Sample workflow for testing - persisted to database"""
    workflow = Workflow(
        id=uuid.uuid4(),
        name="Test Workflow",
        description="Test workflow description",
        steps=[],
        organization_id="org-123",
        created_by="user-123",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    return workflow
```

#### Related Entities

When creating entities with foreign keys, create parent entities first:

```python
@pytest.fixture
def sample_agent(session):
    """Sample agent with prompt - persisted to database"""
    # Create prompt first
    prompt = Prompt(
        id=uuid.uuid4(),
        prompt_label="test_prompt",
        prompt="You are a helpful assistant.",
        unique_label="test_prompt_unique",
        app_name="test_app",
        ai_model_provider="openai",
        ai_model_name="gpt-4",
        organization_id="org-123",
        created_by="user-123",
    )
    session.add(prompt)
    session.commit()
    
    # Create agent with prompt reference
    agent = Agent(
        id=uuid.uuid4(),
        name="test_agent",
        system_prompt_id=prompt.id,  # Foreign key
        provider_type="openai_textgen",
        provider_config={"model_name": "gpt-4"},
        organization_id="org-123",
        created_by="user-123",
    )
    session.add(agent)
    session.commit()
    session.refresh(agent)
    return agent
```

---

## Mocking Patterns

### Mock RBAC Guard

RBAC is automatically mocked in `conftest.py`:

```python
@pytest.fixture(autouse=True)
def mock_rbac_guard():
    """Mock RBAC guard to allow all requests"""
    with patch("workflow_engine_poc.routers.rbac_guard.verify_access") as mock:
        mock.return_value = True
        yield mock
```

### Mock External Services

#### LLM Providers

```python
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    with patch("openai.AsyncOpenAI") as mock:
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = AsyncMock(
            choices=[
                AsyncMock(
                    message=AsyncMock(content="Test response"),
                    finish_reason="stop",
                )
            ]
        )
        mock.return_value = mock_client
        yield mock_client
```

#### Database Services

For unit tests, mock database services:

```python
@pytest.fixture
def mock_workflows_service():
    """Mock WorkflowsService for unit testing"""
    with patch("workflow_engine_poc.services.workflows_service.WorkflowsService") as mock:
        mock.get_workflow.return_value = sample_workflow_data
        mock.create_execution.return_value = sample_execution_data
        yield mock
```

### Async Mocking

Use `AsyncMock` for async functions:

```python
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_async_service():
    """Mock async service"""
    with patch("module.async_function") as mock:
        mock.return_value = AsyncMock(return_value="result")
        yield mock
```

---

## Best Practices

### 1. Test Naming

Use descriptive names that explain what is being tested:

```python
# Good
def test_create_workflow_with_valid_data_returns_201():
    ...

def test_create_workflow_with_missing_name_returns_400():
    ...

# Bad
def test_workflow():
    ...

def test_create():
    ...
```

### 2. Arrange-Act-Assert Pattern

Structure tests clearly:

```python
def test_workflow_execution():
    # Arrange
    workflow = create_test_workflow()
    execution_data = {"workflow_id": workflow.id}
    
    # Act
    response = test_client.post("/executions", json=execution_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["status"] == "pending"
```

### 3. One Assertion Per Test (When Possible)

```python
# Good - focused test
def test_workflow_creation_returns_201():
    response = test_client.post("/workflows", json=workflow_data)
    assert response.status_code == 201

def test_workflow_creation_returns_workflow_id():
    response = test_client.post("/workflows", json=workflow_data)
    assert "id" in response.json()

# Acceptable - related assertions
def test_workflow_creation_response():
    response = test_client.post("/workflows", json=workflow_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == workflow_data["name"]
    assert data["description"] == workflow_data["description"]
```

### 4. Use Fixtures for Reusable Test Data

```python
# Good - reusable fixture
@pytest.fixture
def workflow_data():
    return {
        "name": "Test Workflow",
        "description": "Test description",
        "steps": [],
    }

def test_create_workflow(test_client, workflow_data):
    response = test_client.post("/workflows", json=workflow_data)
    assert response.status_code == 201

# Bad - duplicated data
def test_create_workflow(test_client):
    data = {"name": "Test Workflow", "description": "Test description"}
    response = test_client.post("/workflows", json=data)
    assert response.status_code == 201
```

### 5. Clean Up After Tests

Use fixtures with cleanup or context managers:

```python
@pytest.fixture
def temp_file():
    """Create temporary file for testing"""
    file_path = Path("test_file.txt")
    file_path.write_text("test content")
    yield file_path
    file_path.unlink()  # Cleanup
```

### 6. Skip Tests Appropriately

Use skip markers with clear reasons:

```python
@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY for embedding"
)
def test_openai_embedding():
    ...
```

---

## Running Tests

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Types

```bash
# Unit tests only (fast)
pytest -m unit

# API tests only
pytest -m api

# Integration tests
pytest -m integration

# E2E tests (requires live server)
pytest -m e2e

# All tests except E2E
pytest -m "not e2e"
```

### Run Specific Test Files

```bash
# Single file
pytest tests/api/test_workflows_router.py

# Single test
pytest tests/api/test_workflows_router.py::test_create_workflow

# Single test class
pytest tests/api/test_workflows_router.py::TestWorkflowCRUD
```

### Run with Coverage

```bash
# Generate coverage report
pytest tests/ --cov=workflow_engine_poc --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

### Run with Verbose Output

```bash
# Show test names
pytest -v

# Show print statements
pytest -s

# Show full tracebacks
pytest --tb=long
```

---

## Coverage Requirements

### Target Coverage

- **Overall**: 50%+ (currently 49%)
- **Routers**: 80%+ (currently 80-100%)
- **Services**: 60%+
- **Core Logic**: 70%+

### What to Cover

1. **Happy paths** - Normal operation
2. **Error cases** - Invalid input, missing data
3. **Edge cases** - Boundary conditions, empty data
4. **Integration points** - Service interactions

### What NOT to Cover

1. **External libraries** - Don't test FastAPI, SQLAlchemy
2. **Configuration** - Don't test environment variables
3. **Trivial code** - Simple getters/setters
4. **Debug code** - Temporary debugging code

---

## Common Patterns

### Testing API Endpoints

```python
@pytest.mark.api
class TestWorkflowEndpoints:
    def test_create_workflow_success(self, test_client, auth_headers):
        response = test_client.post(
            "/workflows",
            json={"name": "Test", "description": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 201
    
    def test_get_workflow_not_found(self, test_client, auth_headers):
        response = test_client.get(
            "/workflows/00000000-0000-0000-0000-000000000000",
            headers=auth_headers,
        )
        assert response.status_code == 404
```

### Testing Async Functions

```python
@pytest.mark.unit
async def test_async_function():
    result = await async_function()
    assert result == expected_value
```

### Testing Error Handling

```python
@pytest.mark.unit
def test_error_handling():
    with pytest.raises(ValueError, match="Invalid input"):
        function_that_raises("invalid")
```

---

## Troubleshooting

### Common Issues

#### 1. Database Integrity Errors

**Problem**: `NOT NULL constraint failed`

**Solution**: Ensure all required fields are set in fixtures

```python
# Bad
prompt = Prompt(prompt="Test")

# Good
prompt = Prompt(
    id=uuid.uuid4(),
    prompt_label="test",
    prompt="Test",
    unique_label="test_unique",
    app_name="test_app",
    ai_model_provider="openai",
    ai_model_name="gpt-4",
    organization_id="org-123",
    created_by="user-123",
)
```

#### 2. Async Test Failures

**Problem**: `RuntimeError: Event loop is closed`

**Solution**: Use `async def` for async tests

```python
# Bad
def test_async_function():
    result = await async_function()  # Error!

# Good
async def test_async_function():
    result = await async_function()
```

#### 3. Mock Not Working

**Problem**: Mock not being called

**Solution**: Patch the correct import path

```python
# Bad - patching where it's defined
@patch("external_module.function")

# Good - patching where it's used
@patch("workflow_engine_poc.routers.workflows.function")
```

---

## Additional Resources

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)

