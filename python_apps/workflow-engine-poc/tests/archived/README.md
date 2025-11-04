# Archived Tests

This directory contains tests that have been archived because they reference outdated systems or APIs.

## RBAC Tests (Archived 2025-11-04)

The following RBAC tests were archived because they reference the old RBAC system that has been replaced with the new auth package and OPA-based RBAC:

- `test_comprehensive_rbac.py` - Comprehensive RBAC tests for old system
- `test_rbac_e2e.py` - End-to-end RBAC tests for old system
- `test_rbac_integration.py` - RBAC integration tests for old system
- `test_with_real_rbac.py` - Real RBAC tests for old system

**Total:** 24 tests archived

These tests will be rewritten from scratch to use the new auth package integration with:
- JWT-based authentication
- OPA policy evaluation
- New RBAC SDK with `require_permission_async` guards
- Proper header-based authentication (X-elevAIte-UserId, X-elevAIte-apikey, etc.)

## Why Archive Instead of Delete?

These tests contain valuable test scenarios and edge cases that should be considered when writing the new auth integration tests. They serve as reference material for:
- Permission scenarios to test (viewer, editor, admin roles)
- Header validation requirements
- Error cases and edge conditions
- API endpoint coverage

## Next Steps

New auth integration tests will be created in `tests/auth/` directory with:
- Integration with the auth package
- OPA policy testing
- API key validation
- JWT token validation
- Role-based access control scenarios

