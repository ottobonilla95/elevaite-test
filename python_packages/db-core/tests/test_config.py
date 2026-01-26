"""
Tests for the config module of db-core package.
"""

import pytest
from pydantic import ValidationError

from db_core import MultitenancySettings


class TestMultitenancySettings:
    """Tests for MultitenancySettings class."""

    def test_default_settings(self):
        """Test default settings."""
        settings = MultitenancySettings()
        
        # Check default values
        assert settings.tenant_id_header == "X-Tenant-ID"
        assert settings.default_tenant_id is None
        assert settings.admin_tenant_id is None
        assert settings.auto_create_tenant_schema is True
        assert settings.case_sensitive_tenant_id is False
        assert settings.tenant_id_validation_pattern == r"^[a-zA-Z0-9_-]+$"
        assert settings.db_url is None
        assert settings.schema_prefix == "tenant_"
        assert settings.db_pool_size == 5
        assert settings.db_max_overflow == 10
        assert settings.db_pool_timeout == 30
        assert settings.db_pool_recycle == 1800
        assert settings.use_public_schema_for_admin is True
        assert settings.tenant_specific_settings == {}

    def test_custom_settings(self):
        """Test custom settings values."""
        custom_settings = {
            "tenant_id_header": "X-Custom-Tenant",
            "default_tenant_id": "default",
            "admin_tenant_id": "admin",
            "auto_create_tenant_schema": False,
            "case_sensitive_tenant_id": True,
            "tenant_id_validation_pattern": r"^[a-z]+$",
            "db_url": "postgresql://user:pass@localhost/db",
            "schema_prefix": "custom_",
            "db_pool_size": 10,
            "db_max_overflow": 20,
            "db_pool_timeout": 60,
            "db_pool_recycle": 3600,
            "use_public_schema_for_admin": False,
            "tenant_specific_settings": {
                "tenant1": {
                    "db_pool_size": 15,
                },
            },
        }
        
        settings = MultitenancySettings(**custom_settings)
        
        # Check custom values
        for key, value in custom_settings.items():
            assert getattr(settings, key) == value

    def test_validation(self):
        """Test settings validation."""
        # Test empty tenant ID header
        with pytest.raises(ValidationError):
            MultitenancySettings(tenant_id_header="")
        
        # Other validations could be added here

    def test_copy(self):
        """Test settings copy method."""
        settings = MultitenancySettings(tenant_id_header="X-Tenant")
        
        # Copy settings
        settings_copy = settings.copy()
        
        # Verify copy is independent
        assert settings_copy.tenant_id_header == "X-Tenant"
        
        # Modify copy
        settings_copy.tenant_id_header = "X-Modified"
        
        # Verify original is unchanged
        assert settings.tenant_id_header == "X-Tenant"
        assert settings_copy.tenant_id_header == "X-Modified"
        
    def test_schema_strategy(self):
        """Test schema strategy settings."""
        # Schema strategy is the only supported strategy
        MultitenancySettings()
        
        # Verify schema prefix can be customized
        custom_settings = MultitenancySettings(schema_prefix="custom_")
        assert custom_settings.schema_prefix == "custom_"