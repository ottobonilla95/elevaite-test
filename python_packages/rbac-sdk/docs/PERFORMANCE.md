# RBAC SDK Performance Tuning Guide

Optimize the RBAC SDK for maximum performance in production environments.

## Performance Metrics

Based on comprehensive performance testing (Phase 3.2):

- **Cache Speedup:** 208x faster than API calls
- **Cache Hit Rate:** 90% with mixed access patterns
- **Throughput:** 1M+ req/s from cache, 28K req/s async
- **Latency:** P99 < 1ms for cached requests, >10ms for API calls

## Quick Wins

### 1. Enable API Key Caching (Biggest Impact)

**Before:**
```python
# No caching - every request hits Auth API
validator = api_key_http_validator(
    base_url="http://localhost:8004",
    cache_ttl=0.0,  # No caching
)
```

**After:**
```python
# With caching - 208x faster
validator = api_key_http_validator(
    base_url="http://localhost:8004",
    cache_ttl=60.0,  # Cache for 60 seconds
)
```

**Impact:** 208x speedup, reduces Auth API load by 90%

### 2. Use JWT API Keys (No HTTP Calls)

**Before:**
```python
# HTTP validation - requires network call
validator = api_key_http_validator(
    base_url="http://localhost:8004",
    cache_ttl=60.0,
)
```

**After:**
```python
# JWT validation - local only, no network call
validator = api_key_jwt_validator(
    algorithm="HS256",
    secret="your-secret-key",
)
```

**Impact:** No network latency, unlimited throughput

### 3. Use Async Guards

**Before:**
```python
# Sync guard - blocks thread
guard = require_permission(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(),
)
```

**After:**
```python
# Async guard - non-blocking
guard = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(),
)
```

**Impact:** Better concurrency, higher throughput

## Caching Strategies

### Cache TTL Selection

Choose cache TTL based on your security vs performance tradeoff:

| TTL | Use Case | Security | Performance |
|-----|----------|----------|-------------|
| 0s | Maximum security | Highest | Lowest |
| 30s | Balanced | High | Good |
| 60s | **Recommended** | Good | High |
| 300s (5min) | Low-security | Medium | Highest |

```python
# Production recommendation: 60 seconds
validator = api_key_http_validator(
    base_url="http://localhost:8004",
    cache_ttl=60.0,
)
```

### Cache Invalidation

The SDK uses time-based cache invalidation. For immediate invalidation:

1. **Restart service** - Clears all caches
2. **Wait for TTL** - Cache expires naturally
3. **Use shorter TTL** - Faster invalidation

**Note:** There is no manual cache invalidation API. This is intentional for simplicity.

### Cache Memory Usage

Cache memory usage depends on:
- Number of unique API keys
- Cache TTL
- Request rate

**Estimate:**
```
Memory = (num_unique_keys * 100 bytes) * (cache_ttl / 60)

Example:
- 1,000 unique API keys
- 60 second TTL
- Memory: 1,000 * 100 * 1 = 100 KB
```

**Monitoring:**
```python
import sys

# Check cache size
validator = api_key_http_validator(...)
cache_size = sys.getsizeof(validator.__closure__[0].cell_contents)
print(f"Cache size: {cache_size} bytes")
```

## OPA Performance

### OPA Response Time

OPA should respond in < 10ms for most queries. If slower:

1. **Check OPA logs:**
```bash
docker logs opa-container
```

2. **Profile OPA:**
```bash
curl http://localhost:8181/metrics
```

3. **Optimize Rego policies:**
- Avoid complex loops
- Use indexed lookups
- Cache policy compilation

### OPA Connection Pooling

The SDK uses `httpx` with connection pooling by default. No configuration needed.

### OPA Timeout Configuration

Default timeout is 5 seconds. Adjust if needed:

```python
# Not directly configurable in current SDK
# OPA should respond in < 10ms, so 5s timeout is generous
```

## Network Optimization

### 1. Collocate Services

**Best:** All services on same host
```
Auth API: localhost:8004
OPA: localhost:8181
Your Service: localhost:8000
```

**Good:** All services in same datacenter/VPC
```
Auth API: 10.0.1.10:8004
OPA: 10.0.1.11:8181
Your Service: 10.0.1.12:8000
```

**Avoid:** Services across internet
```
Auth API: api.example.com:8004  # High latency
OPA: opa.example.com:8181  # High latency
```

### 2. Use HTTP/2 (Future Enhancement)

Current SDK uses HTTP/1.1. HTTP/2 support planned for future release.

### 3. Reduce Header Size

Smaller headers = faster parsing:

```python
# Good: Short UUIDs
X-elevAIte-ProjectId: 550e8400-e29b-41d4-a716-446655440000

# Better: Short IDs (if possible)
X-elevAIte-ProjectId: proj-123
```

## Concurrency Optimization

### Thread Safety

The SDK is thread-safe. Cache uses thread-safe dict operations.

**Tested:** 100+ concurrent threads, no race conditions

### Async Concurrency

Use async guards for maximum concurrency:

```python
# Can handle 1000+ concurrent requests
guard = require_permission_async(...)

@router.get("/projects", dependencies=[Depends(guard)])
async def list_projects():
    ...
```

### Connection Limits

Default `httpx` connection limits:
- Max connections: 100
- Max keepalive connections: 20

For high-concurrency scenarios, increase limits:

```python
# Not directly configurable in current SDK
# Future enhancement: allow custom httpx client
```

## Monitoring & Profiling

### 1. Enable Logging

```python
import logging

# Enable DEBUG logging
logging.basicConfig(level=logging.DEBUG)

# Or just for RBAC SDK
logging.getLogger("rbac_sdk").setLevel(logging.DEBUG)
```

### 2. Measure Latency

```python
import time

start = time.time()
allowed = await check_access_async(...)
latency = time.time() - start
print(f"RBAC check took {latency*1000:.2f}ms")
```

### 3. Track Cache Hit Rate

```python
# Add instrumentation to validator
hits = 0
misses = 0

def instrumented_validator(api_key: str, request):
    global hits, misses
    # Check if in cache
    if api_key in cache:
        hits += 1
    else:
        misses += 1
    return original_validator(api_key, request)

# Print stats periodically
print(f"Cache hit rate: {hits/(hits+misses)*100:.1f}%")
```

## Production Recommendations

### Configuration

```python
# Recommended production configuration
from rbac_sdk import (
    api_key_http_validator,
    require_permission_async,
    resource_builders,
    principal_resolvers,
)

# Use HTTP validator with caching
validator = api_key_http_validator(
    base_url="http://localhost:8004",
    cache_ttl=60.0,  # 60 second cache
    timeout=3.0,  # 3 second timeout
)

# Create guard
guard = require_permission_async(
    action="view_project",
    resource_builder=resource_builders.project_from_headers(),
    principal_resolver=principal_resolvers.api_key_or_user(
        validate_api_key=validator
    ),
)
```

### Environment Variables

```bash
# Production environment variables
export AUTH_API_BASE="http://auth-api:8004"
export AUTHZ_SERVICE_URL="http://opa:8181"
export API_KEY_SECRET="your-production-secret"
export API_KEY_ALGORITHM="HS256"
```

### Deployment Checklist

- [ ] Enable API key caching (60s TTL)
- [ ] Use async guards
- [ ] Collocate services (same VPC/datacenter)
- [ ] Monitor OPA response time (< 10ms)
- [ ] Monitor cache hit rate (> 80%)
- [ ] Set up logging and alerting
- [ ] Load test before production

## Load Testing

### Test Script

```python
import asyncio
import time
from rbac_sdk import check_access_async

async def test_load():
    tasks = []
    for i in range(1000):
        task = check_access_async(
            user_id=f"user-{i % 100}",  # 100 unique users
            action="view_project",
            resource={
                "type": "project",
                "id": "proj-123",
                "organization_id": "org-456",
            }
        )
        tasks.append(task)
    
    start = time.time()
    results = await asyncio.gather(*tasks)
    duration = time.time() - start
    
    print(f"1000 requests in {duration:.2f}s")
    print(f"Throughput: {1000/duration:.0f} req/s")
    print(f"Latency: {duration/1000*1000:.2f}ms per request")

asyncio.run(test_load())
```

### Expected Results

With caching enabled:
- **Throughput:** 10,000+ req/s
- **Latency:** < 1ms per request
- **Cache hit rate:** > 90%

Without caching:
- **Throughput:** 100-500 req/s (limited by Auth API)
- **Latency:** 10-50ms per request
- **Cache hit rate:** 0%

## Troubleshooting Performance Issues

### Slow Requests

1. **Check cache hit rate** - Should be > 80%
2. **Check OPA response time** - Should be < 10ms
3. **Check Auth API response time** - Should be < 50ms
4. **Check network latency** - Should be < 5ms

### High Memory Usage

1. **Reduce cache TTL** - Lower TTL = less memory
2. **Monitor unique API keys** - More keys = more memory
3. **Restart service** - Clears cache

### Low Throughput

1. **Enable caching** - 208x speedup
2. **Use async guards** - Better concurrency
3. **Use JWT validation** - No network calls
4. **Increase connection limits** - More concurrent connections

## Future Optimizations

Planned enhancements:
- [ ] HTTP/2 support
- [ ] Configurable connection pooling
- [ ] Distributed caching (Redis)
- [ ] Metrics endpoint
- [ ] Cache warming
- [ ] Batch authorization checks

## Benchmarking

See `python_packages/rbac-sdk/tests/performance/` for benchmark code.

Run benchmarks:
```bash
cd python_packages/rbac-sdk
uv run pytest tests/performance/ -v -s
```

