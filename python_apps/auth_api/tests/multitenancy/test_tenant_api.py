"""Tests for tenant-aware API endpoints."""

import pytest

from db_core.utils import get_schema_name

from app.core.multitenancy import multitenancy_settings


@pytest.mark.asyncio
async def test_tenant_isolation(test_client, test_user):
    """Test that users are isolated between tenants."""
    # Register a user in tenant1
    tenant1_headers = {"X-Tenant-ID": "tenant1"}
    tenant1_user = {"email": "tenant1_api@example.com", "password": "Password123!@#", "full_name": "Tenant 1 User"}

    response = await test_client.post("/api/auth/register", json=tenant1_user, headers=tenant1_headers)
    assert response.status_code == 201
    assert response.json()["email"] == tenant1_user["email"]

    # Activate the user in tenant1
    # We need to do this directly in the database since we don't have an API endpoint for it
    from sqlalchemy import text
    from app.db.orm import get_async_session

    async for session in get_async_session():
        # Set the tenant context

        schema_name = get_schema_name("tenant1", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Activate the user
        await session.execute(
            text("UPDATE users SET status = 'active', is_verified = TRUE WHERE email = :email"),
            {"email": tenant1_user["email"]},
        )
        await session.commit()

    # Register a user in tenant2
    tenant2_headers = {"X-Tenant-ID": "tenant2"}
    tenant2_user = {"email": "tenant2_api@example.com", "password": "Password456!@#", "full_name": "Tenant 2 User"}

    response = await test_client.post("/api/auth/register", json=tenant2_user, headers=tenant2_headers)
    assert response.status_code == 201
    assert response.json()["email"] == tenant2_user["email"]

    # Activate the user in tenant2
    async for session in get_async_session():
        # Set the tenant context
        from db_core.utils import get_schema_name
        from app.core.multitenancy import multitenancy_settings

        schema_name = get_schema_name("tenant2", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Activate the user
        await session.execute(
            text("UPDATE users SET status = 'active', is_verified = TRUE WHERE email = :email"),
            {"email": tenant2_user["email"]},
        )
        await session.commit()

    # Login with tenant1 user
    login_data = {"email": "tenant1_api@example.com", "password": "Password123!@#"}

    response = await test_client.post("/api/auth/login", json=login_data, headers=tenant1_headers)
    assert response.status_code == 200
    tenant1_token = response.json()["access_token"]

    # Login with tenant2 user
    login_data = {"email": "tenant2_api@example.com", "password": "Password456!@#"}

    response = await test_client.post("/api/auth/login", json=login_data, headers=tenant2_headers)
    assert response.status_code == 200
    tenant2_token = response.json()["access_token"]

    # Verify that the tokens are different
    assert tenant1_token != tenant2_token


@pytest.mark.asyncio
async def test_cross_tenant_access(test_client, test_user):
    """Test that users cannot access resources from other tenants."""
    # Register a user in tenant1
    tenant1_headers = {"X-Tenant-ID": "tenant1"}
    tenant1_user = {"email": "cross_tenant_test@example.com", "password": "Password123!@#", "full_name": "Tenant 1 User"}

    response = await test_client.post("/api/auth/register", json=tenant1_user, headers=tenant1_headers)
    assert response.status_code == 201

    # Activate the user in tenant1
    # We need to do this directly in the database since we don't have an API endpoint for it
    from sqlalchemy import text
    from app.db.orm import get_async_session

    async for session in get_async_session():
        # Set the tenant context

        schema_name = get_schema_name("tenant1", multitenancy_settings)
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))

        # Activate the user
        await session.execute(
            text("UPDATE users SET status = 'active', is_verified = TRUE WHERE email = :email"),
            {"email": tenant1_user["email"]},
        )
        await session.commit()

    # Login with tenant1 user
    login_data = {"email": "cross_tenant_test@example.com", "password": "Password123!@#"}

    response = await test_client.post("/api/auth/login", json=login_data, headers=tenant1_headers)
    assert response.status_code == 200
    tenant1_token = response.json()["access_token"]

    # Try to use tenant1 token with tenant2 context
    tenant2_headers = {"X-Tenant-ID": "tenant2", "Authorization": f"Bearer {tenant1_token}"}

    # This should fail because the token is for tenant1 but we're using tenant2 context
    response = await test_client.get("/api/auth/me", headers=tenant2_headers)
    assert response.status_code == 401
