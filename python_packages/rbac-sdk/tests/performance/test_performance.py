"""
Phase 3.2: Performance Tests

Test cache performance with 10K keys, memory usage, latency (P50/P95/P99),
throughput, and cache hit rate.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

import pytest

from rbac_sdk.fastapi_helpers import api_key_http_validator


class TestCachePerformance:
    """Test cache performance with large numbers of keys."""

    def test_cache_with_10k_keys(self):
        """Test cache performance with 10,000 unique keys."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            call_count = 0

            def mock_validate(url, *args, **kwargs):
                nonlocal call_count
                call_count += 1
                headers = kwargs.get("headers", {})
                api_key = headers.get("X-elevAIte-apikey", "")

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"user_id": f"user_{api_key}"}
                return mock_response

            mock_post.side_effect = mock_validate

            validator = api_key_http_validator(
                base_url="http://localhost:8004",
                cache_ttl=60.0,
            )

            request = Mock()

            # Populate cache with 10K keys
            start_time = time.time()
            for i in range(10000):
                result = validator(f"api-key-{i}", request)
                assert result == f"user_api-key-{i}"

            populate_time = time.time() - start_time

            # Verify all keys were cached
            assert call_count == 10000

            # Access all keys from cache
            start_time = time.time()
            for i in range(10000):
                result = validator(f"api-key-{i}", request)
                assert result == f"user_api-key-{i}"

            access_time = time.time() - start_time

            # Should still only have 10K API calls (all from cache)
            assert call_count == 10000

            # Cache access should be much faster than population
            print(f"\nPopulate 10K keys: {populate_time:.2f}s")
            print(f"Access 10K keys from cache: {access_time:.2f}s")
            print(f"Speedup: {populate_time / access_time:.1f}x")

            # Cache should be at least 5x faster
            assert access_time < populate_time / 5

    def test_cache_hit_rate(self):
        """Test cache hit rate with mixed access patterns."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            call_count = 0

            def mock_validate(url, *args, **kwargs):
                nonlocal call_count
                call_count += 1
                headers = kwargs.get("headers", {})
                api_key = headers.get("X-elevAIte-apikey", "")

                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"user_id": f"user_{api_key}"}
                return mock_response

            mock_post.side_effect = mock_validate

            validator = api_key_http_validator(
                base_url="http://localhost:8004",
                cache_ttl=60.0,
            )

            request = Mock()

            # Access pattern: 100 unique keys, each accessed 10 times
            total_accesses = 0
            for _ in range(10):
                for i in range(100):
                    result = validator(f"api-key-{i}", request)
                    assert result == f"user_api-key-{i}"
                    total_accesses += 1

            # Should only have 100 API calls (90% cache hit rate)
            assert call_count == 100
            assert total_accesses == 1000

            cache_hits = total_accesses - call_count
            hit_rate = cache_hits / total_accesses

            print(f"\nTotal accesses: {total_accesses}")
            print(f"API calls: {call_count}")
            print(f"Cache hits: {cache_hits}")
            print(f"Hit rate: {hit_rate * 100:.1f}%")

            # Should have 90% cache hit rate
            assert hit_rate >= 0.9


class TestLatency:
    """Test latency metrics (P50, P95, P99)."""

    def test_cache_access_latency(self):
        """Test latency distribution for cache access."""
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

            # Populate cache
            validator("test-api-key", request)

            # Measure latency for 1000 cache accesses
            latencies = []
            for _ in range(1000):
                start = time.perf_counter()
                result = validator("test-api-key", request)
                end = time.perf_counter()
                latencies.append((end - start) * 1000)  # Convert to ms
                assert result == "user123"

            # Calculate percentiles
            latencies.sort()
            p50 = latencies[len(latencies) // 2]
            p95 = latencies[int(len(latencies) * 0.95)]
            p99 = latencies[int(len(latencies) * 0.99)]

            print("\nCache access latency:")
            print(f"P50: {p50:.3f}ms")
            print(f"P95: {p95:.3f}ms")
            print(f"P99: {p99:.3f}ms")

            # Cache access should be very fast (< 1ms for P99)
            assert p99 < 1.0

    def test_api_call_latency(self):
        """Test latency distribution for API calls (cache miss)."""
        with patch("rbac_sdk.fastapi_helpers.requests.post") as mock_post:
            # Mock successful validation with simulated network delay
            def mock_validate(url, *args, **kwargs):
                time.sleep(0.01)  # Simulate 10ms network delay
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"user_id": "user123"}
                return mock_response

            mock_post.side_effect = mock_validate

            validator = api_key_http_validator(
                base_url="http://localhost:8004",
                cache_ttl=0.0,  # Disable cache to force API calls
            )

            request = Mock()

            # Measure latency for 100 API calls
            latencies = []
            for _ in range(100):
                start = time.perf_counter()
                result = validator("test-api-key", request)
                end = time.perf_counter()
                latencies.append((end - start) * 1000)  # Convert to ms
                assert result == "user123"

            # Calculate percentiles
            latencies.sort()
            p50 = latencies[len(latencies) // 2]
            p95 = latencies[int(len(latencies) * 0.95)]
            p99 = latencies[int(len(latencies) * 0.99)]

            print("\nAPI call latency:")
            print(f"P50: {p50:.1f}ms")
            print(f"P95: {p95:.1f}ms")
            print(f"P99: {p99:.1f}ms")

            # API calls should be slower than cache (> 10ms due to simulated delay)
            assert p50 > 10.0


class TestThroughput:
    """Test throughput metrics."""

    def test_cache_throughput(self):
        """Test cache throughput (requests per second)."""
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

            # Populate cache
            validator("test-api-key", request)

            # Measure throughput for 10,000 cache accesses
            start_time = time.time()
            for _ in range(10000):
                result = validator("test-api-key", request)
                assert result == "user123"

            elapsed = time.time() - start_time
            throughput = 10000 / elapsed

            print(f"\nCache throughput: {throughput:.0f} req/s")
            print(f"Time for 10K requests: {elapsed:.2f}s")

            # Should handle at least 10K requests per second from cache
            assert throughput > 10000

    def test_concurrent_throughput(self):
        """Test throughput with concurrent requests."""
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

            # Populate cache
            request = Mock()
            validator("test-api-key", request)

            # Measure throughput with 10 concurrent threads
            def make_requests():
                for _ in range(1000):
                    result = validator("test-api-key", request)
                    assert result == "user123"

            start_time = time.time()
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_requests) for _ in range(10)]
                for f in futures:
                    f.result()

            elapsed = time.time() - start_time
            total_requests = 10 * 1000
            throughput = total_requests / elapsed

            print(f"\nConcurrent throughput (10 threads): {throughput:.0f} req/s")
            print(f"Time for {total_requests} requests: {elapsed:.2f}s")

            # Should handle at least 50K requests per second with concurrency
            assert throughput > 50000


class TestAsyncPerformance:
    """Test async client performance."""

    @pytest.mark.asyncio
    async def test_async_throughput(self):
        """Test async client throughput."""
        from rbac_sdk.async_client import check_access_async

        with patch("rbac_sdk.async_client.httpx.AsyncClient") as mock_client_class:
            # Mock successful authorization
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = Mock(return_value={"allowed": True})

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

            # Measure throughput for 1000 concurrent async requests
            start_time = time.time()

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
                for i in range(1000)
            ]

            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start_time
            throughput = 1000 / elapsed

            print(f"\nAsync throughput: {throughput:.0f} req/s")
            print(f"Time for 1000 async requests: {elapsed:.2f}s")

            # All should succeed
            assert all(r is True for r in results)
            # Should handle at least 1000 requests per second
            assert throughput > 1000
