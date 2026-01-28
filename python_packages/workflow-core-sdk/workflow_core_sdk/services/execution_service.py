"""
Workflow Execution Service

This module provides service-level workflow execution functions that can be used
by schedulers, background tasks, and other internal components without requiring
HTTP request handling.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from sqlmodel import Session

from ..execution.context_impl import ExecutionContext, UserContext
from ..db.service import DatabaseService
from ..dbos_impl.workflows import execute_and_persist_dbos_result

logger = logging.getLogger(__name__)


class ExecutionService:
    """Service for executing workflows programmatically"""

    @staticmethod
    async def execute_workflow(
        *,
        workflow_id: str,
        session: Session,
        workflow_engine: Any,  # WorkflowEngine type
        backend: str = "dbos",
        trigger_payload: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        wait: bool = False,
    ) -> str:
        """
        Execute a workflow programmatically without HTTP request handling.

        This is the core execution logic extracted from the router layer,
        suitable for use by schedulers, background tasks, and other internal components.

        Args:
            workflow_id: ID of the workflow to execute
            session: Database session
            workflow_engine: WorkflowEngine instance
            backend: Execution backend ("dbos" or "local")
            trigger_payload: Trigger data (defaults to webhook trigger with metadata)
            user_id: User ID for execution context
            session_id: Session ID for execution context
            organization_id: Organization ID for execution context
            input_data: Additional input data for the workflow
            metadata: Execution metadata
            wait: Whether to wait for execution to complete

        Returns:
            execution_id: ID of the created execution

        Raises:
            ValueError: If workflow not found or invalid backend
            RuntimeError: If execution fails
        """
        db = DatabaseService()

        # Get workflow configuration
        workflow = db.get_workflow(session, workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")

        # Default trigger payload if not provided
        if trigger_payload is None:
            trigger_payload = {
                "kind": "webhook",
                "data": metadata or {},
            }

        # Default metadata
        if metadata is None:
            metadata = {}

        # Default input data
        if input_data is None:
            input_data = {}

        # Validate backend
        if backend not in ("dbos", "local"):
            raise ValueError(f"Invalid execution backend: {backend}")

        # Create execution record
        execution_id = db.create_execution(
            session,
            {
                "workflow_id": workflow_id,
                "user_id": user_id,
                "session_id": session_id,
                "organization_id": organization_id,
                "input_data": input_data,
                "metadata": metadata,
            },
        )

        # Execute based on backend
        if backend == "dbos":
            # Execute via DBOS adapter
            try:
                execution_id = await execute_and_persist_dbos_result(
                    session,
                    db,
                    workflow=workflow,
                    trigger_payload=trigger_payload,
                    user_context={
                        "user_id": user_id,
                        "session_id": session_id,
                        "organization_id": organization_id,
                    },
                    execution_id=execution_id,
                    wait=wait,
                    metadata=metadata,
                    chosen_backend=backend,
                )
            except RuntimeError as e:
                raise RuntimeError(f"DBOS execution failed: {e}")
        else:
            # Local backend execution
            # Build execution context
            user_context = UserContext(
                user_id=user_id,
                session_id=session_id,
                organization_id=organization_id,
            )
            execution_context = ExecutionContext(
                workflow_config=workflow,
                user_context=user_context,
                workflow_engine=workflow_engine,
                execution_id=execution_id,
            )

            # Seed trigger payload and input data
            execution_context.step_io_data["trigger_raw"] = trigger_payload
            if input_data:
                execution_context.step_io_data.update(input_data)

            # Execute workflow
            if wait:
                # Synchronous execution
                await workflow_engine.execute_workflow(execution_context)
            else:
                # Asynchronous execution (fire and forget)
                async def execute_async():
                    try:
                        await workflow_engine.execute_workflow(execution_context)
                    except Exception as e:
                        logger.error(
                            f"Background execution failed for {execution_id}: {e}",
                            exc_info=True,
                        )

                asyncio.create_task(execute_async())

        return execution_id
