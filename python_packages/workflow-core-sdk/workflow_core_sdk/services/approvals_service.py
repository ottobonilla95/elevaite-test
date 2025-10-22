from __future__ import annotations

from typing import Optional, List, Dict, Any

from sqlmodel import Session

from ..db.service import DatabaseService


class ApprovalsService:
    """Encapsulate DB access for approval requests.
    Routers call this layer; internals delegate to DatabaseService.
    """

    @staticmethod
    def list_approval_requests(
        session: Session,
        *,
        execution_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        db = DatabaseService()
        return db.list_approval_requests(
            session,
            execution_id=execution_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def get_approval_request(session: Session, approval_id: str) -> Optional[Dict[str, Any]]:
        db = DatabaseService()
        return db.get_approval_request(session, approval_id)

    @staticmethod
    def create_approval_request(session: Session, data: Dict[str, Any]) -> str:
        db = DatabaseService()
        return db.create_approval_request(session, data)

    @staticmethod
    def update_approval_request(session: Session, approval_id: str, changes: Dict[str, Any]) -> bool:
        db = DatabaseService()
        return db.update_approval_request(session, approval_id, changes)

