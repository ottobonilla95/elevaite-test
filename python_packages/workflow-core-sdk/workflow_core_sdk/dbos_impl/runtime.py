"""
Runtime helpers for DBOS adapter without import-time cycles.

Provides get_dbos_adapter() with lazy import of the Adapter class to avoid
circular imports between steps/workflows and the adapter.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from dbos import DBOS, DBOSConfig

DBOS_AVAILABLE = True
logger = logging.getLogger(__name__)

_dbos_adapter: Optional["DBOSWorkflowAdapter"] = None


async def get_dbos_adapter():
    """Get or create the global DBOS adapter instance lazily.

    Note: We import DBOSWorkflowAdapter inside the function to avoid cycles.
    """
    global _dbos_adapter
    if _dbos_adapter is None:
        # Lazy import to break cycles
        from .adapter import DBOSWorkflowAdapter  # local import

        _dbos_adapter = DBOSWorkflowAdapter()
        await _dbos_adapter.initialize()

        # Ensure DBOS is configured (idempotent)
        if DBOS_AVAILABLE:
            try:
                from workflow_engine_poc.db.database import DATABASE_URL as _ENGINE_DB_URL

                _dbos_db_url = os.getenv("DBOS_DATABASE_URL") or os.getenv("DATABASE_URL") or _ENGINE_DB_URL
                _app_name = os.getenv("DBOS_APPLICATION_NAME") or os.getenv("DBOS_APP_NAME") or "workflow-engine-poc"
                try:
                    DBOS(config=DBOSConfig(database_url=_dbos_db_url, name=_app_name))  # type: ignore[call-arg]
                except Exception:
                    # likely already configured
                    pass
            except Exception as e:
                logger.warning(f"DBOS init failed: {e}")

    return _dbos_adapter

