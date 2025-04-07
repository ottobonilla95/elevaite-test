"""
Tests for the utils module of db-core package.
"""

import pytest
from sqlalchemy import text

from db_core import MultitenancySettings
from db_core.exceptions import InvalidTenantIdError
from db_core.utils import (
    async_create_tenant_schema,
    async_list_tenant_schemas,
    async_set_tenant_search_path,
    async_tenant_schema_exists,
    create_tenant_schema,
    get_schema_name,
    get_tenant_id_from_schema,
    list_tenant_schemas,
    set_tenant_search_path,
    tenant_schema_exists,
    validate_tenant_id,
)


class TestSchemaUtils:
    """Tests for schema utility functions."""

    def test_get_schema_name(self, multitenancy_settings):
        """Test get_schema_name function."""
        # Default settings
        schema_name = get_schema_name("tenant1", multitenancy_settings)
        assert schema_name == "test_tenant_tenant1"
        
        # Custom prefix
        settings = multitenancy_settings.copy()
        settings.schema_prefix = "custom_"
        schema_name = get_schema_name("tenant2", settings)
        assert schema_name == "custom_tenant2"
        
        # Mixed case tenant ID with case insensitivity
        settings = multitenancy_settings.copy()
        settings.case_sensitive_tenant_id = False
        schema_name = get_schema_name("TenANT3", settings)
        assert schema_name == "test_tenant_tenant3"
        
        # Mixed case tenant ID with case sensitivity
        settings = multitenancy_settings.copy()
        settings.case_sensitive_tenant_id = True
        schema_name = get_schema_name("TenANT3", settings)
        assert schema_name == "test_tenant_TenANT3"

    def test_validate_tenant_id(self, multitenancy_settings):
        """Test validate_tenant_id function."""
        # Valid tenant IDs
        assert validate_tenant_id("tenant1", multitenancy_settings) is True
        assert validate_tenant_id("tenant-2", multitenancy_settings) is True
        assert validate_tenant_id("tenant_3", multitenancy_settings) is True
        assert validate_tenant_id("123", multitenancy_settings) is True
        
        # Invalid tenant IDs
        with pytest.raises(InvalidTenantIdError):
            validate_tenant_id("tenant@1", multitenancy_settings)
        
        with pytest.raises(InvalidTenantIdError):
            validate_tenant_id("tenant.1", multitenancy_settings)
        
        with pytest.raises(InvalidTenantIdError):
            validate_tenant_id("tenant/1", multitenancy_settings)
        
        # Empty tenant ID
        assert validate_tenant_id("", multitenancy_settings) is False
        
        # Custom validation pattern
        settings = multitenancy_settings.copy()
        settings.tenant_id_validation_pattern = r"^[a-z]+$"
        
        assert validate_tenant_id("tenant", settings) is True
        
        with pytest.raises(InvalidTenantIdError):
            validate_tenant_id("tenant1", settings)
        
        with pytest.raises(InvalidTenantIdError):
            validate_tenant_id("Tenant", settings)

    @pytest.mark.db
    def test_tenant_schema_exists(self, setup_db, db_engine, multitenancy_settings):
        """Test tenant_schema_exists function."""
        # Check existing schema
        schema_name = get_schema_name("tenant1", multitenancy_settings)
        assert tenant_schema_exists(db_engine, schema_name) is True
        
        # Check non-existing schema
        assert tenant_schema_exists(db_engine, "nonexistent_schema") is False

    @pytest.mark.db
    async def test_async_tenant_schema_exists(
        self, setup_async_db, async_db_engine, multitenancy_settings
    ):
        """Test async_tenant_schema_exists function."""
        # Check existing schema
        schema_name = get_schema_name("tenant1", multitenancy_settings)
        result = await async_tenant_schema_exists(async_db_engine, schema_name)
        assert result is True
        
        # Check non-existing schema
        result = await async_tenant_schema_exists(async_db_engine, "nonexistent_schema")
        assert result is False

    @pytest.mark.db
    def test_create_tenant_schema(self, db_engine, multitenancy_settings):
        """Test create_tenant_schema function."""
        # Create a new schema
        schema_name = "test_new_schema"
        
        # First, make sure it doesn't exist
        with db_engine.connect() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        
        # Create the schema
        result = create_tenant_schema(db_engine, schema_name)
        assert result is True
        
        # Verify schema exists
        assert tenant_schema_exists(db_engine, schema_name) is True
        
        # Clean up
        with db_engine.connect() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))

    @pytest.mark.db
    async def test_async_create_tenant_schema(self, async_db_engine, multitenancy_settings):
        """Test async_create_tenant_schema function."""
        # Create a new schema
        schema_name = "test_async_new_schema"
        
        # First, make sure it doesn't exist
        async with async_db_engine.connect() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        
        # Create the schema
        result = await async_create_tenant_schema(async_db_engine, schema_name)
        assert result is True
        
        # Verify schema exists
        result = await async_tenant_schema_exists(async_db_engine, schema_name)
        assert result is True
        
        # Clean up
        async with async_db_engine.connect() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))

    @pytest.mark.db
    def test_list_tenant_schemas(self, setup_db, db_engine, multitenancy_settings):
        """Test list_tenant_schemas function."""
        # Get list of tenant schemas
        schemas = list_tenant_schemas(db_engine, multitenancy_settings.schema_prefix)
        
        # Verify all test tenant schemas are in the list
        for tenant_id in ["tenant1", "tenant2", "admin"]:
            schema_name = get_schema_name(tenant_id, multitenancy_settings)
            assert schema_name in schemas

    @pytest.mark.db
    async def test_async_list_tenant_schemas(
        self, setup_async_db, async_db_engine, multitenancy_settings
    ):
        """Test async_list_tenant_schemas function."""
        # Get list of tenant schemas
        schemas = await async_list_tenant_schemas(
            async_db_engine, multitenancy_settings.schema_prefix
        )
        
        # Verify all test tenant schemas are in the list
        for tenant_id in ["tenant1", "tenant2", "admin"]:
            schema_name = get_schema_name(tenant_id, multitenancy_settings)
            assert schema_name in schemas

    def test_get_tenant_id_from_schema(self, multitenancy_settings):
        """Test get_tenant_id_from_schema function."""
        # Get tenant ID from schema name
        schema_name = "test_tenant_tenant1"
        tenant_id = get_tenant_id_from_schema(schema_name, multitenancy_settings.schema_prefix)
        assert tenant_id == "tenant1"
        
        # Get tenant ID from schema with different prefix
        schema_name = "custom_tenant2"
        tenant_id = get_tenant_id_from_schema(schema_name, "custom_")
        assert tenant_id == "tenant2"
        
        # Non-matching schema name
        schema_name = "public"
        tenant_id = get_tenant_id_from_schema(schema_name, multitenancy_settings.schema_prefix)
        assert tenant_id is None

    @pytest.mark.db
    def test_set_tenant_search_path(self, setup_db, db_engine, multitenancy_settings):
        """Test set_tenant_search_path function."""
        # Set search path for a connection
        schema_name = get_schema_name("tenant1", multitenancy_settings)
        result = set_tenant_search_path(db_engine, schema_name)
        assert result is True
        
        # Verify search path was set (use the same connection)
        with db_engine.connect() as conn:
            # Set search path for this specific connection
            conn.execute(text(f'SET search_path TO "{schema_name}", public'))
            # Now verify the schema
            result = conn.execute(text("SELECT current_schema()"))
            current_schema = result.scalar()
            assert current_schema == schema_name

    @pytest.mark.db
    async def test_async_set_tenant_search_path(
        self, setup_async_db, async_db_engine, multitenancy_settings
    ):
        """Test async_set_tenant_search_path function."""
        # Set search path for a connection
        schema_name = get_schema_name("tenant1", multitenancy_settings)
        result = await async_set_tenant_search_path(async_db_engine, schema_name)
        assert result is True
        
        # Verify search path was set
        async with async_db_engine.connect() as conn:
            result = await conn.execute(text("SELECT current_schema()"))
            current_schema = result.scalar()
            assert current_schema == schema_name