# RBAC SDK Test Suite Summary

## Overview

This test suite contains **brutal, comprehensive unit tests** for the RBAC SDK. The goal is simple: **if a test fails and it's not obvious why, we need to find the bug**.

## Test Statistics

| Category | Test Files | Test Classes | Test Methods | Coverage Target |
|----------|-----------|--------------|--------------|-----------------|
| **Total** | 6 | 30+ | 150+ | 90%+ |

## Test Files

### 1. `test_client.py` - Synchronous Client Tests

**Purpose**: Test the synchronous `check_access()` client that calls the Auth API.

**Test Classes**:
- `TestCheckAccessHappyPath` - Successful authorization scenarios
- `TestCheckAccessNetworkFailures` - Connection errors, timeouts, HTTP errors
- `TestCheckAccessMalformedResponses` - Invalid JSON, missing fields, type issues
- `TestCheckAccessEdgeCases` - Boundary conditions, empty values, special cases

**Key Tests**:
- ✅ Allowed/denied responses
- ✅ Custom base URLs and timeouts
- ✅ Connection errors raise `RBACClientError`
- ✅ Timeouts raise `RBACClientError`
- ✅ HTTP 404/500/401 errors raise `RBACClientError`
- ✅ Missing `allowed` field defaults to False
- ✅ Empty response defaults to False
- ✅ Invalid JSON raises `RBACClientError`
- ✅ Null/string/numeric `allowed` values handled correctly
- ✅ Zero/negative user IDs passed through
- ✅ Empty action/resource passed through

**Critical Finding**: `bool("false")` returns `True` in Python! This is tested and documented.

---

### 2. `test_async_client.py` - Asynchronous Client Tests

**Purpose**: Test the async `check_access_async()` client with fail-closed semantics.

**Test Classes**:
- `TestCheckAccessAsyncHappyPath` - Successful authorization scenarios
- `TestCheckAccessAsyncFailClosed` - **Critical**: All errors return False, not exceptions
- `TestCheckAccessAsyncMalformedResponses` - Invalid responses
- `TestCheckAccessAsyncEdgeCases` - Boundary conditions

**Key Tests**:
- ✅ Allowed/denied responses
- ✅ Custom base URLs and timeouts
- ✅ **Connection errors return False** (fail-closed)
- ✅ **Timeouts return False** (fail-closed)
- ✅ **HTTP errors return False** (fail-closed)
- ✅ **Any exception returns False** (fail-closed)
- ✅ 404/500/401/403 status codes return False
- ✅ Missing `allowed` field returns False
- ✅ Invalid JSON returns False
- ✅ Null/zero/one `allowed` values handled correctly

**Security Principle**: **Fail-closed** - when in doubt, deny access. This is critical for security.

---

### 3. `test_principal_resolvers.py` - Principal Resolution Tests

**Purpose**: Test user ID and API key resolution from request headers.

**Test Classes**:
- `TestDefaultPrincipalResolver` - Default user ID header resolver
- `TestUserIdHeaderResolver` - Custom user ID header resolver
- `TestApiKeyOrUserResolver` - API key with fallback to user ID
- `TestApiKeyOrUserEnvironmentVariables` - Environment variable handling
- `TestPrincipalResolverSecurityEdgeCases` - **Security-critical edge cases**

**Key Tests**:
- ✅ User ID header extraction
- ✅ Missing user ID raises 401
- ✅ Empty user ID raises 401
- ✅ Custom header names
- ✅ API key validation with custom validator
- ✅ API key validation failure raises 401
- ✅ Fallback to user ID when no API key
- ✅ Local JWT validation (when enabled)
- ✅ Insecure fallback mode (dev only)
- ✅ API key without validator raises 401
- ✅ Environment variables: `RBAC_SDK_ALLOW_INSECURE_APIKEY_AS_PRINCIPAL`
- ✅ Environment variables: `RBAC_SDK_APIKEY_ENABLE_LOCAL_JWT`
- ✅ **SQL injection in user ID** (passed through - server validates)
- ✅ **XSS in user ID** (passed through - server validates)
- ✅ **Very long user IDs** (10,000+ chars)
- ✅ **Unicode in user IDs**
- ✅ **Null bytes in user IDs**

**Security Note**: The SDK does NOT validate/sanitize user IDs. This is intentional - validation is server-side.

---

### 4. `test_resource_builders.py` - Resource Building Tests

**Purpose**: Test resource dictionary construction from request headers.

**Test Classes**:
- `TestProjectFromHeaders` - Project resource building
- `TestAccountFromHeaders` - Account resource building
- `TestOrganizationFromHeaders` - Organization resource building
- `TestResourceBuilderSecurityEdgeCases` - **Security-critical edge cases**
- `TestResourceBuilderConsistency` - Consistency across builders

**Key Tests**:
- ✅ All headers extracted correctly
- ✅ Missing required headers raise 400
- ✅ Optional headers (account_id) handled correctly
- ✅ Empty header strings raise 400
- ✅ Custom header names
- ✅ Resource type field consistency
- ✅ **SQL injection in resource IDs** (passed through)
- ✅ **Path traversal in resource IDs** (passed through)
- ✅ **Very long IDs** (10,000+ chars)
- ✅ **Unicode in IDs**
- ✅ **Special characters in IDs**
- ✅ **Null bytes in IDs**
- ✅ **Whitespace-only IDs** (truthy in Python)

**Security Note**: The SDK does NOT validate/sanitize resource IDs. This is intentional - validation is server-side.

---

### 5. `test_api_key_validators.py` - API Key Validation Tests

**Purpose**: Test HTTP-based and JWT-based API key validation.

**Test Classes**:
- `TestApiKeyHttpValidator` - HTTP-based validation via Auth API
- `TestApiKeyHttpValidatorCaching` - Cache behavior (TTL, expiration)
- `TestApiKeyJwtValidator` - Local JWT validation

**Key Tests**:

**HTTP Validator**:
- ✅ Successful validation returns user_id
- ✅ 401 response returns None
- ✅ 500 response returns None
- ✅ Connection errors return None
- ✅ Timeouts return None
- ✅ Missing user_id in response returns None
- ✅ Invalid JSON returns None
- ✅ Custom path, header name, timeout
- ✅ Extra headers included
- ✅ Missing AUTH_API_BASE raises RuntimeError
- ✅ Environment variable AUTH_API_BASE used

**Caching**:
- ✅ Successful validations cached
- ✅ Cache expires after TTL
- ✅ Cache disabled with TTL=0
- ✅ Different keys cached separately
- ✅ Failed validations NOT cached

**JWT Validator**:
- ✅ HS256 algorithm support
- ✅ RS256 algorithm support
- ✅ Wrong token type returns None
- ✅ Missing 'sub' claim returns None
- ✅ JWT decode errors return None
- ✅ Generic exceptions return None
- ✅ Missing jose library returns None
- ✅ Type requirement can be disabled
- ✅ Environment variables used
- ✅ Missing secret/public key returns None
- ✅ Unsupported algorithm returns None

---

### 6. `test_guards.py` - Guard/Dependency Tests

**Purpose**: Test FastAPI dependency guards that enforce RBAC.

**Test Classes**:
- `TestRequirePermissionSync` - Synchronous guard tests
- `TestRequirePermissionAsync` - Asynchronous guard tests
- `TestGuardIntegration` - Integration scenarios
- `TestGuardErrorHandling` - Error propagation

**Key Tests**:

**Sync Guards**:
- ✅ Allowed access passes through
- ✅ Denied access raises 403
- ✅ Missing user ID raises 401
- ✅ Missing resource headers raise 400
- ✅ Custom principal resolver used
- ✅ Custom base URL passed through
- ✅ RBAC service errors propagated

**Async Guards**:
- ✅ Allowed access passes through
- ✅ Denied access raises 403
- ✅ Missing user ID raises 401
- ✅ Missing resource headers raise 400
- ✅ Custom principal resolver used
- ✅ Custom base URL passed through
- ✅ Service failure returns False (fail-closed)
- ✅ Missing async client raises 500

**Integration**:
- ✅ Multiple guards on same endpoint
- ✅ API key authentication
- ✅ Different resource types (project/account/org)

**Error Handling**:
- ✅ Principal resolver exceptions propagated
- ✅ Resource builder exceptions propagated

---

## Security Edge Cases Tested

### Input Validation

The SDK **intentionally does NOT validate or sanitize** user inputs. This is by design:
- **Client-side validation is not security** - it can be bypassed
- **Server-side validation is the only real security**
- The SDK passes inputs through to the Auth API, which validates them

We test that malicious inputs are **passed through correctly**:

| Attack Vector | Test Coverage | Expected Behavior |
|---------------|---------------|-------------------|
| SQL Injection | ✅ | Passed to server |
| XSS | ✅ | Passed to server |
| Path Traversal | ✅ | Passed to server |
| Unicode | ✅ | Handled correctly |
| Null Bytes | ✅ | Handled correctly |
| Very Long Strings | ✅ | Handled correctly |
| Special Characters | ✅ | Handled correctly |

### Fail-Closed Semantics

The async client implements **fail-closed** semantics:

| Error Type | Sync Client | Async Client |
|------------|-------------|--------------|
| Connection Error | Raises `RBACClientError` | Returns `False` |
| Timeout | Raises `RBACClientError` | Returns `False` |
| HTTP Error | Raises `RBACClientError` | Returns `False` |
| Invalid JSON | Raises `RBACClientError` | Returns `False` |
| Any Exception | Raises `RBACClientError` | Returns `False` |

**Why different?**
- **Sync client**: Used in non-critical paths, caller can handle exceptions
- **Async client**: Used in FastAPI dependencies, must not crash the app

Both approaches are **secure by default**: when in doubt, deny access.

---

## Type Coercion Gotchas

Python's type coercion can cause bugs. We test for these:

```python
bool("false")  # True  ⚠️ Non-empty string is truthy!
bool("true")   # True
bool("")       # False
bool(0)        # False
bool(1)        # True
bool(None)     # False
```

**Implication**: If the Auth API returns `{"allowed": "false"}` (string), the SDK will treat it as `True`!

**Solution**: The Auth API should return boolean `true`/`false`, not strings.

---

## Running the Tests

### Quick Start

```bash
cd python_packages/rbac-sdk
make install
make test
```

### With Coverage

```bash
make test-cov
```

### Fast (Parallel)

```bash
make test-fast
```

### Specific Test File

```bash
make test-client
make test-async-client
make test-principal-resolvers
make test-resource-builders
make test-api-key-validators
make test-guards
```

### Debug Mode

```bash
make test-debug
```

---

## Coverage Target

**Minimum**: 90%  
**Goal**: 95%+

Run coverage report:

```bash
make test-cov
```

---

## CI/CD Integration

Add to your CI pipeline:

```yaml
- name: Test RBAC SDK
  run: |
    cd python_packages/rbac-sdk
    make install
    make test-cov
```

---

## What's NOT Tested

These require integration tests (not unit tests):

- ❌ Real network calls to Auth API
- ❌ Real OPA policy evaluation
- ❌ Real database queries
- ❌ Real JWT signing/verification
- ❌ Multi-threading/concurrency issues
- ❌ Performance under load

These should be covered by:
- Integration tests (Auth API + RBAC SDK)
- End-to-end tests (Full stack)
- Load tests (Performance)

---

## Maintenance

When adding new features:

1. ✅ Write tests FIRST (TDD)
2. ✅ Cover happy path
3. ✅ Cover failure modes
4. ✅ Cover edge cases
5. ✅ Cover security concerns
6. ✅ Update this summary

When fixing bugs:

1. ✅ Write a failing test that reproduces the bug
2. ✅ Fix the bug
3. ✅ Verify the test passes
4. ✅ Add regression test to prevent recurrence

---

## Questions?

If you have questions about the tests:

1. Read the test name - it should be self-explanatory
2. Read the test docstring - it should explain the scenario
3. Read the test code - it should be obvious
4. If it's not obvious, **improve the test**

The goal is: **no mystery tests**.

