# Agent Studio Tests

Comprehensive test suite for the Agent Studio API with 108+ integration tests covering all API endpoints.

## Quick Start

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific API tests
pytest tests/integration/test_prompts_api.py -v

# Run with coverage
pytest tests/integration/ --cov=api --cov=services --cov-report=html
```

## Test Structure

```
tests/
├── integration/           # API integration tests (108 tests) ✅
│   ├── test_prompts_api.py       # 14 tests
│   ├── test_agents_api.py        # 12 tests
│   ├── test_workflows_api.py     # 13 tests
│   ├── test_executions_api.py    # 25 tests
│   ├── test_tools_api.py         # 11 tests
│   ├── test_files_api.py         # 14 tests
│   ├── test_analytics_api.py     # 19 tests
│   └── TEST_ENVIRONMENT.md       # Test environment guide
│
├── unit/                  # Unit tests for individual components
├── functional/            # Functional tests for features
├── workflows/             # Workflow-specific tests
├── analytics/             # Analytics component tests
├── e2e/                   # End-to-end tests
├── metrics/               # Metrics and monitoring tests
├── smoke/                 # Smoke tests for quick validation
│
├── conftest.py            # Shared fixtures and configuration
├── SECRETS_MANAGEMENT.md  # Guide for managing API keys
└── README.md              # This file
```

## Integration Tests (108 tests)

Our comprehensive integration test suite covers all API endpoints with **108 tests passing in 1.57 seconds**.

### Coverage by API Module

| API Module | Tests | Coverage |
|------------|-------|----------|
| Prompts API | 14 | CRUD, pagination, filtering, duplicates |
| Agents API | 12 | All agent types, lifecycle, errors |
| Workflows API | 13 | Multi-step, connections, tags, pagination |
| Executions API | 25 | Status, results, traces, analytics |
| Tools API | 11 | List, search, pagination, parameters |
| Files API | 14 | Upload, list, delete, configuration |
| Analytics API | 19 | Usage stats, performance, summaries |

## Test Environment

### Environment Variables

Tests use a three-tier approach for environment configuration:

1. **`.env.test`** (committed) - Safe defaults, no real secrets
2. **`.env.test.local`** (gitignored) - Your personal API keys
3. **Environment variables** - CI/CD secrets (highest priority)

See [SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md) for complete guide.

### Quick Setup

**Default (mock keys):**
```bash
pytest tests/integration/ -v
```

**With real API keys:**
```bash
cp .env.test .env.test.local
# Edit .env.test.local with your real keys
pytest tests/integration/ -v
```

⚠️ **Warning**: Real API keys will make actual API calls and incur costs!

## Running Tests

### All Integration Tests
```bash
pytest tests/integration/ -v
```

### Specific Test File
```bash
pytest tests/integration/test_prompts_api.py -v
```

### Specific Test
```bash
pytest tests/integration/test_prompts_api.py::TestPromptsAPI::test_create_prompt_success -v
```

### With Coverage
```bash
pytest tests/integration/ --cov=api --cov=services --cov-report=html
open htmlcov/index.html
```

### Parallel Execution
```bash
pytest tests/integration/ -n auto
```

## Test Fixtures

### `test_db_session`
Provides an isolated database session with automatic rollback.

### `test_client`
Provides a FastAPI TestClient with database override.

### `mock_openai_client`
Mocks OpenAI API calls to prevent real charges.

See [conftest.py](conftest.py) for all available fixtures.

## Writing New Tests

### Integration Test Template

```python
"""Integration tests for [Feature] API endpoints."""

import pytest
from fastapi.testclient import TestClient


class Test[Feature]API:
    """Test suite for [Feature] API endpoints."""

    def test_create_success(self, test_client: TestClient):
        """Test creating a [feature] successfully."""
        response = test_client.post(
            "/api/[feature]/",
            json={"name": "Test", ...},
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
```

### Best Practices

1. **Use unique names** - Avoid conflicts with `uuid.uuid4().hex[:8]`
2. **Clean up resources** - Delete created entities in tests
3. **Test isolation** - Don't depend on other tests' data
4. **Fast tests** - Mock external services, use small datasets
5. **Clear assertions** - Test one thing per test
6. **Descriptive names** - Test names should describe what they test

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: elevaite
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run tests
        env:
          TEST_DATABASE_URL: postgresql://postgres:elevaite@localhost:5432/test
          TEST_OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: pytest tests/integration/ -v --cov
```

## Documentation

- **[SECRETS_MANAGEMENT.md](SECRETS_MANAGEMENT.md)** - Managing API keys and secrets
- **[integration/TEST_ENVIRONMENT.md](integration/TEST_ENVIRONMENT.md)** - Test environment configuration
- **[e2e/README.md](e2e/README.md)** - End-to-end testing guide

## Troubleshooting

### Tests fail with "connection refused"
**Solution**: Start services with `docker-compose up -d`

### Tests fail with "table does not exist"
**Solution**: Run migrations with `alembic upgrade head`

### Tests make real API calls
**Solution**: Unset the key or use `mock_openai_client` fixture

### Tests are slow
**Solution**: Mock external services, use smaller test database

## Current Status

✅ **108 integration tests passing**  
⚡ **1.57 seconds execution time**  
🔒 **No secrets in repository**  
📊 **Comprehensive API coverage**

Last updated: 2025-10-15

