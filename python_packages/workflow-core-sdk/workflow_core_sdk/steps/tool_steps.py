"""
Tool Execution Step

Allows invoking a tool (local, DB-registered, or MCP) as a standalone workflow step.
Supports parameter mapping from step input_data and static defaults.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import importlib
import logging
import time
from datetime import datetime

from sqlmodel import Session, select

from workflow_core_sdk.execution_context import ExecutionContext
from workflow_core_sdk.db.database import engine
from workflow_core_sdk.db.models import Tool as DBTool, MCPServer
from workflow_core_sdk.tools import get_all_tools
from workflow_core_sdk.execution.streaming import stream_manager, create_step_event
from workflow_core_sdk.clients.mcp_client import (
    mcp_client,
    MCPToolExecutionError,
    MCPServerUnavailableError,
)
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
    - MCP tools (tool_type="mcp", execution_type="api") are executed via MCP client.
    """
    cfg = step_config.get("config", {}) or {}
    tool_name: Optional[str] = cfg.get("tool_name")
    tool_id: Optional[str] = cfg.get("tool_id")
    param_mapping: Dict[str, str] = cfg.get("param_mapping", {}) or {}
    static_params: Dict[str, Any] = cfg.get("static_params", {}) or {}

    resolved_name: Optional[str] = None
    func = None
    tool_record: Optional[DBTool] = None

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
            tool_record = rec
            resolved_name = rec.name or tool_name

            # Check if this is an MCP tool
            if (
                rec.tool_type == "mcp"
                and rec.execution_type == "api"
                and rec.mcp_server_id
            ):
                # MCP tool - will be handled separately below
                pass
            # Prefer module_path/function_name if available for local tools
            elif rec.module_path and rec.function_name:
                try:
                    mod = importlib.import_module(rec.module_path)
                    func = getattr(mod, rec.function_name)
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Failed to import {rec.module_path}.{rec.function_name}: {e}",
                        "resolved": {
                            "by": "id",
                            "tool_id": tool_id,
                            "name": resolved_name,
                        },
                    }
        except Exception as e:
            return {"success": False, "error": f"DB error resolving tool_id: {e}"}

    # Resolve by name (fallback or direct) for local tools
    if func is None and tool_record is None and (tool_name or resolved_name):
        name: str = tool_name or (resolved_name or "")
        local_tools = get_all_tools()
        func = local_tools.get(name)  # local tools
        resolved_name = name

    # If we have an MCP tool, execute it via MCP client
    if (
        tool_record
        and tool_record.tool_type == "mcp"
        and tool_record.execution_type == "api"
    ):
        return await _execute_mcp_tool(
            tool_record=tool_record,
            param_mapping=param_mapping,
            static_params=static_params,
            input_data=input_data,
            step_config=step_config,
            execution_context=execution_context,
        )

    if func is None:
        # Mark as a hard failure so the engine can fail the execution if critical
        raise Exception(
            f"Tool not found or unsupported: name={resolved_name} id={tool_id}"
        )

    # Build call params from mapping + static
    # First, build an extended input_data that includes trigger data from execution context
    extended_input_data = dict(input_data) if input_data else {}

    # Add trigger data if available in step_io_data
    # This allows param_mapping paths like "trigger.current_message" or "trigger.messages"
    if hasattr(execution_context, "step_io_data"):
        trigger_data = execution_context.step_io_data.get(
            "trigger"
        ) or execution_context.step_io_data.get("trigger_raw")
        if trigger_data and "trigger" not in extended_input_data:
            extended_input_data["trigger"] = trigger_data

        # Also make step_io_data accessible for direct references to other steps
        for step_id_key, step_output in execution_context.step_io_data.items():
            if step_id_key not in extended_input_data:
                extended_input_data[step_id_key] = step_output

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
        val = extract_from_path(extended_input_data, spath)
        if val is not None:
            params[pname] = val

    # Get tool parameter names for spreading logic
    tool_param_names: set = set()
    if func is not None:
        try:
            import inspect

            sig = inspect.signature(func)
            tool_param_names = set(sig.parameters.keys())
        except Exception:
            pass

    # Special case: if param_mapping is empty but input_data has trigger data,
    # try to extract params from trigger.current_message
    # This handles the UI case where "use response" toggle is set but no explicit param_mapping
    if not params and tool_param_names:
        trigger_source = None
        # Check input_data for trigger mapping (e.g., input_mapping: {response: "trigger"})
        if input_data:
            for ikey, ival in input_data.items():
                if isinstance(ival, dict) and "current_message" in ival:
                    trigger_source = ival.get("current_message")
                    break
        # Also check extended_input_data.trigger.current_message
        if not trigger_source and "trigger" in extended_input_data:
            trigger_data = extended_input_data["trigger"]
            if isinstance(trigger_data, dict):
                trigger_source = trigger_data.get("current_message")

        if trigger_source:
            # Try to parse as JSON and spread properties
            if isinstance(trigger_source, str):
                try:
                    parsed = json.loads(trigger_source)
                    if isinstance(parsed, dict):
                        for inner_key, inner_val in parsed.items():
                            if inner_key in tool_param_names:
                                params[inner_key] = inner_val
                except (json.JSONDecodeError, ValueError):
                    pass
            elif isinstance(trigger_source, dict):
                for inner_key, inner_val in trigger_source.items():
                    if inner_key in tool_param_names:
                        params[inner_key] = inner_val

    # Special case: if trigger.current_message was mapped but the tool doesn't have that param,
    # and the value is a dict, spread the dict properties as individual params.
    # This handles the UI case where "use response" is toggled and user sends JSON like {"a": 42, "b": 69}
    if params and tool_param_names:
        # Find params that don't match any tool parameter
        unmatched = {k: v for k, v in params.items() if k not in tool_param_names}
        for unmapped_key, unmapped_val in unmatched.items():
            # If the value is a dict, spread its properties as individual params
            if isinstance(unmapped_val, dict):
                for inner_key, inner_val in unmapped_val.items():
                    if inner_key in tool_param_names and inner_key not in params:
                        params[inner_key] = inner_val
                # Remove the unmatched key
                del params[unmapped_key]
            # If the value is a JSON string, try parsing and spreading
            elif isinstance(unmapped_val, str):
                try:
                    parsed = json.loads(unmapped_val)
                    if isinstance(parsed, dict):
                        for inner_key, inner_val in parsed.items():
                            if (
                                inner_key in tool_param_names
                                and inner_key not in params
                            ):
                                params[inner_key] = inner_val
                        # Remove the unmatched key
                        del params[unmapped_key]
                except (json.JSONDecodeError, ValueError):
                    pass

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
                            params[pname] = v.strip().lower() in (
                                "true",
                                "1",
                                "yes",
                                "y",
                            )
                    except Exception:
                        pass
    except Exception:
        pass

    # Emit tool_call event (same format as agent executions for frontend consistency)
    step_id = step_config.get("step_id", "unknown")
    start_time = time.time()
    try:
        tool_call_event = create_step_event(
            execution_id=execution_context.execution_id,
            step_id=step_id,
            step_status="running",
            workflow_id=execution_context.workflow_id,
            step_type="tool_execution",
            output_data={
                "event_type": "tool_call",
                "tool_name": resolved_name,
                "arguments": params,
            },
        )
        await stream_manager.emit_execution_event(tool_call_event)
        if execution_context.workflow_id:
            await stream_manager.emit_workflow_event(tool_call_event)
    except Exception as e:
        logger.debug(f"Failed to emit tool_call event: {e}")

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
                output_data={
                    "tool_name": resolved_name,
                    "error": f"Parameter mismatch: {e}",
                },
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

    # Emit tool_response event (same format as agent executions for frontend consistency)
    # Note: Use step_status="running" so this is treated as an intermediate update,
    # not the final step completion (which is emitted by the engine with the return value)
    duration_ms = int((time.time() - start_time) * 1000)
    try:
        tool_response_event = create_step_event(
            execution_id=execution_context.execution_id,
            step_id=step_id,
            step_status="running",
            workflow_id=execution_context.workflow_id,
            step_type="tool_execution",
            output_data={
                "event_type": "tool_response",
                "tool_name": resolved_name,
                "result": result,
                "duration_ms": duration_ms,
            },
        )
        await stream_manager.emit_execution_event(tool_response_event)
        if execution_context.workflow_id:
            await stream_manager.emit_workflow_event(tool_response_event)
    except Exception as e:
        logger.debug(f"Failed to emit tool_response event: {e}")

    return {
        "success": True,
        "tool": {"name": resolved_name},
        "params": params,
        "result": result,
        "executed_at": datetime.now().isoformat(),
    }


async def _execute_mcp_tool(
    tool_record: DBTool,
    param_mapping: Dict[str, str],
    static_params: Dict[str, Any],
    input_data: Dict[str, Any],
    step_config: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Execute an MCP tool via the MCP client.

    Args:
        tool_record: Database tool record with MCP server info
        param_mapping: Parameter mapping from input_data
        static_params: Static parameter values
        input_data: Step input data
        step_config: Step configuration
        execution_context: Execution context

    Returns:
        Tool execution result
    """
    step_id = step_config.get("step_id", "unknown")
    tool_name = tool_record.name
    remote_name = tool_record.remote_name or tool_name

    # Get MCP server configuration
    try:
        with Session(engine) as session:
            mcp_server = session.exec(
                select(MCPServer).where(MCPServer.id == tool_record.mcp_server_id)
            ).first()

        if not mcp_server:
            error_msg = f"MCP server not found for tool {tool_name}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "tool": {"name": tool_name, "type": "mcp"},
            }
    except Exception as e:
        error_msg = f"Failed to fetch MCP server: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "tool": {"name": tool_name, "type": "mcp"},
        }

    # Build server configuration for MCP client
    server_config = {
        "host": mcp_server.host,
        "port": mcp_server.port,
        "protocol": mcp_server.protocol or "http",
        "endpoint": mcp_server.endpoint,
        "auth_type": mcp_server.auth_type,
        "auth_config": mcp_server.auth_config or {},
    }

    # Build extended input_data that includes trigger data from execution context
    # This allows param_mapping paths like "trigger.current_message" or "trigger.messages"
    extended_input_data = dict(input_data) if input_data else {}

    if hasattr(execution_context, "step_io_data"):
        trigger_data = execution_context.step_io_data.get(
            "trigger"
        ) or execution_context.step_io_data.get("trigger_raw")
        if trigger_data and "trigger" not in extended_input_data:
            extended_input_data["trigger"] = trigger_data

        # Also make step_io_data accessible for direct references to other steps
        for step_id_key, step_output in execution_context.step_io_data.items():
            if step_id_key not in extended_input_data:
                extended_input_data[step_id_key] = step_output

    # Build parameters using the same logic as local tools
    def extract_from_path(data: Any, path: str) -> Any:
        """Extract value from nested data using dot notation."""
        if not path:
            return data

        parts = path.split(".")
        current = data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, str):
                try:
                    current = json.loads(current)
                    if isinstance(current, dict):
                        current = current.get(part)
                except (json.JSONDecodeError, TypeError):
                    return None
            else:
                return None

            if current is None:
                return None

        return current

    # Build parameters
    params: Dict[str, Any] = {}

    # Apply static params first
    for key, value in static_params.items():
        params[key] = value

    # Apply mapped params (can override static)
    for param_name, path in param_mapping.items():
        val = extract_from_path(extended_input_data, path)
        if val is not None:
            params[param_name] = val

    # Emit tool_call event (same format as agent executions for frontend consistency)
    start_time = time.time()
    try:
        tool_call_event = create_step_event(
            execution_id=execution_context.execution_id,
            step_id=step_id,
            step_status="running",
            workflow_id=execution_context.workflow_id,
            step_type="tool_execution",
            output_data={
                "event_type": "tool_call",
                "tool_name": tool_name,
                "tool_type": "mcp",
                "remote_name": remote_name,
                "server": mcp_server.name,
                "arguments": params,
            },
        )
        await stream_manager.emit_execution_event(tool_call_event)
        if execution_context.workflow_id:
            await stream_manager.emit_workflow_event(tool_call_event)
    except Exception as e:
        logger.debug(f"Failed to emit MCP tool_call event: {e}")

    # Execute tool via MCP client
    try:
        result = await mcp_client.execute_tool(
            server_config=server_config,
            tool_name=remote_name,
            parameters=params,
            execution_id=execution_context.execution_id,
        )

        # Emit tool_response event (same format as agent executions for frontend consistency)
        # Note: Use step_status="running" so this is treated as an intermediate update,
        # not the final step completion (which is emitted by the engine with the return value)
        duration_ms = int((time.time() - start_time) * 1000)
        try:
            tool_response_event = create_step_event(
                execution_id=execution_context.execution_id,
                step_id=step_id,
                step_status="running",
                workflow_id=execution_context.workflow_id,
                step_type="tool_execution",
                output_data={
                    "event_type": "tool_response",
                    "tool_name": tool_name,
                    "tool_type": "mcp",
                    "remote_name": remote_name,
                    "server": mcp_server.name,
                    "result": result,
                    "duration_ms": duration_ms,
                },
            )
            await stream_manager.emit_execution_event(tool_response_event)
            if execution_context.workflow_id:
                await stream_manager.emit_workflow_event(tool_response_event)
        except Exception as e:
            logger.debug(f"Failed to emit MCP tool_response event: {e}")

        return {
            "success": True,
            "tool": {
                "name": tool_name,
                "type": "mcp",
                "remote_name": remote_name,
                "server": mcp_server.name,
            },
            "params": params,
            "result": result,
            "executed_at": datetime.now().isoformat(),
        }

    except MCPServerUnavailableError as e:
        error_msg = f"MCP server unavailable: {e}"
        logger.error(error_msg)

        # Emit error event
        try:
            error_event = create_step_event(
                execution_id=execution_context.execution_id,
                step_id=step_id,
                step_status="failed",
                workflow_id=execution_context.workflow_id,
                step_type="tool_execution",
                output_data={
                    "tool_name": tool_name,
                    "tool_type": "mcp",
                    "error": error_msg,
                },
            )
            await stream_manager.emit_execution_event(error_event)
            if execution_context.workflow_id:
                await stream_manager.emit_workflow_event(error_event)
        except Exception as emit_error:
            logger.debug(f"Failed to emit MCP tool error event: {emit_error}")

        return {
            "success": False,
            "error": error_msg,
            "tool": {
                "name": tool_name,
                "type": "mcp",
                "remote_name": remote_name,
                "server": mcp_server.name,
            },
        }

    except MCPToolExecutionError as e:
        error_msg = f"MCP tool execution failed: {e}"
        logger.error(error_msg)

        # Emit error event
        try:
            error_event = create_step_event(
                execution_id=execution_context.execution_id,
                step_id=step_id,
                step_status="failed",
                workflow_id=execution_context.workflow_id,
                step_type="tool_execution",
                output_data={
                    "tool_name": tool_name,
                    "tool_type": "mcp",
                    "error": error_msg,
                },
            )
            await stream_manager.emit_execution_event(error_event)
            if execution_context.workflow_id:
                await stream_manager.emit_workflow_event(error_event)
        except Exception as emit_error:
            logger.debug(f"Failed to emit MCP tool error event: {emit_error}")

        return {
            "success": False,
            "error": error_msg,
            "tool": {
                "name": tool_name,
                "type": "mcp",
                "remote_name": remote_name,
                "server": mcp_server.name,
            },
        }

    except Exception as e:
        error_msg = f"Unexpected error executing MCP tool: {e}"
        logger.error(error_msg)

        return {
            "success": False,
            "error": error_msg,
            "tool": {
                "name": tool_name,
                "type": "mcp",
                "remote_name": remote_name,
                "server": mcp_server.name,
            },
        }
