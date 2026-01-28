"""
Multitenancy configuration for the Workflow Engine.

This module provides schema-based multitenancy configuration using db-core.
Each tenant gets their own PostgreSQL schema with isolated workflow data.
"""

import os
from typing import List

from db_core import MultitenancySettings

# Import database URL from central location to avoid duplication
from workflow_core_sdk.db.database import DATABASE_URL

# Default tenants to create on startup (comma-separated list from env, or defaults)
_default_tenants_str = os.getenv("WORKFLOW_DEFAULT_TENANTS", "default,iopex")
DEFAULT_TENANTS: List[str] = [
    t.strip() for t in _default_tenants_str.split(",") if t.strip()
]

# Multitenancy settings for workflow engine
multitenancy_settings = MultitenancySettings(
    tenant_id_header="X-Tenant-ID",
    default_tenant_id=os.getenv("DEFAULT_TENANT_ID", "default"),
    schema_prefix="workflow_",  # Workflow schema prefix (e.g., workflow_default, workflow_iopex)
    db_url=DATABASE_URL,
)
