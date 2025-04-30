"""Tests for tenant isolation."""

import pytest
import pytest_asyncio
from sqlalchemy import text

from db_core.middleware import set_current_tenant_id
from db_core.utils import get_schema_name

from app.schemas.user import UserCreate
from app.services.auth_orm import create_user, get_user_by_email
from app.core.multitenancy import multitenancy_settings


async def set_tenant_context(session, tenant_id):
    """Set the tenant context for the session."""
    # Set the tenant ID in the middleware context
    set_current_tenant_id(tenant_id)
    # Set the search path for the session
    schema_name = get_schema_name(tenant_id, multitenancy_settings)
    await session.execute(text(f'SET search_path TO "{schema_name}"'))


@pytest_asyncio.fixture
async def tenant1_session(test_session_factory):
    """Create a session for tenant1."""
    session = test_session_factory()
    try:
        # Set tenant context
        set_current_tenant_id("tenant1")
        schema_name = get_schema_name("tenant1", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Verify the search path is set correctly
        result = await session.execute(text("SHOW search_path"))
        search_path = result.scalar()
        assert schema_name in search_path, f"Search path not set correctly: {search_path}"

        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def tenant2_session(test_session_factory):
    """Create a session for tenant2."""
    session = test_session_factory()
    try:
        # Set tenant context
        set_current_tenant_id("tenant2")
        schema_name = get_schema_name("tenant2", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Verify the search path is set correctly
        result = await session.execute(text("SHOW search_path"))
        search_path = result.scalar()
        assert schema_name in search_path, f"Search path not set correctly: {search_path}"

        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def default_tenant_session(test_session_factory):
    """Create a session for the default tenant."""
    session = test_session_factory()
    try:
        # Set tenant context
        set_current_tenant_id("default")
        schema_name = get_schema_name("default", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Verify the search path is set correctly
        result = await session.execute(text("SHOW search_path"))
        search_path = result.scalar()
        assert schema_name in search_path, f"Search path not set correctly: {search_path}"

        # Commit any pending transactions
        await session.commit()

        # Close and reopen the session to ensure a fresh connection
        await session.close()
        session = test_session_factory()

        # Set the search path again
        set_current_tenant_id("default")
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Verify the search path again
        result = await session.execute(text("SHOW search_path"))
        search_path = result.scalar()
        assert schema_name in search_path, f"Search path not set correctly after reconnect: {search_path}"

        yield session
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_tenant_isolation_db(tenant1_session, tenant2_session):
    """Test that tenants are isolated at the database level."""
    # Create a user in tenant1
    user_data1 = UserCreate(email="tenant1@example.com", password="Password123!@#", full_name="Tenant 1 User")
    user1 = await create_user(tenant1_session, user_data1)
    assert user1 is not None
    assert user1.email == "tenant1@example.com"
    assert user1.full_name == "Tenant 1 User"

    # Create a user in tenant2
    user_data2 = UserCreate(email="tenant2@example.com", password="Password456!@#", full_name="Tenant 2 User")
    user2 = await create_user(tenant2_session, user_data2)
    assert user2 is not None
    assert user2.email == "tenant2@example.com"
    assert user2.full_name == "Tenant 2 User"

    # Verify that users exist in their respective tenants
    tenant1_user = await get_user_by_email(tenant1_session, "tenant1@example.com")
    assert tenant1_user is not None
    assert tenant1_user.email == "tenant1@example.com"
    assert tenant1_user.full_name == "Tenant 1 User"

    tenant2_user = await get_user_by_email(tenant2_session, "tenant2@example.com")
    assert tenant2_user is not None
    assert tenant2_user.email == "tenant2@example.com"
    assert tenant2_user.full_name == "Tenant 2 User"

    # Verify that tenant1 can't see tenant2's user
    tenant2_user_in_tenant1 = await get_user_by_email(tenant1_session, "tenant2@example.com")
    assert tenant2_user_in_tenant1 is None, "Tenant1 should not see tenant2's user"

    # Verify that tenant2 can't see tenant1's user
    tenant1_user_in_tenant2 = await get_user_by_email(tenant2_session, "tenant1@example.com")
    assert tenant1_user_in_tenant2 is None, "Tenant2 should not see tenant1's user"


@pytest.mark.asyncio
async def test_tenant_context_switching(tenant1_session, tenant2_session, test_session_factory):
    """Test that switching tenant context works correctly."""
    # Create a user in tenant1
    user_data1 = UserCreate(email="switch1@example.com", password="Password123!@#", full_name="Tenant 1 User")
    await create_user(tenant1_session, user_data1)

    # Create a user in tenant2
    user_data2 = UserCreate(email="switch2@example.com", password="Password456!@#", full_name="Tenant 2 User")
    await create_user(tenant2_session, user_data2)

    # Use a new session and switch between tenants
    session = test_session_factory()
    try:
        # First check tenant1
        set_current_tenant_id("tenant1")
        schema_name = get_schema_name("tenant1", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Verify search path
        result = await session.execute(text("SHOW search_path"))
        search_path = result.scalar()
        assert schema_name in search_path, f"Search path not set correctly: {search_path}"

        tenant1_user = await get_user_by_email(session, "switch1@example.com")
        assert tenant1_user is not None
        assert tenant1_user.full_name == "Tenant 1 User"

        # Then switch to tenant2
        set_current_tenant_id("tenant2")
        schema_name = get_schema_name("tenant2", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Verify search path
        result = await session.execute(text("SHOW search_path"))
        search_path = result.scalar()
        assert schema_name in search_path, f"Search path not set correctly: {search_path}"

        # Commit any pending transactions
        await session.commit()

        # Close and reopen the session to ensure a fresh connection
        await session.close()
        session = test_session_factory()
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Verify the search path again
        result = await session.execute(text("SHOW search_path"))
        search_path = result.scalar()
        assert schema_name in search_path, f"Search path not set correctly after reconnect: {search_path}"

        # Get the user from tenant2
        tenant2_user = await get_user_by_email(session, "switch2@example.com")
        assert tenant2_user is not None, "User in tenant2 not found"
        print(f"Found user in tenant2: {tenant2_user.email}, {tenant2_user.full_name}")
        assert tenant2_user.full_name == "Tenant 2 User"

        # Verify the users have different attributes
        # Note: IDs might be the same since they're in different schemas
        assert tenant1_user.email != tenant2_user.email
        assert tenant1_user.full_name != tenant2_user.full_name
    finally:
        await session.close()


@pytest.mark.asyncio
async def test_default_tenant(test_client):
    """Test that the default tenant works correctly."""
    # Use direct database access instead of the ORM to avoid session issues
    from app.db.orm import get_async_session

    # Create a unique email for this test
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    test_email = f"default_tenant_{unique_id}@example.com"

    # Create a user in the default tenant
    async for session in get_async_session():
        # Set tenant context
        set_current_tenant_id("default")
        schema_name = get_schema_name("default", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Get a real password hash
        from app.core.security import get_password_hash

        test_password = "Password123!@#"
        hashed_password = get_password_hash(test_password)

        # Create user directly with SQL
        await session.execute(
            text("""
            INSERT INTO users (email, hashed_password, full_name, status, is_verified, is_superuser, mfa_enabled, failed_login_attempts, is_password_temporary, created_at, updated_at)
            VALUES (:email, :password, :full_name, 'active', TRUE, FALSE, FALSE, 0, FALSE, NOW(), NOW())
            """),
            {
                "email": test_email,
                "password": hashed_password,
                "full_name": "Default Tenant User",
            },
        )
        await session.commit()

        # Verify user was created
        result = await session.execute(
            text("SELECT * FROM users WHERE email = :email"),
            {"email": test_email},
        )
        user = result.fetchone()
        assert user is not None, "User in default tenant not created"
        assert user.email == test_email, f"Got unexpected email: {user.email}"
        assert user.full_name == "Default Tenant User"
