# CI/CD Testing Setup for Workflow Engine PoC

This document describes the CI/CD testing infrastructure set up for the workflow-engine-poc.

## Overview

A comprehensive testing and CI/CD pipeline has been established to ensure code quality and prevent regressions.

## What Was Set Up

### 1. GitHub Actions Workflow (`.github/workflows/test-workflow-engine-poc.yml`)

**Triggers:**
- Pull requests to `main` or `testing` branches
- Pushes to `main` or `testing` branches
- Changes to `python_apps/workflow-engine-poc/**` or `packages/workflow-core-sdk/**`

**Jobs:**

#### Test Job (Always Runs)
- Sets up PostgreSQL and Redis services
- Installs Python 3.11 and dependencies via `uv`
- Runs unit and integration tests (excluding E2E)
- Generates coverage reports (XML, HTML, terminal)
- Uploads coverage to Codecov
- Posts coverage comments on PRs
- **Minimum coverage**: 70% (green), 50% (orange)

#### E2E Test Job (Optional)
- Only runs on push or with `run-e2e` label
- Starts the workflow engine server
- Runs end-to-end tests
- Uploads test results as artifacts

#### Lint Job
- Runs Ruff for linting and formatting checks
- Runs MyPy for type checking
- Non-blocking (won't fail CI)

### 2. Pytest Configuration (`pytest.ini`)

**Test Markers:**
- `unit`: Fast tests with no external dependencies
- `integration`: Tests with database/Redis
- `e2e`: End-to-end tests requiring running server
- `slow`: Tests taking >5 seconds
- `requires_openai`: Tests needing OpenAI API key
- `requires_anthropic`: Tests needing Anthropic API key
- `requires_external`: Tests needing external services
- `smoke`: Quick validation tests

**Coverage Settings:**
- Source: `workflow_engine_poc`
- Excludes: tests, migrations, scripts, debug
- Shows missing lines
- Precision: 2 decimal places

### 3. Test Fixtures (`tests/conftest.py`)

**Database Fixtures:**
- `engine`: In-memory SQLite engine
- `session`: Database session with automatic rollback
- `test_client`: FastAPI TestClient with DB override
- `clean_database`: Ensures clean DB before/after tests

**Mock Services:**
- `mock_openai_client`: Prevents real OpenAI API calls
- `mock_anthropic_client`: Prevents real Anthropic API calls
- `mock_redis`: Mocks Redis for tests that don't need it

**Test Data Factories:**
- `sample_workflow_data`: Sample workflow for testing
- `sample_agent_data`: Sample agent configuration
- `sample_prompt_data`: Sample prompt data
- `sample_tool_data`: Sample tool definition

**Environment:**
- `setup_test_environment`: Sets test env vars for entire session
- `reset_app_state`: Resets app state between tests

### 4. Documentation

**TESTING.md:**
- Comprehensive testing guide
- How to run tests (all, unit, integration, E2E)
- How to write tests (with examples)
- Test markers and fixtures
- Coverage requirements and gaps
- Troubleshooting guide
- Contributing guidelines

**test_template.py.example:**
- Template file for writing new tests
- Examples of all test patterns:
  - Unit tests
  - Integration tests
  - API tests
  - Error handling tests
  - Async tests
  - Parametrized tests
  - E2E tests
  - Fixture usage

**CI_SETUP.md (this file):**
- Overview of CI/CD setup
- What was configured
- How to use it

## Current Test Status

### Test Count
- **44 tests** total
- **Unit tests**: 8 (error handling, conditional execution, monitoring)
- **Integration tests**: 6 (API endpoints, workflow execution)
- **E2E tests**: 30 (streaming, approvals, multi-agent workflows)

### Test Results (as of setup)
- **Passing**: 13 tests
- **Failing**: 28 tests (mostly E2E tests requiring running server)
- **Skipped**: 3 tests (require external services)

### Coverage Gaps Identified

**Critical (Must Fix):**
1. RBAC/Security tests (authentication, authorization, tenant isolation)
2. Router/API tests (agents, tools, prompts, messages, approvals)
3. Error handling tests (validation, failures, timeouts)

**High Priority:**
4. Service tests (WorkflowsService, ExecutionsService, AgentsService, ToolsService)
5. Business logic tests (scheduler, streaming, DBOS integration)

**Medium Priority:**
6. Data integrity tests (transactions, constraints, cascades)
7. Performance tests (load, concurrency, memory)

See [TESTING.md](TESTING.md) for detailed coverage requirements.

## How to Use

### For Developers

**Before Committing:**
```bash
# Run tests locally
cd python_apps/workflow-engine-poc
pytest tests/ -m "not e2e" --ignore=tests/e2e/

# Check coverage
pytest tests/ -m "not e2e" --ignore=tests/e2e/ --cov=workflow_engine_poc --cov-report=html
open htmlcov/index.html
```

**Writing New Tests:**
1. Copy `tests/test_template.py.example` to `tests/test_<feature>.py`
2. Use appropriate test markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
3. Use fixtures from `conftest.py`
4. Follow naming conventions (`test_<what_it_tests>`)
5. Add docstrings explaining what the test validates

**Running Specific Tests:**
```bash
# Unit tests only (fast)
pytest tests/ -m unit

# Integration tests only
pytest tests/ -m integration

# Specific test file
pytest tests/test_error_handling.py -v

# Specific test function
pytest tests/test_error_handling.py::test_retry_mechanisms -v
```

### For Reviewers

**On Pull Requests:**
1. Check that tests pass in CI
2. Review coverage report (posted as PR comment)
3. Ensure new code has tests (aim for >80% coverage)
4. Verify test quality (not just happy paths)

**Running E2E Tests:**
Add the `run-e2e` label to the PR to trigger E2E tests in CI.

### For CI/CD

**Automatic Triggers:**
- Tests run automatically on PR creation/update
- Tests run on push to `main` or `testing`
- Only runs if relevant files changed

**Manual Triggers:**
- Add `run-e2e` label to PR to run E2E tests
- Re-run failed jobs from GitHub Actions UI

**Coverage Reports:**
- Coverage posted as PR comment
- Coverage artifacts uploaded for 7 days
- Codecov integration (if token configured)

## Environment Variables

### Required for Tests
```bash
# Database (provided by CI services)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/workflow_test
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=workflow_test
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis (provided by CI services)
REDIS_HOST=localhost
REDIS_PORT=6379

# Test environment
ENVIRONMENT=test
TESTING=true
SKIP_EXTERNAL_SERVICES=true

# Mock API keys (for tests that need them)
OPENAI_API_KEY=sk-test-mock-key-for-testing-only
ANTHROPIC_API_KEY=sk-ant-test-mock-key-for-testing-only

# Disable telemetry
OTEL_SDK_DISABLED=true
OTLP_ENDPOINT=
```

### Optional for E2E Tests
```bash
# Real API keys (use secrets in CI)
OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY_TEST }}
ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY_TEST }}
```

## Next Steps

### Immediate (High Priority)

1. **Fix Broken E2E Tests**
   - Many E2E tests fail because they expect a running server
   - Options:
     - Convert to integration tests using TestClient
     - Set up proper E2E test infrastructure
     - Mark as `@pytest.mark.skip` until infrastructure is ready

2. **Add Critical Missing Tests**
   - RBAC/Security tests
   - Router tests (agents, tools, prompts, messages)
   - Service tests (WorkflowsService, ExecutionsService, etc.)

3. **Improve Coverage**
   - Current coverage is unknown (need to run with coverage)
   - Target: >70% overall, >80% for new code

### Medium Term

4. **Set up Codecov**
   - Add `CODECOV_TOKEN` to GitHub secrets
   - Enable coverage tracking and trends

5. **Add Performance Tests**
   - Load testing
   - Stress testing
   - Memory profiling

6. **Add Security Tests**
   - SQL injection tests
   - XSS tests
   - Authentication bypass tests

### Long Term

7. **Set up Test Data Management**
   - Fixtures for common scenarios
   - Test data generators
   - Database seeding for E2E tests

8. **Add Mutation Testing**
   - Use `mutmut` or similar
   - Ensure tests actually catch bugs

9. **Set up Visual Regression Testing**
   - For any UI components
   - Screenshot comparison

## Troubleshooting

### Tests Fail Locally But Pass in CI
- Check Python version (CI uses 3.11)
- Check environment variables
- Check database state (clean DB in CI)

### Tests Pass Locally But Fail in CI
- Check for race conditions
- Check for hardcoded paths
- Check for missing dependencies

### Coverage Too Low
- Add tests for uncovered code
- Remove dead code
- Mark intentionally untested code with `# pragma: no cover`

### E2E Tests Timeout
- Increase timeout in pytest.ini
- Check if server is actually running
- Check network connectivity

## Resources

- [TESTING.md](TESTING.md) - Detailed testing guide
- [test_template.py.example](tests/test_template.py.example) - Test template
- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [GitHub Actions](https://docs.github.com/en/actions)

