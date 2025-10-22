"""
Tool adapter for converting SDK UnifiedTool to Agent Studio ToolResponse format.

This adapter bridges the gap between the SDK's UnifiedTool (from tool_registry)
and Agent Studio's expected ToolResponse schema with all legacy fields.
"""

from typing import Dict, Any
from sqlmodel import Session, select
from uuid import UUID as UUID_type

from workflow_core_sdk.tools.registry import UnifiedTool
from workflow_core_sdk.services.tools_service import ToolsService
from workflow_core_sdk.db.models.tools import MCPServer


def unified_tool_to_response(unified_tool: UnifiedTool, db: Session) -> Dict[str, Any]:
    """
    Convert UnifiedTool to full ToolResponse format with all fields.

    This function:
    1. Fetches full DB tool details if available
    2. Fetches related category and MCP server if present
    3. Returns a complete response matching the ToolResponse schema

    Args:
        unified_tool: UnifiedTool from the tool registry
        db: Database session for fetching related data

    Returns:
        Dictionary matching ToolResponse schema with all fields populated
    """
    # If tool is from DB, fetch full details
    db_tool = None
    category = None
    mcp_server = None

    if unified_tool.db_id:
        db_tool = ToolsService.get_db_tool_by_id(db, str(unified_tool.db_id))

        # Fetch category if available
        if db_tool and db_tool.category_id:
            category_obj = ToolsService.get_category(db, str(db_tool.category_id))
            if category_obj:
                category = {
                    "id": int(str(category_obj.id).replace("-", "")[:16], 16) % (2**31),
                    "category_id": str(category_obj.id),
                    "name": category_obj.name,
                    "description": category_obj.description,
                    "icon": category_obj.icon,
                    "color": category_obj.color,
                    "created_at": category_obj.created_at.isoformat()
                    if hasattr(category_obj, "created_at") and category_obj.created_at
                    else None,
                    "updated_at": category_obj.updated_at.isoformat()
                    if hasattr(category_obj, "updated_at") and category_obj.updated_at
                    else None,
                }

        # Fetch MCP server if available
        if db_tool and db_tool.mcp_server_id:
            mcp_server_obj = db.exec(select(MCPServer).where(MCPServer.id == UUID_type(str(db_tool.mcp_server_id)))).first()
            if mcp_server_obj:
                mcp_server = {
                    "id": int(str(mcp_server_obj.id).replace("-", "")[:16], 16) % (2**31),
                    "server_id": str(mcp_server_obj.id),
                    "name": mcp_server_obj.name,
                    "description": mcp_server_obj.description,
                    "host": mcp_server_obj.host,
                    "port": mcp_server_obj.port,
                    "protocol": mcp_server_obj.protocol,
                    "status": mcp_server_obj.status,
                    "version": mcp_server_obj.version,
                }

    # Base response from unified tool
    response = {
        "id": int(str(unified_tool.db_id).replace("-", "")[:16], 16) % (2**31) if unified_tool.db_id else None,
        "tool_id": str(unified_tool.db_id) if unified_tool.db_id else None,
        "name": unified_tool.name,
        "display_name": db_tool.display_name if db_tool else None,
        "description": unified_tool.description,
        "version": unified_tool.version,
        "tool_type": db_tool.tool_type if db_tool else unified_tool.source,
        "execution_type": unified_tool.execution_type,
        "parameters_schema": unified_tool.parameters_schema,
        "return_schema": unified_tool.return_schema,
        "source": unified_tool.source,
        "uri": unified_tool.uri,
        "openai_schema": {
            "type": "function",
            "function": {
                "name": unified_tool.name,
                "description": unified_tool.description or f"Tool: {unified_tool.name}",
                "parameters": unified_tool.parameters_schema or {"type": "object", "properties": {}},
            },
        },
    }

    # Add DB-specific fields if available
    if db_tool:
        response.update(
            {
                "module_path": db_tool.module_path,
                "function_name": db_tool.function_name,
                "mcp_server_id": str(db_tool.mcp_server_id) if db_tool.mcp_server_id else None,
                "remote_name": db_tool.remote_name,
                "api_endpoint": db_tool.api_endpoint,
                "http_method": db_tool.http_method,
                "headers": db_tool.headers,
                "auth_required": db_tool.auth_required,
                "category_id": str(db_tool.category_id) if db_tool.category_id else None,
                "tags": db_tool.tags if isinstance(db_tool.tags, list) else [],
                "documentation": db_tool.documentation,
                "examples": db_tool.examples if isinstance(db_tool.examples, list) else [],
                "is_active": db_tool.is_active,
                "is_available": db_tool.is_available,
                "last_used": db_tool.last_used.isoformat() if db_tool.last_used else None,
                "usage_count": db_tool.usage_count,
                "created_at": db_tool.created_at.isoformat() if db_tool.created_at else None,
                "updated_at": db_tool.updated_at.isoformat() if db_tool.updated_at else None,
                "category": category,
                "mcp_server": mcp_server,
            }
        )
    else:
        # Default values for non-DB tools
        response.update(
            {
                "module_path": None,
                "function_name": None,
                "mcp_server_id": None,
                "remote_name": None,
                "api_endpoint": None,
                "http_method": None,
                "headers": None,
                "auth_required": False,
                "category_id": None,
                "tags": [],
                "documentation": None,
                "examples": None,
                "is_active": True,
                "is_available": True,
                "last_used": None,
                "usage_count": 0,
                "created_at": None,
                "updated_at": None,
                "category": None,
                "mcp_server": None,
            }
        )

    return response
