"""
Multitenancy configuration for the Workflow Engine.

This module provides schema-based multitenancy configuration using db-core.
Each tenant gets their own PostgreSQL schema with isolated workflow data.
"""

import os
from typing import List

from db_core import MultitenancySettings

# Default tenants to create on startup
DEFAULT_TENANTS: List[str] = ["default", "iopex"]

# Multitenancy settings for workflow engine
multitenancy_settings = MultitenancySettings(
    tenant_id_header="X-Tenant-ID",
    default_tenant_id="default",
    schema_prefix="wf_",  # Workflow schema prefix (e.g., wf_default, wf_iopex)
    db_url=os.getenv(
        "SQLALCHEMY_DATABASE_URL",
        os.getenv(
            "WORKFLOW_ENGINE_DATABASE_URL",
            "postgresql://elevaite:elevaite@localhost:5433/agent_studio_sdk",
        ),
    ),
    # Pool settings - can be overridden via MultitenancySettings fields
    db_pool_size=int(os.getenv("WORKFLOW_ENGINE_DB_POOL_SIZE", os.getenv("DB_POOL_SIZE", "20"))),
    db_max_overflow=int(os.getenv("WORKFLOW_ENGINE_DB_MAX_OVERFLOW", os.getenv("DB_MAX_OVERFLOW", "50"))),
    db_pool_recycle=int(os.getenv("WORKFLOW_ENGINE_DB_POOL_RECYCLE", os.getenv("DB_POOL_RECYCLE", "1800"))),
    db_pool_timeout=int(os.getenv("WORKFLOW_ENGINE_DB_POOL_TIMEOUT", os.getenv("DB_POOL_TIMEOUT", "30"))),
)

