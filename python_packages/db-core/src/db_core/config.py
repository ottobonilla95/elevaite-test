"""
Configuration options for schema-based multitenancy.
"""

from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, field_validator, ConfigDict


class MultitenancySettings(BaseModel):
    """Configuration settings for schema-based multitenancy."""

    tenant_id_header: str = "X-Tenant-ID"
    default_tenant_id: Optional[str] = None
    admin_tenant_id: Optional[str] = None
    auto_create_tenant_schema: bool = True
    case_sensitive_tenant_id: bool = False
    tenant_id_validation_pattern: str = r"^[a-zA-Z0-9_-]+$"
    db_url: Optional[str] = None
    schema_prefix: str = "tenant_"

    # Additional database connection parameters
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # Schema/tenant management
    use_public_schema_for_admin: bool = True

    # Custom tenant-specific database settings
    tenant_specific_settings: Dict[str, Dict[str, Any]] = {}

    @field_validator("tenant_id_header")
    @classmethod
    def validate_header_name(cls, v):
        if not v:
            raise ValueError("Tenant ID header name cannot be empty")
        return v

    # Use Pydantic v2 style config
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")
