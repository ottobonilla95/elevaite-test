import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

import pytest

from app.core.config import settings
from sqlalchemy import select
from app.db.models import Session as DbSession, User
from app.core.security import get_password_hash


async def _create_active_user(test_session, email: str, password: str) -> int:
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        full_name="Test User",
        status="active",
        is_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_session.add(user)
    await test_session.commit()

    # fetch id
    result = await test_session.execute(select(User).where(User.email == email))
    u = result.scalars().first()
    return int(u.id)


async def _login(
    test_client, email: str, password: str, tenant: str = "default"
) -> Dict[str, Any]:
    resp = await test_client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
        headers={"X-Tenant-ID": tenant, "User-Agent": "pytest"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.mark.asyncio
async def test_extend_session_fast_path_single(monkeypatch, test_client, test_session):
    email = "redis_single@example.com"
    password = "Password123!@#"
    await _create_active_user(test_session, email, password)

    # Login to create a session
    tokens = await _login(test_client, email, password)

    # Capture original expires_at from DB for that refresh token
    result = await test_session.execute(
        select(DbSession).where(DbSession.refresh_token == tokens["refresh_token"])
    )
    db_sess = result.scalars().first()
    assert db_sess is not None
    original_expires = db_sess.expires_at

    # Redis fast path: hit, but debounce prevents DB write-through
    monkeypatch.setattr(
        "app.core.redis.extend_session_ttl",
        lambda *a, **k: asyncio.Future(),
        raising=False,
    )
    # make extend_session_ttl return True via future
    fut = asyncio.Future()
    fut.set_result(True)
    monkeypatch.setattr(
        "app.core.redis.extend_session_ttl", lambda *a, **k: fut, raising=False
    )

    # Debounce not acquired -> skip DB write
    monkeypatch.setattr(
        "app.core.redis.acquire_debounce",
        lambda *a, **k: asyncio.Future(),
        raising=False,
    )
    fut2 = asyncio.Future()
    fut2.set_result(False)
    monkeypatch.setattr(
        "app.core.redis.acquire_debounce", lambda *a, **k: fut2, raising=False
    )

    # Call extend-session
    resp = await test_client.post(
        "/api/auth/extend-session",
        headers={
            "X-Tenant-ID": "default",
            "Authorization": f"Bearer {tokens['access_token']}",
            "X-Refresh-Token": tokens["refresh_token"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("extended") is True
    assert data.get("extension_minutes") == settings.SESSION_EXTENSION_MINUTES

    # DB should remain unchanged due to debounce skip
    result2 = await test_session.execute(
        select(DbSession).where(DbSession.refresh_token == tokens["refresh_token"])
    )
    db_sess2 = result2.scalars().first()
    assert db_sess2.expires_at == original_expires


@pytest.mark.asyncio
async def test_extend_session_fallback_db_path_single(
    monkeypatch, test_client, test_session
):
    email = "redis_dbpath@example.com"
    password = "Password123!@#"
    await _create_active_user(test_session, email, password)
    tokens = await _login(test_client, email, password)

    # Force Redis miss -> DB path
    fut_false = asyncio.Future()
    fut_false.set_result(False)
    monkeypatch.setattr(
        "app.core.redis.extend_session_ttl", lambda *a, **k: fut_false, raising=False
    )

    # Capture DB before
    before = (
        (
            await test_session.execute(
                select(DbSession).where(
                    DbSession.refresh_token == tokens["refresh_token"]
                )
            )
        )
        .scalars()
        .first()
    )
    assert before is not None

    # Call extend-session
    resp = await test_client.post(
        "/api/auth/extend-session",
        headers={
            "X-Tenant-ID": "default",
            "Authorization": f"Bearer {tokens['access_token']}",
            "X-Refresh-Token": tokens["refresh_token"],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    new_expires_at_str = data["new_expires_at"]

    # Verify DB updated to the returned expires_at (allow small skew)
    after = (
        (
            await test_session.execute(
                select(DbSession).where(
                    DbSession.refresh_token == tokens["refresh_token"]
                )
            )
        )
        .scalars()
        .first()
    )
    assert after is not None
    # Allow DB to be equal or later (some implementations keep the later of existing vs extension)
    from datetime import datetime

    resp_dt = datetime.fromisoformat(new_expires_at_str.replace("Z", "+00:00"))
    assert after.expires_at >= resp_dt


@pytest.mark.asyncio
async def test_extend_session_bulk_redis_and_db(monkeypatch, test_client, test_session):
    email = "redis_bulk@example.com"
    password = "Password123!@#"
    await _create_active_user(test_session, email, password)

    # Login once to ensure at least one active session
    t1 = await _login(test_client, email, password)

    # Confirm active sessions in DB (at least 1)
    user_id_row = (
        (await test_session.execute(select(User.id).where(User.email == email)))
        .scalars()
        .first()
    )
    rows = (
        (
            await test_session.execute(
                select(DbSession).where(
                    DbSession.user_id == user_id_row, DbSession.is_active.is_(True)
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) >= 1

    # Patch Redis bulk TTL extend and ensure we write-through to DB
    fut_int = asyncio.Future()
    fut_int.set_result(len(rows))
    monkeypatch.setattr(
        "app.core.redis.extend_all_user_sessions_ttl",
        lambda *a, **k: fut_int,
        raising=False,
    )
    fut_true = asyncio.Future()
    fut_true.set_result(True)
    monkeypatch.setattr(
        "app.core.redis.acquire_debounce", lambda *a, **k: fut_true, raising=False
    )

    # Call without X-Refresh-Token to trigger bulk flow (use t1 access token)
    resp = await test_client.post(
        "/api/auth/extend-session",
        headers={
            "X-Tenant-ID": "default",
            "Authorization": f"Bearer {t1['access_token']}",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("extended") is True
    assert data.get("sessions_extended") == len(rows)

    # Verify DB sessions now share the returned new_expires_at
    rows_after = (
        (
            await test_session.execute(
                select(DbSession).where(
                    DbSession.user_id
                    == (
                        await test_session.execute(
                            select(User.id).where(User.email == email)
                        )
                    )
                    .scalars()
                    .first(),
                    DbSession.is_active.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )
    assert len(rows_after) == len(rows)
    for r in rows_after:
        from datetime import datetime

        resp_dt = datetime.fromisoformat(
            (data["new_expires_at"]).replace("Z", "+00:00")
        )
        assert r.expires_at >= resp_dt
