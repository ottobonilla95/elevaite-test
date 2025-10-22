"""
Tool Execution Step

Allows invoking a tool (local or DB-registered) as a standalone workflow step.
Supports parameter mapping from step input_data and static defaults.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import importlib
import logging
from datetime import datetime

from sqlmodel import Session, select

from workflow_core_sdk.execution_context import ExecutionContext
from workflow_core_sdk.db.database import engine
from workflow_core_sdk.db.models import Tool as DBTool
from workflow_core_sdk.tools import get_all_tools
from workflow_core_sdk.execution.streaming import stream_manager, create_step_event

logger = logging.getLogger(__name__)


async def tool_execution_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Execute a tool by name or id.

    Config options (step_config["config"]):
    - tool_name: Optional[str]  # e.g., "add_numbers"
    - tool_id: Optional[str]    # UUID of a DB tool
    - param_mapping: Dict[str, str]  # param_name -> dot-path within input_data
    - static_params: Dict[str, Any]  # defaults/overrides for parameters

    Notes:
    - Local tools are resolved from basic_tools.
    - DB tools that are local can also be resolved by name; if module_path is provided,
      we attempt to import the function dynamically.
    - Remote/MCP/api tools are not implemented in this first version.
    """
    cfg = step_config.get("config", {}) or {}
    tool_name: Optional[str] = cfg.get("tool_name")
    tool_id: Optional[str] = cfg.get("tool_id")
    param_mapping: Dict[str, str] = cfg.get("param_mapping", {}) or {}
    static_params: Dict[str, Any] = cfg.get("static_params", {}) or {}

    resolved_name: Optional[str] = None
    func = None

    # Resolve by tool_id if provided
    if tool_id:
        try:
            with Session(engine) as session:
                rec = session.exec(select(DBTool).where(DBTool.id == tool_id)).first()
            if rec is None:
                return {
                    "success": False,
                    "error": f"Tool not found: id={tool_id}",
                    "resolved": {"by": "id", "tool_id": tool_id},
                }
            resolved_name = rec.name or tool_name
            # Prefer module_path/function_name if available
            if rec.module_path and rec.function_name:
                try:
                    mod = importlib.import_module(rec.module_path)
                    func = getattr(mod, rec.function_name)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to import {rec.module_path}.{rec.function_name}: {e}",
                        "resolved": {"by": "id", "tool_id": tool_id, "name": resolved_name},
                    }
        except Exception as e:
            return {"success": False, "error": f"DB error resolving tool_id: {e}"}

    # Resolve by name (fallback or direct)
    if func is None and (tool_name or resolved_name):
        name: str = tool_name or (resolved_name or "")
        local_tools = get_all_tools()
        func = local_tools.get(name)  # local tools
        resolved_name = name

    if func is None:
        # Mark as a hard failure so the engine can fail the execution if critical
        raise Exception(
            f"Tool not found or unsupported (only local tools supported currently): name={resolved_name} id={tool_id}"
        )

    # Build call params from mapping + static
    def extract_from_path(data: Any, path: str) -> Any:
        cur = data
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
                # Auto-parse JSON strings
                if isinstance(cur, str):
                    try:
                        import json

                        parsed = json.loads(cur)
                        if isinstance(parsed, dict):
                            cur = parsed
                    except (json.JSONDecodeError, ValueError):
                        # Not JSON, keep as string
                        pass
            else:
                return None
        return cur

    params = dict(static_params)
    for pname, spath in param_mapping.items():
        val = extract_from_path(input_data, spath)
        if val is not None:
            params[pname] = val

    # Emit tool execution start event
    step_id = step_config.get("step_id", "unknown")
    try:
        start_event = create_step_event(
            execution_id=execution_context.execution_id,
            step_id=step_id,
            step_status="running",
            workflow_id=execution_context.workflow_id,
            step_type="tool_execution",
            output_data={"tool_name": resolved_name, "params": params, "message": f"Executing tool: {resolved_name}"},
        )
        await stream_manager.emit_execution_event(start_event)
        if execution_context.workflow_id:
            await stream_manager.emit_workflow_event(start_event)
    except Exception as e:
        logger.debug(f"Failed to emit tool start event: {e}")

    # Execute tool
    try:
        result = func(**params)  # basic_tools are synchronous functions
    except TypeError as e:
        # Emit error event
        try:
            error_event = create_step_event(
                execution_id=execution_context.execution_id,
                step_id=step_id,
                step_status="failed",
                workflow_id=execution_context.workflow_id,
                step_type="tool_execution",
                output_data={"tool_name": resolved_name, "error": f"Parameter mismatch: {e}"},
            )
            await stream_manager.emit_execution_event(error_event)
            if execution_context.workflow_id:
                await stream_manager.emit_workflow_event(error_event)
        except Exception:
            pass

        return {
            "success": False,
            "error": f"Parameter mismatch when calling tool '{resolved_name}': {e}",
            "resolved": {"name": resolved_name},
            "params": params,
        }
    except Exception as e:
        # Emit error event
        try:
            error_event = create_step_event(
                execution_id=execution_context.execution_id,
                step_id=step_id,
                step_status="failed",
                workflow_id=execution_context.workflow_id,
                step_type="tool_execution",
                output_data={"tool_name": resolved_name, "error": str(e)},
            )
            await stream_manager.emit_execution_event(error_event)
            if execution_context.workflow_id:
                await stream_manager.emit_workflow_event(error_event)
        except Exception:
            pass

        return {
            "success": False,
            "error": f"Tool '{resolved_name}' raised an error: {e}",
            "resolved": {"name": resolved_name},
            "params": params,
        }

    # Emit tool completion event
    try:
        complete_event = create_step_event(
            execution_id=execution_context.execution_id,
            step_id=step_id,
            step_status="completed",
            workflow_id=execution_context.workflow_id,
            step_type="tool_execution",
            output_data={
                "tool_name": resolved_name,
                "result": result,
                "message": f"Tool {resolved_name} completed successfully",
            },
        )
        await stream_manager.emit_execution_event(complete_event)
        if execution_context.workflow_id:
            await stream_manager.emit_workflow_event(complete_event)
    except Exception as e:
        logger.debug(f"Failed to emit tool completion event: {e}")

    return {
        "success": True,
        "tool": {"name": resolved_name},
        "params": params,
        "result": result,
        "executed_at": datetime.now().isoformat(),
    }
