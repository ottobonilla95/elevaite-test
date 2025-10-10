from __future__ import annotations

import hashlib
from typing import Optional, Iterable, Any

import asyncio

try:
    # Prefer redis.asyncio if available
    from redis.asyncio import Redis
except Exception:  # pragma: no cover
    Redis = None  # type: ignore

from app.core.config import settings
from app.core.metrics import metrics

_redis_client: Optional[Any] = None
_redis_init_lock = asyncio.Lock()


def _hash_sid(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


async def get_client() -> Optional[Any]:
    global _redis_client

    if not settings.REDIS_ENABLED:
        return None

    if Redis is None:
        return None

    if _redis_client is not None:
        return _redis_client

    async with _redis_init_lock:
        if _redis_client is not None:
            return _redis_client
        host = settings.REDIS_HOST or "localhost"
        kwargs = {
            "host": str(host),
            "port": int(settings.REDIS_PORT),
            "db": int(settings.REDIS_DB),
            "decode_responses": True,
            "socket_timeout": float(settings.REDIS_SOCKET_TIMEOUT),
            "socket_connect_timeout": float(settings.REDIS_CONNECT_TIMEOUT),
            "health_check_interval": 30,
        }
        if settings.REDIS_USERNAME:
            kwargs["username"] = str(settings.REDIS_USERNAME)
        if settings.REDIS_PASSWORD:
            kwargs["password"] = str(settings.REDIS_PASSWORD)
        client = Redis(**kwargs)
        try:
            await client.ping()
            metrics.availability(True)
        except Exception:
            # Could not connect; disable usage
            metrics.availability(False)
            return None
        _redis_client = client
        return _redis_client


# Key helpers (tenant-scoped)


def sess_key(tenant_id: str, sid: str) -> str:
    return f"sess:{tenant_id}:{sid}"


def user_sessions_key(tenant_id: str, user_id: int) -> str:
    return f"user:sessions:{tenant_id}:{user_id}"


def debounce_key(tenant_id: str, sid: str) -> str:
    return f"sess:debounce:{tenant_id}:{sid}"


async def mark_session_in_redis(
    tenant_id: str, refresh_token: str, ttl_seconds: int
) -> None:
    client = await get_client()
    if not client:
        return
    sid = _hash_sid(refresh_token)
    try:
        await client.setex(sess_key(tenant_id, sid), ttl_seconds, "1")
        metrics.session_marked(tenant_id)
    except Exception:
        metrics.error("mark_session", tenant_id)

    # we add to per-user set elsewhere when we also have user_id


async def add_session_to_user_set(
    tenant_id: str, user_id: int, refresh_token: str
) -> None:
    client = await get_client()
    if not client:
        return
    sid = _hash_sid(refresh_token)
    try:
        await client.sadd(user_sessions_key(tenant_id, user_id), sid)
    except Exception:
        metrics.error("add_session_to_user_set", tenant_id)


async def extend_session_ttl(
    tenant_id: str, refresh_token: str, extension_seconds: int
) -> bool:
    client = await get_client()
    if not client:
        return False
    sid = _hash_sid(refresh_token)
    k = sess_key(tenant_id, sid)
    try:
        exists = await client.exists(k)
        if not exists:
            metrics.miss("extend_session", tenant_id)
            return False
        await client.expire(k, extension_seconds)
        metrics.hit("extend_session", tenant_id)
        return True
    except Exception:
        metrics.error("extend_session", tenant_id)
        return False


async def extend_all_user_sessions_ttl(
    tenant_id: str, user_id: int, extension_seconds: int
) -> int:
    client = await get_client()
    if not client:
        return 0
    try:
        sids = await client.smembers(user_sessions_key(tenant_id, user_id))
        if not sids:
            metrics.miss("extend_all", tenant_id)
            return 0
        pipe = client.pipeline()
        for sid in sids:
            pipe.expire(sess_key(tenant_id, sid), extension_seconds)
        results: Iterable = await pipe.execute()
        # Count how many were successfully scheduled (non-zero results)
        count = 0
        for r in results:
            try:
                if int(r) == 1:
                    count += 1
            except Exception:
                pass
        metrics.bulk_extended(tenant_id, count)
        return count
    except Exception:
        metrics.error("extend_all", tenant_id)
        return 0


async def acquire_debounce(
    tenant_id: str, refresh_token: str, ttl_seconds: int
) -> bool:
    client = await get_client()
    if not client:
        return False
    sid = _hash_sid(refresh_token)
    k = debounce_key(tenant_id, sid)
    # Use SET NX EX
    try:
        res = await client.set(k, "1", ex=ttl_seconds, nx=True)
        acquired = bool(res)
        if acquired:
            metrics.debounce_acquired("debounce", tenant_id)
        else:
            metrics.debounce_skipped("debounce", tenant_id)
        return acquired
    except Exception:
        metrics.error("debounce", tenant_id)
        return False


async def remove_session(
    tenant_id: str, user_id: Optional[int], refresh_token: Optional[str]
) -> None:
    client = await get_client()
    if not client:
        return
    if refresh_token:
        sid = _hash_sid(refresh_token)
        await client.delete(sess_key(tenant_id, sid), debounce_key(tenant_id, sid))
        if user_id is not None:
            await client.srem(user_sessions_key(tenant_id, user_id), sid)


async def remove_all_user_sessions(tenant_id: str, user_id: int) -> None:
    client = await get_client()
    if not client:
        return
    key = user_sessions_key(tenant_id, user_id)
    sids = await client.smembers(key)
    if sids:
        pipe = client.pipeline()
        for sid in sids:
            pipe.delete(sess_key(tenant_id, sid), debounce_key(tenant_id, sid))
        pipe.delete(key)
        await pipe.execute()
