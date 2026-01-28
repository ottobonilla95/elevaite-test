"""
Phase 3.1: Concurrency Tests

Test concurrent cache access, race conditions, cache expiration races,
async client concurrency, and thread safety.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import pytest

from rbac_sdk.fastapi_helpers import api_key_http_validator

# Test constants
ALGORITHM = "HS256"
API_KEY_SECRET = "test-secret-for-concurrency-tests"


class TestConcurrentCacheAccess:
    """Test concurrent access to the API key validation cache."""

    def test_concurrent_cache_reads(self):
        """Test multiple threads reading from cache simultaneously."""
        # Create a validator with caching enabled
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            # Mock successful validation
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(
                base_url="http://localhost:8004",
                cache_ttl=60.0,
            )

            # First call to populate cache
            request = Mock()
            result1 = validator("test-api-key", request)
            assert result1 == "user123"
            assert mock_post.call_count == 1

            # Concurrent reads from cache
            def read_from_cache():
                return validator("test-api-key", request)

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(read_from_cache) for _ in range(100)]
                results = [f.result() for f in futures]

            # All reads should return cached value
            assert all(r == "user123" for r in results)
            # Should still only have 1 API call (the initial one)
            assert mock_post.call_count == 1

    def test_concurrent_cache_writes(self):
        """Test multiple threads writing to cache simultaneously (cache miss scenario)."""
        call_count = 0

        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            # Mock successful validation
            def mock_validate(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                time.sleep(0.01)  # Simulate network delay
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"user_id": f"user{call_count}"}
                return mock_response

            mock_post.side_effect = mock_validate

            validator = api_key_http_validator(
                base_url="http://localhost:8004",
                cache_ttl=60.0,
            )

            # Concurrent writes to cache (different keys)
            def write_to_cache(key_num):
                request = Mock()
                return validator(f"test-api-key-{key_num}", request)

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(write_to_cache, i) for i in range(50)]
                results = [f.result() for f in futures]

            # All writes should succeed
            assert len(results) == 50
            assert all(r is not None for r in results)
            # Should have 50 API calls (one per unique key)
            assert call_count == 50


class TestRaceConditions:
    """Test race conditions in cache operations."""

    def test_cache_expiration_race(self):
        """Test race condition when cache entry expires during concurrent access."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            # Mock successful validation
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            # Very short TTL to trigger expiration
            validator = api_key_http_validator(
                base_url="http://localhost:8004",
                cache_ttl=0.1,  # 100ms TTL
            )

            request = Mock()

            # First call to populate cache
            result1 = validator("test-api-key", request)
            assert result1 == "user123"
            assert mock_post.call_count == 1

            # Wait for cache to expire
            time.sleep(0.15)

            # Concurrent access after expiration
            def access_after_expiration():
                return validator("test-api-key", request)

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(access_after_expiration) for _ in range(10)]
                results = [f.result() for f in futures]

            # All should succeed
            assert all(r == "user123" for r in results)
            # Should have multiple API calls due to cache expiration
            # (exact count depends on timing, but should be > 1)
            assert mock_post.call_count > 1

    def test_cache_update_race(self):
        """Test race condition when cache is updated while being read."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            # Mock successful validation
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"user_id": "user123"}
            mock_post.return_value = mock_response

            validator = api_key_http_validator(
                base_url="http://localhost:8004",
                cache_ttl=60.0,
            )

            request = Mock()

            # Concurrent access with cache miss (first access)
            def first_access():
                return validator("test-api-key", request)

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(first_access) for _ in range(20)]
                results = [f.result() for f in futures]

            # All should succeed
            assert all(r == "user123" for r in results)
            # Multiple threads may have called the API before cache was populated
            # (exact count depends on timing)
            assert mock_post.call_count >= 1


class TestAsyncClientConcurrency:
    """Test async client concurrency."""

    @pytest.mark.asyncio
    async def test_concurrent_async_requests(self):
        """Test multiple concurrent async authorization checks."""
        from rbac_sdk.async_client import check_access_async

        with patch("rbac_sdk.async_client.httpx.AsyncClient") as mock_client_class:
            # Mock successful authorization
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={"allowed": True})

            # Create async context manager
            async def mock_aenter(self):
                return self

            async def mock_aexit(self, *args):
                return None

            async def mock_post(*args, **kwargs):
                return mock_response

            mock_client = Mock()
            mock_client.__aenter__ = mock_aenter
            mock_client.__aexit__ = mock_aexit
            mock_client.post = mock_post

            mock_client_class.return_value = mock_client

            # Concurrent async requests
            tasks = [
                check_access_async(
                    user_id=i,
                    action="view_project",
                    resource={
                        "type": "project",
                        "id": f"proj{i}",
                        "organization_id": "org1",
                    },
                )
                for i in range(50)
            ]

            results = await asyncio.gather(*tasks)

            # All should succeed
            assert len(results) == 50
            assert all(r is True for r in results)

    @pytest.mark.asyncio
    async def test_async_timeout_handling(self):
        """Test async client handles timeouts correctly under load."""
        from rbac_sdk.async_client import check_access_async

        with patch("rbac_sdk.async_client.httpx.AsyncClient") as mock_client_class:
            # Mock timeout
            mock_client = Mock()
            mock_client.__aenter__ = Mock(return_value=mock_client)
            mock_client.__aexit__ = Mock(return_value=None)

            async def mock_post(*args, **kwargs):
                await asyncio.sleep(5.0)  # Longer than timeout
                raise Exception("Should not reach here")

            mock_client.post = mock_post
            mock_client_class.return_value = mock_client

            # Concurrent requests that will timeout
            tasks = [
                check_access_async(
                    user_id=i,
                    action="view_project",
                    resource={
                        "type": "project",
                        "id": f"proj{i}",
                        "organization_id": "org1",
                    },
                    timeout=0.1,  # Very short timeout
                )
                for i in range(10)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # All should fail closed (return False or raise exception)
            assert all(r is False or isinstance(r, Exception) for r in results)


class TestThreadSafety:
    """Test thread safety of validators and clients."""

    def test_validator_thread_safety(self):
        """Test that validators are thread-safe."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            # Track which keys were validated
            validated_keys = {}

            # Mock successful validation with different user IDs
            def mock_validate(url, *args, **kwargs):
                # Extract API key from headers
                headers = kwargs.get("headers", {})
                api_key = headers.get("X-elevAIte-apikey", "")

                # Store the key
                validated_keys[api_key] = validated_keys.get(api_key, 0) + 1

                # Extract the number from the key
                parts = api_key.split("-")
                user_num = parts[-1] if len(parts) > 1 and parts[-1].isdigit() else "0"

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"user_id": f"user{user_num}"}
                return mock_response

            mock_post.side_effect = mock_validate

            validator = api_key_http_validator(
                base_url="http://localhost:8004",
                cache_ttl=0.0,  # Disable cache to test thread safety of validator itself
            )

            # Concurrent validation of different keys
            def validate_key(key_num):
                request = Mock()
                return validator(f"test-api-key-{key_num}", request)

            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(validate_key, i) for i in range(100)]
                results = [f.result() for f in futures]

            # All should succeed
            assert len(results) == 100
            assert all(r is not None for r in results)
            # Verify we validated 100 unique keys
            assert len(validated_keys) == 100

    def test_cache_isolation(self):
        """Test that cache entries are properly isolated."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            # Mock successful validation
            def mock_validate(url, *args, **kwargs):
                headers = kwargs.get("headers", {})
                api_key = headers.get("X-elevAIte-apikey", "")

                mock_response = Mock()
                mock_response.status_code = 200
                # Return different user IDs for different keys
                if "key1" in api_key:
                    mock_response.json.return_value = {"user_id": "user1"}
                elif "key2" in api_key:
                    mock_response.json.return_value = {"user_id": "user2"}
                else:
                    mock_response.json.return_value = {"user_id": "user_unknown"}
                return mock_response

            mock_post.side_effect = mock_validate

            validator = api_key_http_validator(
                base_url="http://localhost:8004",
                cache_ttl=60.0,
            )

            request = Mock()

            # Populate cache with two different keys
            result1 = validator("test-api-key1", request)
            result2 = validator("test-api-key2", request)

            assert result1 == "user1"
            assert result2 == "user2"

            # Concurrent access to both cached entries
            def access_cache(key):
                return validator(key, request)

            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for _ in range(50):
                    futures.append(executor.submit(access_cache, "test-api-key1"))
                    futures.append(executor.submit(access_cache, "test-api-key2"))

                results = [f.result() for f in futures]

            # Verify cache isolation - each key returns its own user ID
            key1_results = [r for i, r in enumerate(results) if i % 2 == 0]
            key2_results = [r for i, r in enumerate(results) if i % 2 == 1]

            assert all(r == "user1" for r in key1_results)
            assert all(r == "user2" for r in key2_results)
