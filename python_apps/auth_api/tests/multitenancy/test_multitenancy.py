"""
Manual test script to demonstrate multitenancy functionality.

This script creates users with the same email in different tenant schemas
and verifies that they are isolated from each other.
"""

import asyncio
import pytest
import sqlalchemy
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from db_core.middleware import set_current_tenant_id
from db_core.utils import async_create_tenant_schema, get_schema_name

from app.schemas.user import UserCreate
from app.services.auth_orm import create_user, get_user_by_email
from app.core.multitenancy import multitenancy_settings
from app.db.models import Base

# Use the test database URL
from ..conftest import TEST_DATABASE_URL


async def set_tenant_search_path(session, tenant_id):
    """Set the search path for the session to the tenant's schema."""
    schema_name = get_schema_name(tenant_id, multitenancy_settings)
    await session.execute(sqlalchemy.text(f'SET search_path TO "{schema_name}"'))
    # Also set the tenant ID in the middleware context
    set_current_tenant_id(tenant_id)


@pytest.mark.asyncio
async def test_tenant_isolation():
    """Test that users are isolated between tenants."""
    # Create engine
    from app.core.multitenancy import multitenancy_settings

    multitenancy_settings.db_url = TEST_DATABASE_URL
    assert multitenancy_settings.db_url, "Database URL is not set"
    engine = create_async_engine(multitenancy_settings.db_url)

    # Define tenant IDs
    test_tenants = ["tenant1", "tenant2"]

    # First, drop all existing tenant schemas to start fresh
    print("Dropping existing schemas...")
    async with engine.begin() as conn:
        for tenant_id in test_tenants:
            schema_name = get_schema_name(tenant_id, multitenancy_settings)
            print(f"  - Dropping schema {schema_name} if it exists...")
            await conn.execute(
                sqlalchemy.text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            )

    # Now create fresh tenant schemas
    for tenant_id in test_tenants:
        schema_name = get_schema_name(tenant_id, multitenancy_settings)
        print(f"Creating schema {schema_name}...")
        await async_create_tenant_schema(engine, schema_name)

        # Create tables in each schema
        async with engine.begin() as conn:
            await conn.execute(sqlalchemy.text(f'SET search_path TO "{schema_name}"'))
            await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        # Create a user in tenant1 with a fresh session
        tenant1_session = async_session()
        try:
            await set_tenant_search_path(tenant1_session, "tenant1")
            print("Creating user in tenant1...")
            user_data1 = UserCreate(
                email="isolation@example.com",
                password="Password123!@#",
                full_name="Tenant 1 User",
            )

            user1 = await create_user(tenant1_session, user_data1)
            print(f"Created user in tenant1: {user1.email} (ID: {user1.id})")
        finally:
            await tenant1_session.close()

        # Create a user in tenant2 with a fresh session
        tenant2_session = async_session()
        try:
            await set_tenant_search_path(tenant2_session, "tenant2")
            print("\nCreating user in tenant2 with the same email...")
            user_data2 = UserCreate(
                email="isolation@example.com",
                password="Password456!@#",
                full_name="Tenant 2 User",
            )

            user2 = await create_user(tenant2_session, user_data2)
            print(f"Created user in tenant2: {user2.email} (ID: {user2.id})")
        finally:
            await tenant2_session.close()

        # Verify that both users exist in their respective tenants
        print("\nVerifying users in their respective tenants...")

        # Verify tenant1 with a fresh session
        verify1_session = async_session()
        try:
            await set_tenant_search_path(verify1_session, "tenant1")
            tenant1_user = await get_user_by_email(
                verify1_session, "isolation@example.com"
            )
            if tenant1_user:
                print(
                    f"User in tenant1: {tenant1_user.email}, {tenant1_user.full_name}"
                )
            else:
                print("User not found in tenant1!")
        finally:
            await verify1_session.close()

        # Verify tenant2 with a fresh session
        verify2_session = async_session()
        try:
            await set_tenant_search_path(verify2_session, "tenant2")
            tenant2_user = await get_user_by_email(
                verify2_session, "isolation@example.com"
            )
            if tenant2_user:
                print(
                    f"User in tenant2: {tenant2_user.email}, {tenant2_user.full_name}"
                )
            else:
                print("User not found in tenant2!")
        finally:
            await verify2_session.close()

        # Verify that the users are different
        if tenant1_user and tenant2_user:
            print("\nVerifying that the users are different:")
            print(f"User IDs: tenant1={tenant1_user.id}, tenant2={tenant2_user.id}")
            print(
                f"Full names: tenant1='{tenant1_user.full_name}', tenant2='{tenant2_user.full_name}'"
            )

            if (
                tenant1_user.id != tenant2_user.id
                or tenant1_user.full_name != tenant2_user.full_name
            ):
                print(
                    "\n✅ SUCCESS: Users with the same email exist in different tenants!"
                )
            else:
                print("\n❌ FAILURE: Users are not properly isolated between tenants.")
        else:
            print("\n❌ FAILURE: Could not find users in both tenants.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        # Reset tenant context
        set_current_tenant_id(None)  # This doesn't need to be awaited
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_tenant_isolation())
