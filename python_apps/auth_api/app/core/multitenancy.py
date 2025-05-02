"""Multitenancy configuration for the authentication API."""

from db_core import MultitenancySettings

# Default tenants to create on startup
DEFAULT_TENANTS = ["default", "toshiba", "iopex"]

# Multitenancy settings
multitenancy_settings = MultitenancySettings(
    tenant_id_header="X-Tenant-ID",
    default_tenant_id="default",
    schema_prefix="auth_",  # Use a prefix for schema names to avoid conflicts
    db_url="",  # Will be set from config
)
