"""
Flow Control Steps

Steps that control workflow execution flow, including subflows,
conditional execution, and other control structures.
"""

from typing import Dict, Any
from datetime import datetime
import logging

from workflow_core_sdk.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


async def subflow_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Subflow step that executes another workflow as a nested component.

    This enables composition of complex workflows from smaller reusable components.

    Config options:
    - workflow_id: ID of the workflow to execute as a subflow
    - input_mapping: How to map current input data to subflow input
    - output_mapping: How to map subflow output back to current workflow
    - inherit_context: Whether to inherit user context from parent workflow (default: True)
    """
    from ..db.service import DatabaseService
    from ..db.database import engine
    from sqlmodel import Session

    config = step_config.get("config", {})
    workflow_id = config.get("workflow_id")

    if not workflow_id:
        return {
            "subflow_id": None,
            "subflow_execution_id": None,
            "subflow_status": "failed",
            "error": "subflow step requires 'workflow_id' in config",
            "input_data": input_data,
            "success": False,
        }

    # Load the subflow workflow using a session-injected DatabaseService
    try:
        db_service = DatabaseService()
        with Session(engine) as session:
            subflow_config = db_service.get_workflow(session, workflow_id)

        if not subflow_config:
            return {
                "subflow_id": workflow_id,
                "subflow_execution_id": None,
                "subflow_status": "failed",
                "error": f"Subflow workflow not found: {workflow_id}",
                "input_data": input_data,
                "success": False,
            }
    except Exception as e:
        return {
            "subflow_id": workflow_id,
            "subflow_execution_id": None,
            "subflow_status": "failed",
            "error": f"Failed to load subflow workflow: {e}",
            "input_data": input_data,
            "success": False,
        }

    # Handle input mapping
    input_mapping = config.get("input_mapping", {})
    subflow_input = {}

    if input_mapping:
        # Map input data according to mapping configuration
        for target_key, source_path in input_mapping.items():
            # Simple dot notation support (e.g., "data.message")
            value = input_data
            for path_part in source_path.split("."):
                if isinstance(value, dict) and path_part in value:
                    value = value[path_part]
                else:
                    value = None
                    break
            if value is not None:
                subflow_input[target_key] = value
    else:
        # If no mapping specified, pass all input data
        subflow_input = input_data

    # Create execution context for subflow
    inherit_context = config.get("inherit_context", True)

    if inherit_context:
        # Create new execution context that inherits user context
        subflow_execution_context = ExecutionContext(
            workflow_config=subflow_config,
            user_context=execution_context.user_context,
            workflow_engine=execution_context.workflow_engine,
        )
    else:
        # Create isolated execution context
        from ..execution_context import UserContext

        isolated_user_context = UserContext(
            user_id=f"subflow-{execution_context.execution_id}",
            session_id=f"subflow-session-{execution_context.execution_id}",
            organization_id=execution_context.user_context.organization_id,
        )
        subflow_execution_context = ExecutionContext(
            workflow_config=subflow_config,
            user_context=isolated_user_context,
            workflow_engine=execution_context.workflow_engine,
        )

    # Add subflow input to the execution context
    subflow_execution_context.step_io_data["subflow_input"] = subflow_input

    # Get workflow engine from the current execution context
    if not execution_context.workflow_engine:
        return {
            "subflow_id": workflow_id,
            "subflow_execution_id": None,
            "subflow_status": "failed",
            "error": "Workflow engine not available in execution context for subflow execution",
            "input_data": input_data,
            "success": False,
        }

    workflow_engine = execution_context.workflow_engine

    start_time = datetime.now()

    try:
        # Execute the subflow
        completed_context = await workflow_engine.execute_workflow(subflow_execution_context)
        end_time = datetime.now()

        # Handle output mapping
        output_mapping = config.get("output_mapping", {})
        mapped_output = {}

        if output_mapping:
            # Map subflow output according to mapping configuration
            subflow_output = completed_context.step_io_data
            for target_key, source_path in output_mapping.items():
                value = subflow_output
                for path_part in source_path.split("."):
                    if isinstance(value, dict) and path_part in value:
                        value = value[path_part]
                    else:
                        value = None
                        break
                if value is not None:
                    mapped_output[target_key] = value
        else:
            # If no mapping specified, return all subflow output
            mapped_output = completed_context.step_io_data

        return {
            "subflow_id": workflow_id,
            "subflow_execution_id": completed_context.execution_id,
            "subflow_status": completed_context.status.value,
            "subflow_output": mapped_output,
            "execution_time_seconds": (end_time - start_time).total_seconds(),
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat(),
            "input_data": input_data,
            "success": True,
        }

    except Exception as e:
        end_time = datetime.now()
        return {
            "subflow_id": workflow_id,
            "subflow_execution_id": subflow_execution_context.execution_id,
            "subflow_status": "failed",
            "error": str(e),
            "execution_time_seconds": (end_time - start_time).total_seconds(),
            "started_at": start_time.isoformat(),
            "failed_at": end_time.isoformat(),
            "input_data": input_data,
            "success": False,
        }
