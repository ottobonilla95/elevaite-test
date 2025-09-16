"""
Tools API router: GET endpoints for tools and stubs for full CRUD including external registrations (MCP/RPC/API)
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import Session
from ..db.database import get_db_session
from ..db.models import (
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
from ..tools.registry import tool_registry
from ..services.tools_service import ToolsService


router = APIRouter(prefix="/tools", tags=["tools"])
if TYPE_CHECKING:
    from ..db.models import Tool  # for type hints only


# --------- Read-only endpoints (available now) ---------
@router.get("/", response_model=List[ToolRead])
async def list_tools(
    q: Optional[str] = Query(default=None),
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session),
):
    """Unified list of tools from DB + Local (+ MCP in future) as ToolRead objects.
    DB entries take precedence on name collisions. Includes source and uri fields.
    """

    def to_tool_read_from_db(record: Tool) -> ToolRead:
        return ToolRead(
            id=record.id,
            name=record.name,
            display_name=record.display_name,
            description=record.description,
            version=record.version,
            tool_type=record.tool_type,  # type: ignore[arg-type]
            execution_type=record.execution_type,  # type: ignore[arg-type]
            parameters_schema=record.parameters_schema or {"type": "object", "properties": {}, "required": []},
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

    def to_tool_read_local(name: str, description: str, parameters: Dict[str, Any]) -> ToolRead:
        now = datetime.now(timezone.utc)
        return ToolRead(
            id=uuid.uuid5(uuid.NAMESPACE_URL, f"local:{name}"),
            name=name,
            display_name=None,
            description=description,
            version="1.0.0",
            tool_type="local",  # type: ignore[arg-type]
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
            source="local",
            uri=f"local://{name}",
        )

    unified = tool_registry.get_unified_tools(session)
    items: List[ToolRead] = []
    for ut in unified:
        if ut.source == "db" and ut.db_id is not None:
            db_record = ToolsService.get_db_tool_by_id(session, str(ut.db_id))
            if db_record:
                items.append(to_tool_read_from_db(db_record))
                continue
        items.append(to_tool_read_local(ut.name, ut.description, ut.parameters_schema))

    if q:
        ql = q.lower()
        items = [it for it in items if ql in (it.name or "").lower()]
    items.sort(key=lambda x: x.name or "")
    items = items[offset : offset + limit]
    return items


@router.get("/{tool_name}", response_model=ToolRead)
async def get_tool(tool_name: str, session: Session = Depends(get_db_session)):
    """Get a tool by name as ToolRead. Prefers DB; falls back to local registry."""
    # Prefer DB with enriched ToolRead
    db_tool = ToolsService.get_db_tool_by_name(session, tool_name)
    if db_tool:
        return ToolRead(
            id=db_tool.id,
            name=db_tool.name,
            display_name=db_tool.display_name,
            description=db_tool.description,
            version=db_tool.version,
            tool_type=db_tool.tool_type,  # type: ignore[arg-type]
            execution_type=db_tool.execution_type,  # type: ignore[arg-type]
            parameters_schema=db_tool.parameters_schema or {"type": "object", "properties": {}, "required": []},
            return_schema=db_tool.return_schema,
            module_path=db_tool.module_path,
            function_name=db_tool.function_name,
            mcp_server_id=db_tool.mcp_server_id,
            remote_name=db_tool.remote_name,
            api_endpoint=db_tool.api_endpoint,
            http_method=db_tool.http_method,  # type: ignore[arg-type]
            headers=db_tool.headers,
            auth_required=db_tool.auth_required,
            category_id=db_tool.category_id,
            tags=db_tool.tags or [],
            documentation=db_tool.documentation,
            examples=db_tool.examples,
            is_active=db_tool.is_active,
            is_available=db_tool.is_available,
            last_used=db_tool.last_used,
            usage_count=db_tool.usage_count,
            created_at=db_tool.created_at,
            updated_at=db_tool.updated_at,
            source="db",
            uri=f"db://{db_tool.id}",
        )

    # Fallback to local via registry
    ut = tool_registry.get_tool_by_name(session, tool_name)
    if ut:
        now = datetime.now(timezone.utc)
        return ToolRead(
            id=uuid.uuid5(uuid.NAMESPACE_URL, f"{ut.source}:{ut.name}"),
            name=ut.name,
            display_name=None,
            description=ut.description,
            version=ut.version,
            tool_type=("local" if ut.source == "local" else "mcp"),  # type: ignore[arg-type]
            execution_type=ut.execution_type,  # type: ignore[arg-type]
            parameters_schema=ut.parameters_schema,
            return_schema=ut.return_schema,
            module_path=None,
            function_name=ut.name,
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
            source=ut.source,
            uri=ut.uri,
        )

    raise HTTPException(status_code=404, detail="Tool not found")


# --------- Stubs for full CRUD and registration (future) ---------

# --------- DB-backed CRUD for Tools, Categories, MCP Servers ---------


# -- Tool CRUD --
@router.post("/db", response_model=ToolRead)
async def create_tool(tool: ToolCreate, session: Session = Depends(get_db_session)):
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
):
    return ToolsService.list_db_tools(session, q=q, limit=limit, offset=offset)


@router.get("/db/{tool_id}", response_model=ToolRead)
async def get_db_tool(tool_id: str, session: Session = Depends(get_db_session)):
    tool = ToolsService.get_db_tool_by_id(session, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.patch("/db/{tool_id}", response_model=ToolRead)
async def update_db_tool(tool_id: str, payload: ToolUpdate, session: Session = Depends(get_db_session)):
    try:
        _ = ToolsService.update_db_tool(session, tool_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail="Tool not found")
    return await get_db_tool(tool_id, session)


@router.delete("/db/{tool_id}")
async def delete_db_tool(tool_id: str, session: Session = Depends(get_db_session)):
    ok = ToolsService.delete_db_tool(session, tool_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"deleted": True}


# -- Tool Category CRUD --
@router.post("/categories", response_model=ToolCategoryRead)
async def create_category(category: ToolCategoryCreate, session: Session = Depends(get_db_session)):
    try:
        return ToolsService.create_category(session, category)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/categories", response_model=List[ToolCategoryRead])
async def list_categories(session: Session = Depends(get_db_session)):
    return ToolsService.list_categories(session)


@router.patch("/categories/{category_id}", response_model=ToolCategoryRead)
async def update_category(category_id: str, payload: ToolCategoryUpdate, session: Session = Depends(get_db_session)):
    try:
        _ = ToolsService.update_category(session, category_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail="Category not found")
    return await get_category(category_id, session)


@router.get("/categories/{category_id}", response_model=ToolCategoryRead)
async def get_category(category_id: str, session: Session = Depends(get_db_session)):
    cat = ToolsService.get_category(session, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, session: Session = Depends(get_db_session)):
    ok = ToolsService.delete_category(session, category_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"deleted": True}


# -- MCP Server CRUD --
@router.post("/mcp-servers", response_model=MCPServerRead)
async def create_mcp_server(server: MCPServerCreate, session: Session = Depends(get_db_session)):
    try:
        return ToolsService.create_mcp_server(session, server)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/mcp-servers", response_model=List[MCPServerRead])
async def list_mcp_servers(session: Session = Depends(get_db_session)):
    return ToolsService.list_mcp_servers(session)


@router.get("/mcp-servers/{server_id}", response_model=MCPServerRead)
async def get_mcp_server(server_id: str, session: Session = Depends(get_db_session)):
    server = ToolsService.get_mcp_server(session, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return server


@router.patch("/mcp-servers/{server_id}", response_model=MCPServerRead)
async def update_mcp_server(server_id: str, payload: MCPServerUpdate, session: Session = Depends(get_db_session)):
    try:
        _ = ToolsService.update_mcp_server(session, server_id, payload)
    except LookupError:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return await get_mcp_server(server_id, session)


@router.delete("/mcp-servers/{server_id}")
async def delete_mcp_server(server_id: str, session: Session = Depends(get_db_session)):
    ok = ToolsService.delete_mcp_server(session, server_id)
    if not ok:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return {"deleted": True}


@router.post("/sync")
async def sync_tools(source: Optional[str] = Query(default="local"), session: Session = Depends(get_db_session)):
    """Idempotent sync of tools from a source into DB. Currently supports source=local."""
    if source != "local":
        raise HTTPException(status_code=400, detail="Only source=local is supported")
    result = tool_registry.sync_local_to_db(session)
    return {"source": source, **result}


@router.patch("/{tool_name}")
async def update_tool_stub(tool_name: str, body: Dict[str, Any]):
    """Stub for updating a tool."""
    return {"message": "Not implemented yet", "tool_name": tool_name, "request": body}


@router.delete("/{tool_name}")
async def delete_tool_stub(tool_name: str):
    """Stub for deleting a tool."""
    return {"message": "Not implemented yet", "tool_name": tool_name}
