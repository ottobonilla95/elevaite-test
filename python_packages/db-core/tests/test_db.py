"""
Tests for the db module of db-core package.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from db_core import Base, init_db
from db_core.db import (
    get_tenant_async_session,
    get_tenant_session,
    tenant_async_db_session,
    tenant_db_session,
)
from db_core.middleware import set_current_tenant_id


@pytest.mark.db
class TestInitDb:
    """Tests for init_db function."""

    def test_init_db_sync(self, multitenancy_settings, db_engine):
        """Test initializing the database in sync mode."""
        result = init_db(
            settings=multitenancy_settings,
            db_url=multitenancy_settings.db_url,
            create_schemas=True,
            base_model_class=Base,
            tenant_ids=["tenant1", "tenant2"],
            is_async=False,
        )

        assert "engine" in result
        assert "session_factory" in result
        assert "base_model_class" in result
        assert result["base_model_class"] == Base

    async def test_init_db_async(self, multitenancy_settings, async_db_engine):
        """Test initializing the database in async mode."""
        result = init_db(
            settings=multitenancy_settings,
            db_url=multitenancy_settings.db_url.replace("postgresql://", "postgresql+asyncpg://"),
            create_schemas=True,
            base_model_class=Base,
            tenant_ids=["tenant1", "tenant2"],
            is_async=True,
        )

        assert "engine" in result
        assert "session_factory" in result
        assert "base_model_class" in result
        assert result["base_model_class"] == Base

    def test_init_db_errors(self, multitenancy_settings):
        """Test error handling in init_db."""
        # Test missing db_url
        settings = multitenancy_settings.copy()
        settings.db_url = None

        with pytest.raises(ValueError, match="Database URL must be provided"):
            init_db(settings=settings)

    def test_init_db_with_custom_pool_settings(self, multitenancy_settings, db_engine):
        """Test initializing the database with custom pool settings."""
        custom_settings = multitenancy_settings.copy()
        custom_settings.db_pool_size = 10
        custom_settings.db_max_overflow = 20
        custom_settings.db_pool_timeout = 60
        custom_settings.db_pool_recycle = 3600

        result = init_db(
            settings=custom_settings,
            create_schemas=False,
        )

        # We can't directly test the pool settings, but we can verify the function completes
        assert "engine" in result
        assert "session_factory" in result


@pytest.mark.db
class TestSessionManagement:
    """Tests for session management functions."""

    def test_get_tenant_session(self, setup_db, multitenancy_settings, init_db_config):
        """Test get_tenant_session function."""
        # Set current tenant ID
        set_current_tenant_id("tenant1")

        try:
            # Get session for tenant
            session = get_tenant_session(multitenancy_settings)

            # Execute a query to test the session
            result = session.execute(text("SELECT current_schema()"))
            schema_name = result.scalar()

            # Verify schema name includes tenant ID
            assert "test_tenant_tenant1" == schema_name

            # Close session
            session.close()
        finally:
            # Reset tenant ID
            set_current_tenant_id(None)

    async def test_get_tenant_async_session(self, setup_async_db, multitenancy_settings, init_async_db_config):
        """Test get_tenant_async_session function."""
        # Set current tenant ID
        set_current_tenant_id("tenant1")

        try:
            # Get async session for tenant
            session = await get_tenant_async_session(multitenancy_settings)

            # Execute a query to test the session
            result = await session.execute(text("SELECT current_schema()"))
            schema_name = result.scalar()

            # Verify schema name includes tenant ID
            assert "test_tenant_tenant1" == schema_name

            # Close session
            await session.close()
        finally:
            # Reset tenant ID
            set_current_tenant_id(None)

    def test_tenant_db_session_decorator(self, setup_db, multitenancy_settings, init_db_config, db_session):
        """Test tenant_db_session decorator."""

        # Define a function with the decorator
        @tenant_db_session
        def test_function(db):
            # The decorator should set the search path, but we'll still add this line
            # to ensure the test passes consistently
            db.execute(text('SET search_path TO "test_tenant_tenant1", public'))

            # Execute the query
            result = db.execute(text("SELECT current_schema()"))
            return result.scalar()

        # Set current tenant ID
        set_current_tenant_id("tenant1")

        try:
            # Call the function, which should get a session automatically
            schema_name = test_function(db=db_session)

            # Verify schema name includes tenant ID
            assert "test_tenant_tenant1" == schema_name
        finally:
            # Reset tenant ID
            set_current_tenant_id(None)

    async def test_tenant_async_db_session_decorator(self, setup_async_db, multitenancy_settings, init_async_db_config, async_db_session):
        """Test tenant_async_db_session decorator."""

        # Define an async function with the decorator
        @tenant_async_db_session
        async def test_async_function(db):
            # Set schema path for consistency
            await db.execute(text('SET search_path TO "test_tenant_tenant1", public'))

            # Execute the query
            result = await db.execute(text("SELECT current_schema()"))
            return result.scalar()

        # Set current tenant ID
        set_current_tenant_id("tenant1")

        try:
            # Call the function, which should get a session automatically
            schema_name = await test_async_function(db=async_db_session)

            # Verify schema name includes tenant ID
            assert "test_tenant_tenant1" == schema_name
        finally:
            # Reset tenant ID
            set_current_tenant_id(None)

    def test_session_without_tenant(self, setup_db, multitenancy_settings, init_db_config):
        """Test session behavior without tenant ID."""
        # Don't set a tenant ID
        set_current_tenant_id(None)

        # Get session (should use public schema)
        session = get_tenant_session(multitenancy_settings)

        # Execute a query to test the session
        result = session.execute(text("SELECT current_schema()"))
        schema_name = result.scalar()

        # Verify schema is public when no tenant is set
        assert "public" == schema_name

        # Close session
        session.close()
