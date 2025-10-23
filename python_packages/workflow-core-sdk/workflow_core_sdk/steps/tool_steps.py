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
import json

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
        """
        Resolve a dot-path against input_data with a couple of conveniences:
        - If a segment resolves to a JSON string, parse it and continue traversal
        - If the current object is a dict that does not contain the requested key,
          but has a 'response' key that is a JSON string, parse that and retry the
          lookup against the parsed object. This allows paths like 'response.x'
          to access fields inside an agent step's textual JSON response without
          requiring 'response.response.x'.
        """

        def try_parse_json(s: Any) -> Optional[dict]:
            if isinstance(s, str):
                s_strip = s.strip()
                if s_strip.startswith("{") or s_strip.startswith("["):
                    try:
                        parsed = json.loads(s_strip)
                        return parsed if isinstance(parsed, dict) else None
                    except (json.JSONDecodeError, ValueError):
                        return None
            return None

        cur = data
        for part in path.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
                parsed = try_parse_json(cur)
                if parsed is not None:
                    cur = parsed
            else:
                # Fallback: if current dict has textual JSON under 'response',
                # parse it and try to find 'part' inside it.
                if isinstance(cur, dict) and isinstance(cur.get("response"), str):
                    parsed = try_parse_json(cur.get("response"))
                    if isinstance(parsed, dict) and part in parsed:
                        cur = parsed[part]
                        continue
                return None
        return cur

    params = dict(static_params)
    for pname, spath in param_mapping.items():
        val = extract_from_path(input_data, spath)
        if val is not None:
            params[pname] = val

    # Best-effort type coercion based on the tool function signature
    try:
        import inspect

        sig = inspect.signature(func)
        for pname, p in sig.parameters.items():
            if pname in params and p.annotation in (int, float, bool):
                v = params[pname]
                if p.annotation is int:
                    try:
                        params[pname] = int(v) if not isinstance(v, int) else v
                    except Exception:
                        pass
                elif p.annotation is float:
                    try:
                        params[pname] = float(v) if not isinstance(v, float) else v
                    except Exception:
                        pass
                elif p.annotation is bool:
                    try:
                        if isinstance(v, str):
                            params[pname] = v.strip().lower() in ("true", "1", "yes", "y")
                    except Exception:
                        pass
    except Exception:
        pass

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
