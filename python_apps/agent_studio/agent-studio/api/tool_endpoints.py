"""
Tool registry endpoints for Agent Studio.

✅ FULLY MIGRATED TO SDK - Uses tool_registry.get_unified_tools()
All endpoints use workflow-core-sdk tool_registry for unified tool access.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

# SDK imports
from workflow_core_sdk.tools.registry import tool_registry
from workflow_core_sdk import ToolsService

# Database
from db.database import get_db
from db.schemas.tools import ToolResponse

# Adapters
from adapters.tool_adapter import unified_tool_to_response

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("/", response_model=List[ToolResponse])
def get_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    q: Optional[str] = None,
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    List all tools from the unified tool registry.

    ✅ MIGRATED TO SDK - Uses tool_registry.get_unified_tools()
    Returns tools from local registry, database, and MCP servers.
    """
    # Get all unified tools from registry
    unified_tools = tool_registry.get_unified_tools(db)

    # Apply search filter if provided
    if q:
        q_lower = q.lower()
        unified_tools = [
            t for t in unified_tools if q_lower in t.name.lower() or (t.description and q_lower in t.description.lower())
        ]

    # Apply pagination
    paginated_tools = unified_tools[skip : skip + limit]

    # Convert to full response format
    return [unified_tool_to_response(t, db) for t in paginated_tools]


@router.get("/available", response_model=List[ToolResponse])
def get_available_tools(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Get all available tools from the unified registry.

    ✅ MIGRATED TO SDK - Uses tool_registry.get_unified_tools()
    """
    unified_tools = tool_registry.get_unified_tools(db)

    # Convert to full response format
    return [unified_tool_to_response(t, db) for t in unified_tools]


@router.get("/by-name/{tool_name}", response_model=ToolResponse)
def get_tool_by_name(tool_name: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Get a specific tool by name from the unified registry.

    ✅ MIGRATED TO SDK - Uses tool_registry.get_tool_by_name()
    """
    unified_tool = tool_registry.get_tool_by_name(db, tool_name)

    if not unified_tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    return unified_tool_to_response(unified_tool, db)


@router.post("/sync-local")
def sync_local_tools(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Sync local tools to the database.

    ✅ MIGRATED TO SDK - Uses tool_registry.sync_local_to_db()
    """
    result = tool_registry.sync_local_to_db(db)
    return {
        "message": "Local tools synced to database",
        "created": result.get("created", 0),
        "updated": result.get("updated", 0),
    }


# Legacy/Not Implemented Endpoints


@router.post("/")
def create_tool(db: Session = Depends(get_db)) -> None:
    """
    NOT IMPLEMENTED: Tool creation via API.
    Tools should be registered via the unified registry or synced from local.
    """
    raise HTTPException(
        status_code=501, detail="Tool creation via API not implemented. Use POST /api/tools/sync-local to sync local tools."
    )


# Category endpoints - Simplified


@router.get("/categories", response_model=List[Dict[str, Any]])
def list_categories(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    List all tool categories.

    Returns a default category for now to keep frontend working.
    """
    # Try to get categories from DB, but return default if none exist
    try:
        categories = ToolsService.list_categories(db)
        if categories:
            # Apply pagination
            paginated = categories[skip : skip + limit]
            return [
                {
                    "id": str(cat.id),
                    "name": cat.name,
                    "description": cat.description,
                    "created_at": cat.created_at.isoformat() if cat.created_at else None,
                    "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
                }
                for cat in paginated
            ]
    except Exception:
        pass

    # Return default category to keep frontend working
    return [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "General",
            "description": "General purpose tools",
            "created_at": None,
            "updated_at": None,
        }
    ]


@router.get("/{tool_id}")
def get_tool(tool_id: str) -> None:
    """
    NOT IMPLEMENTED: Get tool by ID.
    Use GET /api/tools/by-name/{tool_name} instead.
    """
    raise HTTPException(
        status_code=501, detail="Get tool by ID not implemented. Use GET /api/tools/by-name/{tool_name} instead."
    )


@router.put("/{tool_id}")
def update_tool(tool_id: str) -> None:
    """
    NOT IMPLEMENTED: Update tool.
    """
    raise HTTPException(status_code=501, detail="Tool update not yet implemented.")


@router.delete("/{tool_id}")
def delete_tool(tool_id: str) -> None:
    """
    NOT IMPLEMENTED: Delete tool.
    """
    raise HTTPException(status_code=501, detail="Tool deletion not yet implemented.")


@router.post("/{tool_id}/execute")
def execute_tool(tool_id: str) -> None:
    """
    NOT IMPLEMENTED: Execute tool.
    Tool execution should be handled by the workflow engine.
    """
    raise HTTPException(status_code=501, detail="Tool execution not implemented. Tools are executed by the workflow engine.")


@router.post("/categories/")
def create_category() -> None:
    """
    NOT IMPLEMENTED: Create tool category.
    """
    raise HTTPException(status_code=501, detail="Tool category creation not yet implemented.")


# MCP Server endpoints - Simplified


@router.get("/mcp-servers/")
def list_mcp_servers() -> None:
    """
    NOT IMPLEMENTED: List MCP servers.
    """
    raise HTTPException(status_code=501, detail="MCP server management not yet implemented.")


@router.post("/mcp-servers/")
def create_mcp_server() -> None:
    """
    NOT IMPLEMENTED: Create MCP server.
    """
    raise HTTPException(status_code=501, detail="MCP server management not yet implemented.")
