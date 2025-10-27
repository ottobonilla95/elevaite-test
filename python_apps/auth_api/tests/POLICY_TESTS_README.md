# Policy Management Tests

Comprehensive test suite for the dynamic policy management system.

---

## 📋 Test Structure

```
tests/
├── unit/
│   └── test_policy_service.py          # Unit tests for PolicyService
├── integration/
│   └── test_policy_api.py               # Integration tests for API endpoints
└── e2e/
    ├── conftest.py                      # E2E test configuration
    └── test_policy_management_e2e.py    # End-to-end tests with real OPA
```

---

## 🧪 Test Types

### Unit Tests (`tests/unit/test_policy_service.py`)

Tests the `PolicyService` class in isolation with mocked HTTP calls.

**What's tested:**
- Policy upload (success/failure)
- Policy retrieval (found/not found)
- Policy deletion
- Policy listing
- Rego syntax validation
- Policy generation from JSON

**Run:**
```bash
pytest tests/unit/test_policy_service.py -v
```

**Coverage:**
- ✅ All PolicyService methods
- ✅ Error handling
- ✅ Edge cases (empty lists, invalid syntax, etc.)
- ✅ Singleton pattern

---

### Integration Tests (`tests/integration/test_policy_api.py`)

Tests the API endpoints with mocked PolicyService.

**What's tested:**
- `POST /api/policies/generate` - Generate policy from JSON
- `POST /api/policies/upload` - Upload custom rego
- `GET /api/policies` - List all policies
- `GET /api/policies/{module}` - Get specific policy
- `DELETE /api/policies/{module}` - Delete policy

**Run:**
```bash
pytest tests/integration/test_policy_api.py -v
```

**Coverage:**
- ✅ All API endpoints
- ✅ Request validation
- ✅ Response formats
- ✅ Error responses (400, 404, 500)
- ✅ Authentication (superuser required)

---

### E2E Tests (`tests/e2e/test_policy_management_e2e.py`)

Tests the complete system with real OPA instance.

**What's tested:**
- Complete policy generation flow
- Policy storage in OPA
- Policy retrieval from OPA
- Policy updates
- Policy deletion
- Multiple service policies
- Custom rego upload

**Prerequisites:**
- OPA running at `http://localhost:8181`
- Auth API running at `http://localhost:8004`

**Run:**
```bash
# Start services first
docker compose -f docker-compose.dev.yaml up -d

# Run E2E tests
pytest tests/e2e/test_policy_management_e2e.py -v --run-e2e
```

**Coverage:**
- ✅ Policy generation → OPA storage
- ✅ Policy retrieval from OPA
- ✅ Policy updates (overwrite)
- ✅ Policy deletion from OPA
- ✅ Multiple concurrent policies
- ✅ Organization-level resources

---

## 🚀 Running Tests

### Run All Tests

```bash
# Unit + Integration tests (no services required)
pytest tests/unit/test_policy_service.py tests/integration/test_policy_api.py -v

# All tests including E2E (requires running services)
pytest tests/unit/test_policy_service.py tests/integration/test_policy_api.py tests/e2e/test_policy_management_e2e.py -v --run-e2e
```

### Run Specific Test Classes

```bash
# Unit tests - PolicyService
pytest tests/unit/test_policy_service.py::TestPolicyService -v

# Integration tests - Generate endpoint
pytest tests/integration/test_policy_api.py::TestPolicyGenerateEndpoint -v

# E2E tests - Complete flow
pytest tests/e2e/test_policy_management_e2e.py::TestCompleteAuthorizationFlowE2E -v --run-e2e
```

### Run Specific Tests

```bash
# Test policy upload
pytest tests/unit/test_policy_service.py::TestPolicyService::test_upload_policy_success -v

# Test policy generation endpoint
pytest tests/integration/test_policy_api.py::TestPolicyGenerateEndpoint::test_generate_policy_success -v

# Test E2E workflow
pytest tests/e2e/test_policy_management_e2e.py::TestPolicyGenerationE2E::test_generate_workflow_policy -v --run-e2e
```

### Run with Coverage

```bash
# Unit + Integration with coverage
pytest tests/unit/test_policy_service.py tests/integration/test_policy_api.py \
  --cov=app.services.policy_service \
  --cov=app.routers.policies \
  --cov-report=html \
  --cov-report=term

# View coverage report
open htmlcov/index.html
```

---

## 🔧 Test Setup

### For Unit and Integration Tests

No setup required! These tests use mocks and don't need running services.

```bash
pytest tests/unit/test_policy_service.py tests/integration/test_policy_api.py -v
```

### For E2E Tests

**Option 1: Docker Compose (Recommended)**

```bash
# Start all services
cd python_apps/auth_api
docker compose -f docker-compose.dev.yaml up -d

# Wait for services to be ready
sleep 5

# Run E2E tests
pytest tests/e2e/test_policy_management_e2e.py -v --run-e2e

# Stop services
docker compose -f docker-compose.dev.yaml down
```

**Option 2: Manual Setup**

```bash
# Terminal 1: Start OPA
docker run -p 8181:8181 openpolicyagent/opa:latest run --server

# Terminal 2: Start Auth API
cd python_apps/auth_api
uvicorn app.main:app --reload --port 8004

# Terminal 3: Run tests
pytest tests/e2e/test_policy_management_e2e.py -v --run-e2e
```

---

## 📊 Test Coverage

### Unit Tests Coverage

| Component | Coverage |
|-----------|----------|
| `PolicyService.__init__` | ✅ 100% |
| `PolicyService.upload_policy` | ✅ 100% |
| `PolicyService.get_policy` | ✅ 100% |
| `PolicyService.delete_policy` | ✅ 100% |
| `PolicyService.list_policies` | ✅ 100% |
| `PolicyService.validate_rego_syntax` | ✅ 100% |
| `PolicyService.generate_service_policy` | ✅ 100% |
| `get_policy_service` | ✅ 100% |

### Integration Tests Coverage

| Endpoint | Test Cases |
|----------|------------|
| `POST /api/policies/generate` | ✅ Success, ✅ Invalid syntax, ✅ Upload failure, ✅ Custom belongs_to |
| `POST /api/policies/upload` | ✅ Success, ✅ Invalid syntax |
| `GET /api/policies` | ✅ Success, ✅ Empty list |
| `GET /api/policies/{module}` | ✅ Success, ✅ Not found |
| `DELETE /api/policies/{module}` | ✅ Success, ✅ Failure |

### E2E Tests Coverage

| Scenario | Test Cases |
|----------|------------|
| Policy Generation | ✅ Workflow, ✅ Multiple services, ✅ Organization-level |
| Custom Upload | ✅ Custom rego code |
| Policy Listing | ✅ List all, ✅ Get specific |
| Policy Deletion | ✅ Delete and verify |
| Complete Flow | ✅ Authorization flow, ✅ Policy updates |

---

## 🐛 Debugging Tests

### Enable Verbose Logging

```bash
pytest tests/unit/test_policy_service.py -v -s --log-cli-level=DEBUG
```

### Run Single Test with Print Statements

```bash
pytest tests/unit/test_policy_service.py::TestPolicyService::test_upload_policy_success -v -s
```

### Check OPA Directly (E2E)

```bash
# List policies in OPA
curl http://localhost:8181/v1/policies

# Get specific policy
curl http://localhost:8181/v1/policies/rbac/workflows

# Check OPA health
curl http://localhost:8181/health
```

---

## 📝 Writing New Tests

### Unit Test Template

```python
@pytest.mark.asyncio
async def test_new_feature(self, policy_service):
    """Test description"""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    
    # Act
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.method = AsyncMock(
            return_value=mock_response
        )
        result = await policy_service.method()
    
    # Assert
    assert result is True
```

### Integration Test Template

```python
@pytest.mark.asyncio
async def test_new_endpoint(self, client, mock_superuser, mock_policy_service):
    """Test description"""
    # Arrange
    with patch("app.routers.policies.require_superuser", return_value=mock_superuser), \
         patch("app.routers.policies.get_policy_service", return_value=mock_policy_service):
        
        mock_policy_service.method = AsyncMock(return_value=expected_value)
        
        # Act
        response = await client.post("/api/policies/endpoint", json={...})
        
        # Assert
        assert response.status_code == 200
```

### E2E Test Template

```python
@pytest.mark.asyncio
async def test_new_flow(self, opa_client, policy_client, opa_direct_client):
    """Test description"""
    # Arrange & Act
    result = await policy_client.generate_policy(...)
    
    # Assert
    await asyncio.sleep(0.5)  # Give OPA time to process
    opa_policy = await opa_direct_client.get_policy("rbac/test")
    assert opa_policy is not None
    
    # Cleanup
    await policy_client.delete_policy("rbac/test")
```

---

## ✅ Test Checklist

Before committing:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] E2E tests pass (with running services)
- [ ] Code coverage > 90%
- [ ] No skipped tests (unless intentional)
- [ ] All new features have tests
- [ ] Edge cases are covered
- [ ] Error handling is tested

---

## 🎯 Quick Commands

```bash
# Run all unit tests
pytest tests/unit/test_policy_service.py -v

# Run all integration tests
pytest tests/integration/test_policy_api.py -v

# Run all E2E tests (requires services)
docker compose -f docker-compose.dev.yaml up -d
pytest tests/e2e/test_policy_management_e2e.py -v --run-e2e
docker compose -f docker-compose.dev.yaml down

# Run everything with coverage
pytest tests/unit/test_policy_service.py tests/integration/test_policy_api.py \
  --cov=app.services.policy_service \
  --cov=app.routers.policies \
  --cov-report=html

# Quick smoke test
pytest tests/unit/test_policy_service.py::TestPolicyService::test_generate_service_policy_basic -v
```

---

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [OPA REST API](https://www.openpolicyagent.org/docs/latest/rest-api/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

