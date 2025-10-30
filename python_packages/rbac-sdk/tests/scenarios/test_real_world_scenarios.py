"""
Phase 5.1: FastAPI App Scenarios

Test SDK in realistic production scenarios.
"""

import time
import pytest
from unittest.mock import Mock, patch

from rbac_sdk.fastapi_helpers import (
    api_key_http_validator,
    api_key_jwt_validator,
    resource_builders,
)
from rbac_sdk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState


class TestAuthenticationFlows:
    """Test authentication flows in production scenarios."""

    def test_api_key_http_validator_with_cache(self):
        """Test API key validation with caching."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(base_url="http://localhost:8004", cache_ttl=60.0)
            request = Mock()

            result1 = validator("test-api-key", request)
            assert result1 == "user123"
            assert mock_post.call_count == 1

            result2 = validator("test-api-key", request)
            assert result2 == "user123"
            assert mock_post.call_count == 1

    def test_api_key_jwt_validator_with_valid_token(self):
        """Test JWT API key validation."""
        from jose import jwt
        import os

        secret = os.getenv("SECRET_KEY", "test-secret-key")
        token = jwt.encode({"sub": "user123", "type": "api_key"}, secret, algorithm="HS256")

        validator = api_key_jwt_validator(secret=secret)
        request = Mock()

        result = validator(token, request)
        assert result == "user123"

    def test_invalid_api_key_rejected(self):
        """Test that invalid API keys are rejected."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            validator = api_key_http_validator(base_url="http://localhost:8004", cache_ttl=0.0)
            request = Mock()

            result = validator("invalid-key", request)
            assert result is None


class TestMultiTenantIsolation:
    """Test multi-tenant isolation patterns."""

    def test_resource_builder_extracts_org_id(self):
        """Test that resource builders properly extract organization ID."""
        request = Mock()
        request.headers = {
            "X-elevAIte-OrganizationId": "org123",
            "X-elevAIte-AccountId": "acc456",
            "X-elevAIte-ProjectId": "proj789",
        }

        resource = resource_builders.project_from_headers()(request)

        assert resource["type"] == "project"
        assert resource["id"] == "proj789"
        assert resource["organization_id"] == "org123"
        assert resource["account_id"] == "acc456"

    def test_different_orgs_have_different_resources(self):
        """Test that different organizations have isolated resources."""
        request1 = Mock()
        request1.headers = {
            "X-elevAIte-OrganizationId": "org1",
            "X-elevAIte-ProjectId": "proj1",
        }

        resource1 = resource_builders.project_from_headers()(request1)
        assert resource1["organization_id"] == "org1"

        request2 = Mock()
        request2.headers = {
            "X-elevAIte-OrganizationId": "org2",
            "X-elevAIte-ProjectId": "proj2",
        }

        resource2 = resource_builders.project_from_headers()(request2)
        assert resource2["organization_id"] == "org2"

        assert resource1["organization_id"] != resource2["organization_id"]


class TestConcurrentAccess:
    """Test concurrent access patterns."""

    def test_concurrent_api_key_validation(self):
        """Test concurrent API key validation with cache."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            # Track API calls
            api_calls = []

            def mock_validate(url, *args, **kwargs):
                # Extract API key from headers
                headers = kwargs.get("headers", {})
                api_key = headers.get("X-elevAIte-apikey", "")
                api_calls.append(api_key)

                time.sleep(0.01)

                # Return unique user_id based on API key
                user_num = int(api_key.split("-")[-1])
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"user_id": f"user{user_num}"}
                return mock_response

            mock_post.side_effect = mock_validate

            validator = api_key_http_validator(base_url="http://localhost:8004", cache_ttl=60.0)
            request = Mock()

            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for i in range(10):
                    future = executor.submit(validator, f"api-key-{i}", request)
                    futures.append(future)

                results = [f.result() for f in futures]

            # Should have 10 results
            assert len(results) == 10
            # Each API key should get its own user_id
            assert len(set(results)) == 10
            # Should have called API 10 times (once per unique key)
            assert len(api_calls) == 10

    def test_cache_thread_safety(self):
        """Test that cache is thread-safe under concurrent access."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(base_url="http://localhost:8004", cache_ttl=60.0)
            request = Mock()

            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = []
                for _ in range(100):
                    future = executor.submit(validator, "same-api-key", request)
                    futures.append(future)

                results = [f.result() for f in futures]

            assert all(r == "user123" for r in results)
            assert mock_post.call_count == 1


class TestErrorHandling:
    """Test error handling in production scenarios."""

    def test_auth_api_down_fails_closed(self):
        """Test that when Auth API is down, validation fails closed."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_post.side_effect = Exception("Connection refused")

            validator = api_key_http_validator(base_url="http://localhost:8004", cache_ttl=0.0)
            request = Mock()

            result = validator("test-api-key", request)
            assert result is None

    def test_malformed_response_fails_closed(self):
        """Test that malformed responses fail closed."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_post.return_value = mock_response

            validator = api_key_http_validator(base_url="http://localhost:8004", cache_ttl=0.0)
            request = Mock()

            result = validator("test-api-key", request)
            assert result is None


class TestCircuitBreakerIntegration:
    """Test circuit breaker integration in production scenarios."""

    def test_circuit_breaker_protects_validation(self):
        """Test that circuit breaker can protect API validation calls."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=0.1)
        breaker = CircuitBreaker(config)

        call_count = 0

        def failing_function():
            """A function that always fails."""
            nonlocal call_count
            call_count += 1
            raise Exception("Service unavailable")

        # First 3 calls should fail and open circuit
        for _ in range(3):
            result = breaker.call(failing_function, fallback="fallback")
            assert result == "fallback"

        # Circuit should be open
        assert breaker.state == CircuitState.OPEN

        # Subsequent calls should be rejected without calling function
        call_count_before = call_count
        result = breaker.call(failing_function, fallback="fallback")
        assert result == "fallback"
        assert call_count == call_count_before  # No new calls

    def test_circuit_breaker_with_successful_validation(self):
        """Test circuit breaker with successful validation calls."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=0.1)
        breaker = CircuitBreaker(config)

        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(base_url="http://localhost:8004", cache_ttl=0.0)
            request = Mock()

            # Wrap validator in circuit breaker
            def validate_with_breaker(api_key):
                # Use is_failure to detect None results
                return breaker.call(
                    lambda: validator(api_key, request),
                    fallback=None,
                    is_failure=lambda result: result is None,
                )

            # Successful calls should work
            result1 = validate_with_breaker("test-api-key")
            assert result1 == "user123"

            result2 = validate_with_breaker("test-api-key")
            assert result2 == "user123"

            # Circuit should remain closed
            assert breaker.state == CircuitState.CLOSED

    def test_circuit_breaker_detects_validation_failures(self):
        """Test that circuit breaker detects validation failures."""
        config = CircuitBreakerConfig(failure_threshold=3, timeout=0.1)
        breaker = CircuitBreaker(config)

        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            # Mock 401 responses (invalid API key)
            mock_response = Mock()
            mock_response.status_code = 401
            mock_post.return_value = mock_response

            validator = api_key_http_validator(base_url="http://localhost:8004", cache_ttl=0.0)
            request = Mock()

            # Wrap validator in circuit breaker
            def validate_with_breaker(api_key):
                # Use is_failure to detect None results
                return breaker.call(
                    lambda: validator(api_key, request),
                    fallback=None,
                    is_failure=lambda result: result is None,
                )

            # First 3 calls should fail and open circuit
            for _ in range(3):
                result = validate_with_breaker("invalid-key")
                assert result is None

            # Circuit should be open
            assert breaker.state == CircuitState.OPEN
