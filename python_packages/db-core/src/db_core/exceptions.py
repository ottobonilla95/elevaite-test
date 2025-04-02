"""
Exceptions for the multitenancy package.
"""


class TenantError(Exception):
    """Base exception for all tenant-related errors."""

    pass


class TenantNotFoundError(TenantError):
    """Exception raised when a tenant cannot be found."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        super().__init__(f"Tenant not found: {tenant_id}")


class InvalidTenantIdError(TenantError):
    """Exception raised when a tenant ID is invalid."""

    def __init__(self, tenant_id: str, pattern: str):
        self.tenant_id = tenant_id
        self.pattern = pattern
        super().__init__(f"Invalid tenant ID: {tenant_id}. Must match pattern: {pattern}")


class TenantSchemaError(TenantError):
    """Exception raised when there is an error with a tenant schema."""

    def __init__(self, tenant_id: str, message: str):
        self.tenant_id = tenant_id
        super().__init__(f"Error with tenant schema for {tenant_id}: {message}")


class MissingTenantIdError(TenantError):
    """Exception raised when no tenant ID is provided but one is required."""

    def __init__(self):
        super().__init__("No tenant ID provided")
