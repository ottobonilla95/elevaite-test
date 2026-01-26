"""Test fixtures for the authentication API."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict
from urllib.parse import urlsplit, urlunsplit

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from db_core import MultitenancySettings, TenantMiddleware, init_db
from db_core.middleware import set_current_tenant_id
from db_core.utils import async_create_tenant_schema, get_schema_name

from app.core.config import settings
from app.core.multitenancy import multitenancy_settings
from app.db.models import Base


def _derive_test_db_url(db_url: str) -> str:
    # Strip accidental quotes from env files
    db_url = db_url.strip().strip('"').strip("'")
    parts = urlsplit(db_url)
    if not parts.path or parts.path == "/":
        raise ValueError(f"Could not derive DB name from URL: {db_url}")
    dbname = parts.path.lstrip("/")
    if not dbname.endswith("_test"):
        dbname = f"{dbname}_test"
    return urlunsplit(
        (parts.scheme, parts.netloc, f"/{dbname}", parts.query, parts.fragment)
    )


# Get the database URL from settings or use a default for testing
try:
    base_db_url = settings.DATABASE_URI
except ValueError:
    # If DATABASE_URI is not set (e.g., in CI), use test default
    base_db_url = "postgresql+asyncpg://elevaite:elevaite@localhost:5433/auth"
TEST_DATABASE_URL = _derive_test_db_url(base_db_url)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case.

    This is a session-scoped fixture to match our test_engine fixture.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create a test engine for the database."""
    # Override the database URL for testing
    engine = create_async_engine(TEST_DATABASE_URL)

    # Create all tables in the public schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session")
async def test_db_setup(test_engine):
    """Set up test database with tenant schemas."""
    # Create tenant schemas
    test_tenants = ["default", "tenant1", "tenant2"]

    # Drop schemas first to ensure clean state
    async with test_engine.begin() as conn:
        for tenant_id in test_tenants:
            schema_name = get_schema_name(tenant_id, multitenancy_settings)
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))

    # Create schemas and tables
    for tenant_id in test_tenants:
        schema_name = get_schema_name(tenant_id, multitenancy_settings)
        await async_create_tenant_schema(test_engine, schema_name)

        # Create tables in each schema
        async with test_engine.begin() as conn:
            await conn.execute(text(f'SET search_path TO "{schema_name}"'))
            await conn.run_sync(Base.metadata.create_all)

    yield

    # Clean up schemas
    async with test_engine.begin() as conn:
        for tenant_id in test_tenants:
            schema_name = get_schema_name(tenant_id, multitenancy_settings)
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))


@pytest_asyncio.fixture
async def test_session_factory(test_engine, test_db_setup):
    """Create a test session factory for database operations."""
    return async_sessionmaker(bind=test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def test_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    """Create a test session for database operations (default tenant)."""
    session = test_session_factory()
    try:
        # Default all sessions to the 'default' tenant unless a test overrides it
        set_current_tenant_id("default")
        schema_name = get_schema_name("default", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        yield session
        # Roll back all changes after each test
        await session.rollback()
    finally:
        await session.close()


@pytest_asyncio.fixture
async def test_client(test_db_setup) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for the FastAPI app."""
    # Override the database URL for testing
    test_settings = MultitenancySettings(
        tenant_id_header="X-Tenant-ID",
        default_tenant_id="default",
        schema_prefix=multitenancy_settings.schema_prefix,
        db_url=TEST_DATABASE_URL,
    )

    # Initialize the database with test settings
    init_db(
        settings=test_settings,
        db_url=TEST_DATABASE_URL,
        create_schemas=False,  # Already created in test_db_setup
        base_model_class=Base,
        is_async=True,
    )

    # Create a test app with the test settings
    test_app = FastAPI()
    test_app.add_middleware(TenantMiddleware, settings=test_settings)

    # Add the auth router
    from app.routers import auth

    test_app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

    client = AsyncClient(
        transport=httpx.ASGITransport(app=test_app), base_url="http://test"
    )
    try:
        yield client
    finally:
        await client.aclose()


# Helper fixture to relax rate limiting during tests that don't validate rate limits
@pytest_asyncio.fixture
async def relax_auth_rate_limit():
    """Temporarily override auth router limiter key_func to avoid cross-test 429s.

    The auth router's Limiter instance is module-scoped and keeps in-memory state
    across tests. We switch key_func to use a unique key per request so non-rate-limit
    tests can run reliably without interference, then restore it after the test.
    """
    try:
        from app.routers import auth as auth_router
    except Exception:
        yield  # If import fails for any reason, don't block tests
        return

    limiter = getattr(auth_router, "limiter", None)
    if limiter is None:
        yield
        return

    original_key_func = getattr(limiter, "_key_func", None)

    def _test_key_func(request):
        # Allow explicit override via header for future flexibility, otherwise unique per request
        return request.headers.get("X-Rate-Test-Key", uuid.uuid4().hex)

    limiter._key_func = _test_key_func
    try:
        yield
    finally:
        limiter._key_func = original_key_func


# Ensure rate limiter storage is clean between tests to avoid cross-test interference
@pytest.fixture(autouse=True)
def _reset_auth_rate_limiter_between_tests():
    try:
        from app.routers import auth as auth_router

        limiter = getattr(auth_router, "limiter", None)
        if limiter is not None:
            limiter.reset()
    except Exception:
        pass
    yield
    try:
        from app.routers import auth as auth_router

        limiter = getattr(auth_router, "limiter", None)
        if limiter is not None:
            limiter.reset()
    except Exception:
        pass


@pytest_asyncio.fixture
async def test_user(test_session_factory) -> Dict:
    """Create a test user in the default tenant."""
    # Create a session for the default tenant
    session = test_session_factory()
    try:
        # Set tenant context and search path
        set_current_tenant_id("default")
        schema_name = get_schema_name("default", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}"'))

        # Create a test user directly with SQL
        from sqlalchemy import insert
        from app.db.models import User

        # Use a unique email for each test
        import uuid

        unique_id = str(uuid.uuid4())[:8]
        test_email = f"test_{unique_id}@example.com"
        test_password = "Password123!@#"  # Match password requirements

        # Create user directly with SQL to avoid greenlet issues
        from app.core.security import get_password_hash

        hashed_password = get_password_hash(test_password)

        # Insert the user directly
        stmt = (
            insert(User)
            .values(
                email=test_email,
                hashed_password=hashed_password,
                full_name="Test User",
                status="active",
                is_verified=True,
                is_password_temporary=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            .returning(User.id)
        )

        result = await session.execute(stmt)
        user_id = result.scalar_one()
        await session.commit()

        # Reset tenant context
        set_current_tenant_id(None)

        return {
            "id": user_id,
            "email": test_email,
            "password": test_password,
            "tenant": "default",
        }
    finally:
        await session.close()
