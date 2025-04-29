"""Test fixtures for the authentication API."""

import asyncio
from typing import AsyncGenerator, Dict

import pytest
import pytest_asyncio
from fastapi import FastAPI
import httpx
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from db_core import MultitenancySettings, TenantMiddleware, init_db
from db_core.middleware import set_current_tenant_id
from db_core.utils import async_create_tenant_schema, get_schema_name

from app.core.config import settings
from app.core.multitenancy import multitenancy_settings
from app.db.models import Base
# Don't import the main app directly to avoid rate limiter issues
# from app.main import app as main_app


# Test database URL - use a separate database for testing
TEST_DATABASE_URL = settings.DATABASE_URI.replace("/auth", "/auth_test")


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
    """Create a test session for database operations."""
    session = test_session_factory()
    try:
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

    client = AsyncClient(transport=httpx.ASGITransport(app=test_app), base_url="http://test")
    try:
        yield client
    finally:
        await client.aclose()


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

        # Create a test user
        from app.services.auth_orm import create_user
        from app.schemas.user import UserCreate

        # Use a unique email for each test
        import uuid

        unique_id = str(uuid.uuid4())[:8]

        user_data = UserCreate(
            email=f"test_{unique_id}@example.com",
            password="Password123!@#",  # Match password requirements
            full_name="Test User",
        )

        user = await create_user(session, user_data)

        # Activate the user
        user.is_verified = True
        user.status = "active"
        await session.commit()

        # Reset tenant context
        set_current_tenant_id(None)

        return {"id": user.id, "email": user.email, "password": "Password123!@#", "tenant": "default"}
    finally:
        await session.close()
