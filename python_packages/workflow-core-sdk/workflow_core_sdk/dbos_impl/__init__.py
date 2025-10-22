"""
Lightweight DBOS module scaffolding for the Workflow Engine PoC.

This module is intended to hold DBOS-specific pieces split out of
`workflow_engine_poc.dbos_adapter` to improve readability.

Planned layout:
- messaging.py  -> helpers/utilities for DBOS topic naming and messaging
- steps.py      -> @DBOS.step entrypoints
- workflows.py  -> @DBOS.workflow entrypoints

Usage plan (non-breaking):
- First, create these files (done).
- Next, move functions incrementally from dbos_adapter.py into here.
- Keep dbos_adapter.py exporting get_dbos_adapter and importing these
  modules so decorators bind on import.

Note: We intentionally avoid naming collisions with the external `dbos` package
by using the name `dbos_impl` for this internal module.
"""

from __future__ import annotations
import logging
from typing import Optional
from dbos import DBOS, DBOSConfig
import os

# Runtime accessor is separate to avoid circular imports
from .runtime import get_dbos_adapter  # noqa: F401

DBOS_AVAILABLE = True

__all__ = [
    # Re-exports may be added after migration
]

logger = logging.getLogger(__name__)
