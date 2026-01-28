# RBAC SDK Test Suite

This is a **brutal, comprehensive test suite** for the RBAC SDK. These tests are designed to catch every possible failure mode, edge case, and security concern.

## Test Philosophy

These tests follow a "no mercy" approach:
- **If something can fail, we test it**
- **If there's an edge case, we cover it**
- **If there's a security concern, we validate it**
- **If the test fails and it's not obvious, there's a real bug**

## Test Coverage

### 1. Synchronous Client (`test_client.py`)
- ✅ Happy path (allowed/denied)
- ✅ Network failures (connection errors, timeouts, HTTP errors)
- ✅ Malformed responses (missing fields, invalid JSON, null values)
- ✅ Edge cases (zero/negative user IDs, empty strings, custom timeouts)
- ✅ URL handling (trailing slashes, custom base URLs)

### 2. Asynchronous Client (`test_async_client.py`)
- ✅ Happy path (allowed/denied)
- ✅ **Fail-closed semantics** (all errors return False, not exceptions)
- ✅ Network failures (connection, timeout, HTTP errors)
- ✅ Malformed responses (missing fields, invalid JSON, type coercion)
- ✅ Edge cases (zero/negative user IDs, custom timeouts)

### 3. Principal Resolvers (`test_principal_resolvers.py`)
- ✅ User ID header resolution
- ✅ API key resolution with validators
- ✅ Fallback behavior (API key → user ID)
- ✅ Environment variable handling
- ✅ Local JWT validation
- ✅ Insecure fallback mode (dev only)
- ✅ **Security edge cases** (SQL injection, XSS, Unicode, null bytes)

### 4. Resource Builders (`test_resource_builders.py`)
- ✅ Project resource building
- ✅ Account resource building
- ✅ Organization resource building
- ✅ Missing header validation
- ✅ Custom header names
- ✅ **Security edge cases** (SQL injection, path traversal, special characters)
- ✅ Consistency across builders

### 5. API Key Validators (`test_api_key_validators.py`)
- ✅ HTTP-based validation
- ✅ JWT-based validation
- ✅ Caching behavior (TTL, expiration, cache misses)
- ✅ Network failures
- ✅ Algorithm support (HS256, RS256, ES256)
- ✅ Environment variable configuration
- ✅ Missing dependencies (jose library)

### 6. Guards (`test_guards.py`)
- ✅ Synchronous guards (require_permission)
- ✅ Asynchronous guards (require_permission_async)
- ✅ Principal resolution integration
- ✅ Resource building integration
- ✅ Custom resolvers and builders
- ✅ Multiple guards on same endpoint
- ✅ Different resource types
- ✅ Error propagation

## Running the Tests

### Prerequisites

Install test dependencies:

```bash
cd python_packages/rbac-sdk
pip install -e ".[test]"
```

Or with uv:

```bash
cd python_packages/rbac-sdk
uv pip install -e ".[test]"
```

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=rbac_sdk --cov-report=html
```

Then open `htmlcov/index.html` in your browser.

### Run Specific Test Files

```bash
# Test only the sync client
pytest tests/test_client.py

# Test only the async client
pytest tests/test_async_client.py

# Test only principal resolvers
pytest tests/test_principal_resolvers.py

# Test only resource builders
pytest tests/test_resource_builders.py

# Test only API key validators
pytest tests/test_api_key_validators.py

# Test only guards
pytest tests/test_guards.py
```

### Run Specific Test Classes

```bash
# Test only happy path scenarios
pytest tests/test_client.py::TestCheckAccessHappyPath

# Test only fail-closed semantics
pytest tests/test_async_client.py::TestCheckAccessAsyncFailClosed

# Test only security edge cases
pytest tests/test_principal_resolvers.py::TestPrincipalResolverSecurityEdgeCases
```

### Run Specific Tests

```bash
# Test a specific scenario
pytest tests/test_client.py::TestCheckAccessHappyPath::test_check_access_allowed

# Test SQL injection handling
pytest tests/test_resource_builders.py::TestResourceBuilderSecurityEdgeCases::test_sql_injection_in_project_id
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Extra Verbose Output (show all assertions)

```bash
pytest -vv
```

### Run Only Async Tests

```bash
pytest -m asyncio
```

### Run Only Non-Async Tests

```bash
pytest -m "not asyncio"
```

### Run Tests in Parallel (faster)

```bash
pytest -n auto
```

### Run Tests with Debugging

```bash
# Stop on first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest -x --pdb
```

## Test Metrics

Current test coverage target: **90%+**

Run coverage report:

```bash
pytest --cov=rbac_sdk --cov-report=term-missing
```

## Known Edge Cases Tested

### Security-Critical

1. **SQL Injection**: User IDs and resource IDs with SQL injection attempts are passed through (validation is server-side)
2. **XSS**: User IDs with XSS payloads are passed through
3. **Path Traversal**: Resource IDs with path traversal attempts are passed through
4. **Unicode**: All inputs handle Unicode characters
5. **Null Bytes**: All inputs handle null bytes
6. **Very Long Strings**: All inputs handle 10,000+ character strings

### Fail-Closed Semantics

The async client implements **fail-closed** semantics:
- Network errors → return False (deny access)
- Timeouts → return False (deny access)
- HTTP errors → return False (deny access)
- Invalid JSON → return False (deny access)
- Any exception → return False (deny access)

This is **critical for security**: when in doubt, deny access.

### Type Coercion Bugs

We test for Python's type coercion quirks:
- `bool("false")` → `True` (non-empty string is truthy!)
- `bool(0)` → `False`
- `bool(1)` → `True`
- `bool(None)` → `False`
- `bool("")` → `False`

### Caching Behavior

API key HTTP validator caching is tested for:
- Cache hits (same key within TTL)
- Cache misses (different keys)
- Cache expiration (after TTL)
- Cache disabled (TTL=0)
- Failed validations not cached

## Continuous Integration

These tests should be run in CI on every commit:

```yaml
# Example GitHub Actions workflow
- name: Run RBAC SDK Tests
  run: |
    cd python_packages/rbac-sdk
    pip install -e ".[test]"
    pytest --cov=rbac_sdk --cov-fail-under=90
```

## Adding New Tests

When adding new functionality to the SDK:

1. **Add happy path tests first** - verify it works
2. **Add failure tests** - verify it fails correctly
3. **Add edge case tests** - verify boundary conditions
4. **Add security tests** - verify malicious inputs are handled
5. **Update this README** - document what you tested

## Test Naming Convention

- Test files: `test_<module>.py`
- Test classes: `Test<Feature><Scenario>`
- Test methods: `test_<what>_<condition>`

Examples:
- `test_check_access_allowed` - happy path
- `test_check_access_connection_error_returns_false` - failure mode
- `test_sql_injection_in_user_id` - security edge case

## Debugging Failed Tests

If a test fails:

1. **Read the test name** - it should tell you what failed
2. **Read the assertion message** - it should tell you why
3. **Check the test code** - it should be obvious what's being tested
4. **If it's not obvious, there's a bug** - either in the test or the code

The goal is: **no mystery failures**.

## Performance

These tests are designed to run fast:
- All tests use mocks (no real network calls)
- No database dependencies
- No external service dependencies
- Should complete in < 5 seconds

If tests are slow, something is wrong.

## Future Enhancements

Potential additions:
- [ ] Property-based testing with Hypothesis
- [ ] Mutation testing with mutmut
- [ ] Load testing for caching behavior
- [ ] Integration tests with real Auth API
- [ ] Contract tests with Pact

