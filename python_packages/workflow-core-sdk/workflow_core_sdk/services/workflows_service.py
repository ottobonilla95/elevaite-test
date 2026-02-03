from __future__ import annotations

from typing import Optional, List, Dict, Any
import uuid as uuid_module

from sqlmodel import Session

from ..db.models import Workflow
from ..db.models.executions import ExecutionStatus as DBExecutionStatus
from ..db.service import DatabaseService


class WorkflowsService:
    """Router-facing service to encapsulate DB access for workflows and executions.
    Internally delegates to DatabaseService (ORM wrapper) so routers don't touch ORM directly.
    """

    # -------- Workflow entities (SQLModel) --------
    @staticmethod
    def list_workflows_entities(
        session: Session, *, limit: int = 100, offset: int = 0
    ) -> List[Workflow]:
        db = DatabaseService()
        return db.list_workflow_entities(session, limit=limit, offset=offset)

    @staticmethod
    def get_workflow_entity(session: Session, workflow_id: str) -> Optional[Workflow]:
        db = DatabaseService()
        return db.get_workflow_entity(session, workflow_id)

    @staticmethod
    def create_workflow(session: Session, workflow_data: Dict[str, Any]) -> Workflow:
        """Create a new workflow and return the ORM entity."""
        db = DatabaseService()
        wf_id = str(uuid_module.uuid4())
        db.save_workflow(session, wf_id, workflow_data)
        wf = db.get_workflow_entity(session, wf_id)
        if not wf:
            raise RuntimeError("Failed to retrieve saved workflow entity")
        return wf

    @staticmethod
    def save_workflow(
        session: Session, workflow_id: str, workflow_data: Dict[str, Any]
    ) -> Workflow:
        """Save (create or update) a workflow and return the ORM entity.

        Uses upsert semantics - creates if not exists, updates if exists.
        """
        db = DatabaseService()
        db.save_workflow(session, workflow_id, workflow_data)
        wf = db.get_workflow_entity(session, workflow_id)
        if not wf:
            raise RuntimeError("Failed to retrieve saved workflow entity")
        return wf

    @staticmethod
    def delete_workflow(session: Session, workflow_id: str) -> bool:
        db = DatabaseService()
        return db.delete_workflow(session, workflow_id)

    # -------- Workflow configuration (dict) --------
    @staticmethod
    def get_workflow_config(
        session: Session, workflow_id: str
    ) -> Optional[Dict[str, Any]]:
        db = DatabaseService()
        return db.get_workflow(session, workflow_id)

    # -------- Executions (dict/ORM hybrids as defined in DatabaseService) --------
    @staticmethod
    def create_execution(session: Session, execution_data: Dict[str, Any]) -> str:
        db = DatabaseService()
        return db.create_execution(session, execution_data)

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
    def update_execution_status(
        session: Session, execution_id: str, status: str
    ) -> bool:
        """Update the execution's status in the database (e.g., to 'running')."""
        db = DatabaseService()
        try:
            status_enum = (
                DBExecutionStatus(status) if isinstance(status, str) else status
            )
        except Exception:
            # Fallback without raising if invalid; let DB layer handle/ignore
            status_enum = status
        return db.update_execution(session, execution_id, {"status": status_enum})

    # -------- Agent Messages --------
    @staticmethod
    def create_agent_message(
        session: Session,
        *,
        execution_id: str,
        step_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        db = DatabaseService()
        return db.create_agent_message(
            session,
            execution_id=execution_id,
            step_id=step_id,
            role=role,
            content=content,
            metadata=metadata,
            user_id=user_id,
            session_id=session_id,
        )

    @staticmethod
    def list_agent_messages(
        session: Session,
        *,
        execution_id: str,
        step_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        db = DatabaseService()
        return db.list_agent_messages(
            session,
            execution_id=execution_id,
            step_id=step_id,
            limit=limit,
            offset=offset,
        )
