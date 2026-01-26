from __future__ import annotations

from typing import Optional, List, Dict, Any

from sqlmodel import Session

from ..db.service import DatabaseService
from ..db.models.executions import ExecutionStatus as DBExecutionStatus


class ExecutionsService:
    """Execution accessors used by the executions router.
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
        return db.list_executions(
            session, workflow_id=workflow_id, status=status, limit=limit, offset=offset
        )

    @staticmethod
    def execution_exists(session: Session, execution_id: str) -> bool:
        db = DatabaseService()
        return db.get_execution(session, execution_id) is not None

    @staticmethod
    def create_execution(session: Session, execution_data: Dict[str, Any]) -> str:
        """Create a new execution and return its ID."""
        db = DatabaseService()
        return db.create_execution(session, execution_data)

    @staticmethod
    def update_execution(
        session: Session, execution_id: str, update_data: Dict[str, Any]
    ) -> bool:
        """Update an execution with the given data."""
        db = DatabaseService()
        # Convert string status to enum if needed
        if "status" in update_data:
            status_val = update_data["status"]
            if isinstance(status_val, str):
                try:
                    update_data["status"] = DBExecutionStatus(status_val)
                except ValueError:
                    # Keep as-is if not a valid enum value
                    pass
        return db.update_execution(session, execution_id, update_data)
