# Test Environment Configuration

This document explains how the test environment is configured and how to customize it for your needs.

## Overview

The Agent Studio test suite uses FastAPI's `TestClient` for integration testing. Tests run against the actual application code but with:
- Isolated test database
- Mock/test API keys
- Disabled external services
- Controlled environment variables

## Environment Variables

All test environment variables are configured in `tests/conftest.py` via the `setup_test_environment` fixture.

### Database Configuration

```python
SQLALCHEMY_DATABASE_URL=postgresql://elevaite:elevaite@localhost:5433/agent_studio
AGENT_STUDIO_DATABASE_URL=postgresql://elevaite:elevaite@localhost:5433/agent_studio
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

**Default**: Uses the same database as development  
**Override**: Set `TEST_DATABASE_URL` environment variable to use a separate test database

```bash
export TEST_DATABASE_URL=postgresql://elevaite:elevaite@localhost:5433/agent_studio_test
```

### Redis Configuration

```python
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=1  # Uses DB 1 to avoid conflicts with dev (DB 0)
```

**Override**: Set `TEST_REDIS_*` environment variables

```bash
export TEST_REDIS_HOST=localhost
export TEST_REDIS_PORT=6379
export TEST_REDIS_DB=1
```

### API Keys

By default, tests use **mock API keys** and don't make real API calls:

```python
OPENAI_API_KEY=sk-test-mock-key  # Mock key
ANTHROPIC_API_KEY=               # Empty
COHERE_API_KEY=                  # Empty
GEMINI_API_KEY=                  # Empty
```

**To test with real AI services** (will incur costs!):

1. Create `.env.test.local`:
```bash
TEST_OPENAI_API_KEY=sk-your-real-key-here
TEST_ANTHROPIC_API_KEY=your-real-key-here
```

2. The fixture will use these values instead of mocks

### Other Services

```python
# Vector database
QDRANT_HOST=localhost
QDRANT_PORT=6333

# AWS (for Bedrock)
AWS_DEFAULT_REGION=us-west-1

# Disabled services
OTLP_ENDPOINT=              # Disable OpenTelemetry
KUBERNETES_SERVICE_HOST=    # Not in Kubernetes
```

## Test Fixtures

### `setup_test_environment` (session-scoped, autouse)

Automatically sets up all environment variables before any tests run and restores original values after all tests complete.

```python
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Sets up 60+ environment variables
    # Runs once per test session
    # Automatically restores original values
```

### `test_db_session` (function-scoped)

Creates a fresh database session for each test with automatic rollback:

```python
@pytest.fixture(scope="function")
def test_db_session(test_engine):
    # Creates SQLModel Session
    # Wraps in transaction
    # Rolls back after test
```

### `test_client` (function-scoped)

Creates a FastAPI TestClient with database dependency override:

```python
@pytest.fixture(scope="function")
def test_client(test_db_session):
    # Overrides get_db() dependency
    # Returns TestClient instance
    # Clears overrides after test
```

## Running Tests

### All integration tests
```bash
cd python_apps/agent_studio/agent-studio
pytest tests/integration/ -v
```

### Specific test file
```bash
pytest tests/integration/test_prompts_api.py -v
```

### Specific test
```bash
pytest tests/integration/test_prompts_api.py::TestPromptsAPI::test_create_prompt_success -v
```

### With coverage
```bash
pytest tests/integration/ --cov=api --cov=services --cov-report=html
```

### With real API keys (costs money!)
```bash
export TEST_OPENAI_API_KEY=sk-your-real-key
pytest tests/integration/test_agents_api.py -v
```

## Test Isolation

Each test is isolated:

1. **Database**: Each test runs in a transaction that's rolled back
2. **Environment**: Environment variables are set once per session
3. **Dependencies**: FastAPI dependencies are overridden per test
4. **Cleanup**: Tests clean up created resources (agents, workflows, etc.)

## Customizing Test Environment

### Option 1: Environment Variables (Recommended)

Set environment variables before running tests:

```bash
export TEST_DATABASE_URL=postgresql://user:pass@host:port/testdb
export TEST_OPENAI_API_KEY=sk-real-key
pytest tests/integration/ -v
```

### Option 2: .env.test.local File

Create `.env.test.local` in the agent-studio directory:

```bash
# .env.test.local
TEST_DATABASE_URL=postgresql://user:pass@host:port/testdb
TEST_OPENAI_API_KEY=sk-real-key
TEST_REDIS_DB=2
```

Then load it before running tests:

```bash
set -a; source .env.test.local; set +a
pytest tests/integration/ -v
```

### Option 3: Modify conftest.py

For permanent changes, edit `tests/conftest.py`:

```python
test_env_vars = {
    "OPENAI_API_KEY": "sk-my-default-test-key",
    # ... other vars
}
```

## Troubleshooting

### Tests fail with "connection refused"

**Problem**: Database or Redis not running  
**Solution**: Start services:
```bash
docker-compose up -d postgres redis
```

### Tests fail with "table does not exist"

**Problem**: Database schema not initialized  
**Solution**: Run migrations:
```bash
cd python_apps/agent_studio/agent-studio
alembic upgrade head
```

### Tests make real API calls

**Problem**: Real API key is set in environment  
**Solution**: Unset the variable:
```bash
unset OPENAI_API_KEY
pytest tests/integration/ -v
```

### Tests are slow

**Problem**: Database operations or external calls  
**Solution**: 
- Use smaller test database
- Reduce pool sizes
- Mock external services

## Best Practices

1. **Don't commit real API keys** - Use mock keys in tests
2. **Clean up resources** - Delete created entities in tests
3. **Use unique names** - Avoid conflicts with `uuid.uuid4().hex[:8]`
4. **Test isolation** - Don't depend on other tests' data
5. **Fast tests** - Mock external services, use small datasets

## Current Test Coverage

- **Prompts API**: 14 tests ✅
- **Agents API**: 12 tests ✅
- **Workflows API**: 13 tests ✅
- **Executions API**: 25 tests ✅
- **Tools API**: 11 tests ✅

**Total**: 75 integration tests passing

