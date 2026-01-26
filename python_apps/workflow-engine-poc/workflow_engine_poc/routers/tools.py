"""
Tools API router: GET endpoints for tools and stubs for full CRUD including external registrations (MCP/RPC/API)
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import Session
from workflow_core_sdk.db.database import get_db_session
from workflow_core_sdk.db.models import (
    Tool,
    ToolCreate,
    ToolRead,
    ToolUpdate,
    ToolCategoryCreate,
    ToolCategoryRead,
    ToolCategoryUpdate,
    MCPServerCreate,
    MCPServerRead,
    MCPServerUpdate,
)
from workflow_core_sdk import tool_registry
from workflow_core_sdk.services.tools_service import ToolsService
from ..util import api_key_or_user_guard
from ..schemas import ToolStubUpdate

router = APIRouter(prefix="/tools", tags=["tools"])


# --------- Helper functions for ToolRead conversion ---------
def _tool_read_from_db(record: Tool) -> ToolRead:
    """Convert a DB Tool record to ToolRead."""
    return ToolRead(
        id=record.id,
        name=record.name,
        display_name=record.display_name,
        description=record.description,
        version=record.version,
        tool_type=record.tool_type,  # type: ignore[arg-type]
        execution_type=record.execution_type,  # type: ignore[arg-type]
        parameters_schema=record.parameters_schema
        or {"type": "object", "properties": {}, "required": []},
        return_schema=record.return_schema,
        module_path=record.module_path,
        function_name=record.function_name,
        mcp_server_id=record.mcp_server_id,
        remote_name=record.remote_name,
        api_endpoint=record.api_endpoint,
        http_method=record.http_method,  # type: ignore[arg-type]
        headers=record.headers,
        auth_required=record.auth_required,
        category_id=record.category_id,
        tags=record.tags or [],
        documentation=record.documentation,
        examples=record.examples,
        is_active=record.is_active,
        is_available=record.is_available,
        last_used=record.last_used,
        usage_count=record.usage_count,
        created_at=record.created_at,
        updated_at=record.updated_at,
        source="db",
        uri=f"db://{record.id}",
    )


def _tool_read_from_local(
    name: str, description: str, parameters: Dict[str, Any], source: str = "local"
) -> ToolRead:
    """Convert a local/registry tool to ToolRead."""
    now = datetime.now(timezone.utc)
    return ToolRead(
        id=uuid.uuid5(uuid.NAMESPACE_URL, f"{source}:{name}"),
        name=name,
        display_name=None,
        description=description,
        version="1.0.0",
        tool_type="local" if source == "local" else "mcp",  # type: ignore[arg-type]
        execution_type="function",  # type: ignore[arg-type]
        parameters_schema=parameters,
        return_schema=None,
        module_path=None,
        function_name=name,
        mcp_server_id=None,
        remote_name=None,
        api_endpoint=None,
        http_method=None,  # type: ignore[arg-type]
        headers=None,
        auth_required=False,
        category_id=None,
        tags=[],
        documentation=None,
        examples=None,
        is_active=True,
        is_available=True,
        last_used=None,
        usage_count=0,
        created_at=now,
        updated_at=now,
        source=source,
        uri=f"{source}://{name}",
    )


# --------- Read-only endpoints (available now) ---------
@router.get("/", response_model=List[ToolRead])
async def list_tools(
    q: Optional[str] = Query(default=None),
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_tool")),
):
    """Unified list of tools from DB + Local (+ MCP in future) as ToolRead objects.
    DB entries take precedence on name collisions. Includes source and uri fields.
    """
    unified = tool_registry.get_unified_tools(session)
    items: List[ToolRead] = []
    for ut in unified:
        if ut.source == "db" and ut.db_id is not None:
            db_record = ToolsService.get_db_tool_by_id(session, str(ut.db_id))
            if db_record:
                items.append(_tool_read_from_db(db_record))
                continue
        items.append(
            _tool_read_from_local(
                ut.name, ut.description, ut.parameters_schema, ut.source
            )
        )

    if q:
        ql = q.lower()
        items = [it for it in items if ql in (it.name or "").lower()]
    items.sort(key=lambda x: x.name or "")
    return items[offset : offset + limit]


# --------- Stubs for full CRUD and registration (future) ---------

# --------- DB-backed CRUD for Tools, Categories, MCP Servers ---------


# -- Tool CRUD --
@router.post("/db", response_model=ToolRead)
async def create_tool(
    tool: ToolCreate,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("create_tool")),
):
    try:
        return ToolsService.create_tool(session, tool)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/db", response_model=List[ToolRead])
async def list_db_tools(
    session: Session = Depends(get_db_session),
    q: Optional[str] = Query(default=None),
    limit: int = 100,
    offset: int = 0,
    _principal: str = Depends(api_key_or_user_guard("view_tool")),
):
    return ToolsService.list_db_tools(session, q=q, limit=limit, offset=offset)


@router.get("/db/{tool_id}", response_model=ToolRead)
async def get_db_tool(
    tool_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_tool")),
):
    tool = ToolsService.get_db_tool_by_id(session, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.patch("/db/{tool_id}", response_model=ToolRead)
async def update_db_tool(
    tool_id: str,
    payload: ToolUpdate,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("edit_tool")),
):
    try:
        _ = ToolsService.update_db_tool(session, tool_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail="Tool not found")
    return await get_db_tool(tool_id, session)


@router.delete("/db/{tool_id}")
async def delete_db_tool(
    tool_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("delete_tool")),
):
    ok = ToolsService.delete_db_tool(session, tool_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"deleted": True}


# -- Tool Category CRUD --
@router.post("/categories", response_model=ToolCategoryRead)
async def create_category(
    category: ToolCategoryCreate,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("create_tool_category")),
):
    try:
        return ToolsService.create_category(session, category)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/categories", response_model=List[ToolCategoryRead])
async def list_categories(
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_tool_category")),
):
    return ToolsService.list_categories(session)


@router.patch("/categories/{category_id}", response_model=ToolCategoryRead)
async def update_category(
    category_id: str,
    payload: ToolCategoryUpdate,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("edit_tool_category")),
):
    try:
        _ = ToolsService.update_category(session, category_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail="Category not found")
    return await get_category(category_id, session)


@router.get("/categories/{category_id}", response_model=ToolCategoryRead)
async def get_category(
    category_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_tool_category")),
):
    cat = ToolsService.get_category(session, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("delete_tool_category")),
):
    ok = ToolsService.delete_category(session, category_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"deleted": True}


# -- MCP Server CRUD --
@router.post("/mcp-servers", response_model=MCPServerRead)
async def create_mcp_server(
    server: MCPServerCreate,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("create_mcp_server")),
):
    try:
        return ToolsService.create_mcp_server(session, server)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/mcp-servers", response_model=List[MCPServerRead])
async def list_mcp_servers(
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_mcp_server")),
):
    return ToolsService.list_mcp_servers(session)


@router.get("/mcp-servers/{server_id}", response_model=MCPServerRead)
async def get_mcp_server(
    server_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_mcp_server")),
):
    server = ToolsService.get_mcp_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return server


@router.patch("/mcp-servers/{server_id}", response_model=MCPServerRead)
async def update_mcp_server(
    server_id: str,
    payload: MCPServerUpdate,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("edit_mcp_server")),
):
    try:
        _ = ToolsService.update_mcp_server(session, server_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return await get_mcp_server(server_id, session)


@router.delete("/mcp-servers/{server_id}")
async def delete_mcp_server(
    server_id: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("delete_mcp_server")),
):
    ok = ToolsService.delete_mcp_server(session, server_id)
    if not ok:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return {"deleted": True}


@router.post("/sync")
async def sync_tools(
    source: Optional[str] = Query(default="local"),
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("sync_tools")),
):
    """Idempotent sync of tools from a source into DB. Currently supports source=local."""
    if source != "local":
        raise HTTPException(status_code=400, detail="Only source=local is supported")
    result = tool_registry.sync_local_to_db(session)
    return {"source": source, **result}


# --------- Generic tool operations (catch-all routes - must be last) ---------


@router.get("/{tool_name}", response_model=ToolRead)
async def get_tool(
    tool_name: str,
    session: Session = Depends(get_db_session),
    _principal: str = Depends(api_key_or_user_guard("view_tool")),
):
    """Get a tool by name as ToolRead. Prefers DB; falls back to local registry."""
    # Prefer DB with enriched ToolRead
    db_tool = ToolsService.get_db_tool_by_name(session, tool_name)
    if db_tool:
        return _tool_read_from_db(db_tool)

    # Fallback to local via registry
    ut = tool_registry.get_tool_by_name(session, tool_name)
    if ut:
        return _tool_read_from_local(
            ut.name, ut.description, ut.parameters_schema, ut.source
        )

    raise HTTPException(status_code=404, detail="Tool not found")


@router.patch("/{tool_name}")
async def update_tool_stub(
    tool_name: str,
    body: ToolStubUpdate,
    _principal: str = Depends(api_key_or_user_guard("edit_tool")),
):
    """Stub for updating a tool."""
    return {
        "message": "Not implemented yet",
        "tool_name": tool_name,
        "request": body.model_dump(exclude_unset=True),
    }


@router.delete("/{tool_name}")
async def delete_tool_stub(
    tool_name: str,
    _principal: str = Depends(api_key_or_user_guard("delete_tool")),
):
    """Stub for deleting a tool."""
    return {"message": "Not implemented yet", "tool_name": tool_name}
