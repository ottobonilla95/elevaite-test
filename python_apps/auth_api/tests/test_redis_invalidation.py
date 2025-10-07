import types
import pytest

from types import SimpleNamespace

from app.services.auth_orm import invalidate_session, invalidate_all_sessions


class FakeResult:
    def __init__(self, value):
        self._value = value

    def scalars(self):
        return SimpleNamespace(first=lambda: self._value)


class FakeAsyncSession:
    def __init__(self, select_value=None):
        self.select_value = select_value
        self.executed = []
        self.commits = 0
        self.rollbacks = 0

    async def execute(self, *_args, **_kwargs):
        # Record calls; return select_value on any select, otherwise dummy
        self.executed.append(("execute", _args, _kwargs))
        return FakeResult(self.select_value)

    async def commit(self):
        self.commits += 1

    async def rollback(self):
        self.rollbacks += 1


@pytest.mark.asyncio
async def test_invalidate_session_calls_redis_remove_session(monkeypatch):
    # Arrange: tenant and redis hooks
    tenant_called = {}

    async def fake_remove_session(tenant_id, user_id, refresh_token):
        tenant_called["tenant_id"] = tenant_id
        tenant_called["user_id"] = user_id
        tenant_called["refresh_token"] = refresh_token

    monkeypatch.setattr(
        "app.core.redis.remove_session", fake_remove_session, raising=False
    )
    monkeypatch.setattr(
        "db_core.middleware.get_current_tenant_id", lambda: "tenant1", raising=False
    )

    # Fake Session returned by SELECT with user_id
    fake_user_session = SimpleNamespace(user_id=123)
    db_session = FakeAsyncSession(select_value=fake_user_session)

    # Act
    ok = await invalidate_session(db_session, "rtok-abc")  # type: ignore -- Fake Session CAN be assigned to real session for testing

    # Assert: redis called with expected params and DB updated (commit invoked)
    assert ok is True
    assert tenant_called == {
        "tenant_id": "tenant1",
        "user_id": 123,
        "refresh_token": "rtok-abc",
    }
    assert db_session.commits >= 1
    # Ensure an execute occurred (select + update likely)
    assert len(db_session.executed) >= 1


@pytest.mark.asyncio
async def test_invalidate_all_sessions_calls_redis_remove_all(monkeypatch):
    # Arrange
    called = {}

    async def fake_remove_all_user_sessions(tenant_id, user_id):
        called["tenant_id"] = tenant_id
        called["user_id"] = user_id

    monkeypatch.setattr(
        "app.core.redis.remove_all_user_sessions",
        fake_remove_all_user_sessions,
        raising=False,
    )
    monkeypatch.setattr(
        "db_core.middleware.get_current_tenant_id", lambda: "tenantX", raising=False
    )

    db_session = FakeAsyncSession()

    # Act
    ok = await invalidate_all_sessions(db_session, 999)  # type: ignore -- Fake Session CAN be assigned to real session for testing

    # Assert
    assert ok is True
    assert called == {"tenant_id": "tenantX", "user_id": 999}
    assert db_session.commits >= 1
    assert len(db_session.executed) >= 1
