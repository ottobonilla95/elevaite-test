from __future__ import annotations

from typing import Optional, List, Dict, Any

from sqlmodel import Session

from ..db.service import DatabaseService


class ExecutionsService:
    """Read-only execution accessors used by the executions router.
    Routers call these instead of touching DatabaseService or ORM directly.
    """

    @staticmethod
    def get_execution(session: Session, execution_id: str) -> Optional[Dict[str, Any]]:
        db = DatabaseService()
        return db.get_execution(session, execution_id)

    @staticmethod
    def list_executions(
        session: Session,
        *,
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        db = DatabaseService()
        return db.list_executions(session, workflow_id=workflow_id, status=status, limit=limit, offset=offset)

    @staticmethod
    def execution_exists(session: Session, execution_id: str) -> bool:
        db = DatabaseService()
        return db.get_execution(session, execution_id) is not None

