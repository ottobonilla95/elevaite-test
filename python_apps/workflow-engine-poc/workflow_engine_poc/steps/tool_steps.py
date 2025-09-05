"""
Tool Execution Step

Allows invoking a tool (local or DB-registered) as a standalone workflow step.
Supports parameter mapping from step input_data and static defaults.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import importlib
from datetime import datetime

from sqlmodel import Session, select

from ..execution_context import ExecutionContext
from ..db.database import engine
from ..db.models import Tool as DBTool
from ..tools.basic_tools import get_all_tools


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
            else:
                return None
        return cur

    params = dict(static_params)
    for pname, spath in param_mapping.items():
        val = extract_from_path(input_data, spath)
        if val is not None:
            params[pname] = val

    # Execute tool
    try:
        result = func(**params)  # basic_tools are synchronous functions
    except TypeError as e:
        return {
            "success": False,
            "error": f"Parameter mismatch when calling tool '{resolved_name}': {e}",
            "resolved": {"name": resolved_name},
            "params": params,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool '{resolved_name}' raised an error: {e}",
            "resolved": {"name": resolved_name},
            "params": params,
        }

    return {
        "success": True,
        "tool": {"name": resolved_name},
        "params": params,
        "result": result,
        "executed_at": datetime.now().isoformat(),
    }
