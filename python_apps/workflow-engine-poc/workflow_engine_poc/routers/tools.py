"""
Tools API router: GET endpoints for tools and stubs for full CRUD including external registrations (MCP/RPC/API)
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import Session, select
from ..db.database import get_db_session
from ..db.models import (
    Tool,
    ToolCreate,
    ToolRead,
    ToolUpdate,
    ToolCategory,
    ToolCategoryCreate,
    ToolCategoryRead,
    ToolCategoryUpdate,
    MCPServer,
    MCPServerCreate,
    MCPServerRead,
    MCPServerUpdate,
)
from ..tools import get_all_tools, get_tool_schema


router = APIRouter(prefix="/tools", tags=["tools"])


# --------- Read-only endpoints (available now) ---------
@router.get("/", response_model=List[ToolRead])
async def list_tools(
    q: Optional[str] = Query(default=None),
    limit: int = 100,
    offset: int = 0,
    session: Session = Depends(get_db_session),
):
    """List all tools (DB + in-process) as ToolRead objects.
    DB entries take precedence on name collisions.
    """

    # Helper: DB item -> return as-is (FastAPI/SQLModel will serialize to ToolRead)
    def to_tool_read_db(t: Tool):
        return t

    # Helper: convert registry -> ToolRead (synthetic)
    def to_tool_read_registry(name: str, schema: Dict[str, Any]) -> ToolRead:
        now = datetime.now(timezone.utc)
        func = (schema or {}).get("function", {})
        description = func.get("description", "")
        parameters = func.get("parameters", {"type": "object", "properties": {}, "required": []})
        return ToolRead(
            id=uuid.uuid5(uuid.NAMESPACE_URL, f"registry:{name}"),
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
        )

    # Build DB map by name
    db_tools = session.exec(select(Tool)).all()
    by_name: Dict[str, Tool | ToolRead] = {t.name: to_tool_read_db(t) for t in db_tools}

    # Add registry tools not already in the union map
    reg_tools = get_all_tools()
    for name in reg_tools.keys():
        if name not in by_name:
            by_name[name] = to_tool_read_registry(name, get_tool_schema(name) or {})

    # Filter, sort, paginate
    items_union = list(by_name.values())
    # Normalize to ToolRead using FastAPI coercion by returning mixed list is okay,
    # but to satisfy typing we convert DB Tool objects with model_validate.
    items: List[ToolRead] = [it if isinstance(it, ToolRead) else ToolRead.model_validate(it) for it in items_union]
    if q:
        ql = q.lower()
        items = [it for it in items if ql in (it.name or "").lower()]
    items.sort(key=lambda x: x.name or "")
    items = items[offset : offset + limit]
    return items


@router.get("/{tool_name}", response_model=ToolRead)
async def get_tool(tool_name: str, session: Session = Depends(get_db_session)):
    """Get a tool by name as ToolRead. Prefers DB; falls back to registry."""
    # Prefer DB
    db_tool = session.exec(select(Tool).where(Tool.name == tool_name)).first()
    if db_tool:
        return db_tool

    # Fallback to registry
    tools = get_all_tools()
    if tool_name in tools:
        schema = get_tool_schema(tool_name) or {}
        # build synthetic ToolRead
        func = (schema or {}).get("function", {})
        description = func.get("description", "")
        parameters = func.get("parameters", {"type": "object", "properties": {}, "required": []})
        now = datetime.now(timezone.utc)
        return ToolRead(
            id=uuid.uuid5(uuid.NAMESPACE_URL, f"registry:{tool_name}"),
            name=tool_name,
            display_name=None,
            description=description,
            version="1.0.0",
            tool_type="local",  # type: ignore[arg-type]
            execution_type="function",  # type: ignore[arg-type]
            parameters_schema=parameters,
            return_schema=None,
            module_path=None,
            function_name=tool_name,
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
        )

    raise HTTPException(status_code=404, detail="Tool not found")


# --------- Stubs for full CRUD and registration (future) ---------

# --------- DB-backed CRUD for Tools, Categories, MCP Servers ---------


# -- Tool CRUD --
@router.post("/db", response_model=ToolRead)
async def create_tool(tool: ToolCreate, session: Session = Depends(get_db_session)):
    # Uniqueness by (name, version)
    existing = session.exec(select(Tool).where(Tool.name == tool.name, Tool.version == tool.version)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Tool with this name and version already exists")
    db_tool = Tool(**tool.model_dump())
    session.add(db_tool)
    session.commit()
    session.refresh(db_tool)
    return db_tool


@router.get("/db", response_model=List[ToolRead])
async def list_db_tools(
    session: Session = Depends(get_db_session),
    q: Optional[str] = Query(default=None),
    limit: int = 100,
    offset: int = 0,
):
    query = select(Tool)
    if q:
        # basic filter by name substring match (portable)
        tools = session.exec(query.offset(offset).limit(limit)).all()
        tools = [t for t in tools if q.lower() in (t.name or "").lower()]
    else:
        tools = session.exec(query.offset(offset).limit(limit)).all()
    return tools


@router.get("/db/{tool_id}", response_model=ToolRead)
async def get_db_tool(tool_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    tool = session.exec(select(Tool).where(Tool.id == UUID(tool_id))).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.patch("/db/{tool_id}", response_model=ToolRead)
async def update_db_tool(tool_id: str, payload: ToolUpdate, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_tool = session.exec(select(Tool).where(Tool.id == UUID(tool_id))).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(db_tool, k, v)
    session.add(db_tool)
    session.commit()
    session.refresh(db_tool)
    return await get_db_tool(tool_id, session)


@router.delete("/db/{tool_id}")
async def delete_db_tool(tool_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_tool = session.exec(select(Tool).where(Tool.id == UUID(tool_id))).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    session.delete(db_tool)
    session.commit()
    return {"deleted": True}


# -- Tool Category CRUD --
@router.post("/categories", response_model=ToolCategoryRead)
async def create_category(category: ToolCategoryCreate, session: Session = Depends(get_db_session)):
    existing = session.exec(select(ToolCategory).where(ToolCategory.name == category.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Category with this name already exists")
    db_cat = ToolCategory(**category.model_dump())
    session.add(db_cat)
    session.commit()
    session.refresh(db_cat)
    return db_cat


@router.get("/categories", response_model=List[ToolCategoryRead])
async def list_categories(session: Session = Depends(get_db_session)):
    cats = session.exec(select(ToolCategory)).all()
    return cats


@router.patch("/categories/{category_id}", response_model=ToolCategoryRead)
async def update_category(category_id: str, payload: ToolCategoryUpdate, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_cat = session.exec(select(ToolCategory).where(ToolCategory.id == UUID(category_id))).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(db_cat, k, v)
    session.add(db_cat)
    session.commit()
    session.refresh(db_cat)
    return await get_category(category_id, session)


@router.get("/categories/{category_id}", response_model=ToolCategoryRead)
async def get_category(category_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    cat = session.exec(select(ToolCategory).where(ToolCategory.id == UUID(category_id))).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.delete("/categories/{category_id}")
async def delete_category(category_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_cat = session.exec(select(ToolCategory).where(ToolCategory.id == UUID(category_id))).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(db_cat)
    session.commit()
    return {"deleted": True}


# -- MCP Server CRUD --
@router.post("/mcp-servers", response_model=MCPServerRead)
async def create_mcp_server(server: MCPServerCreate, session: Session = Depends(get_db_session)):
    existing = session.exec(select(MCPServer).where(MCPServer.name == server.name)).first()
    if existing:
        raise HTTPException(status_code=409, detail="MCP server with this name already exists")
    db_server = MCPServer(**server.model_dump())
    session.add(db_server)
    session.commit()
    session.refresh(db_server)
    return db_server


@router.get("/mcp-servers", response_model=List[MCPServerRead])
async def list_mcp_servers(session: Session = Depends(get_db_session)):
    servers = session.exec(select(MCPServer)).all()
    return servers


@router.get("/mcp-servers/{server_id}", response_model=MCPServerRead)
async def get_mcp_server(server_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    server = session.exec(select(MCPServer).where(MCPServer.id == UUID(server_id))).first()
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return server


@router.patch("/mcp-servers/{server_id}", response_model=MCPServerRead)
async def update_mcp_server(server_id: str, payload: MCPServerUpdate, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_server = session.exec(select(MCPServer).where(MCPServer.id == UUID(server_id))).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(db_server, k, v)
    session.add(db_server)
    session.commit()
    session.refresh(db_server)
    return await get_mcp_server(server_id, session)


@router.delete("/mcp-servers/{server_id}")
async def delete_mcp_server(server_id: str, session: Session = Depends(get_db_session)):
    from uuid import UUID

    db_server = session.exec(select(MCPServer).where(MCPServer.id == UUID(server_id))).first()
    if not db_server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    session.delete(db_server)
    session.commit()
    return {"deleted": True}


@router.post("/")
async def create_tool_stub(body: Dict[str, Any]):
    """Stub for creating a tool (local/remote/mcp/api)."""
    return {"message": "Not implemented yet", "request": body}


@router.patch("/{tool_name}")
async def update_tool_stub(tool_name: str, body: Dict[str, Any]):
    """Stub for updating a tool."""
    return {"message": "Not implemented yet", "tool_name": tool_name, "request": body}


@router.delete("/{tool_name}")
async def delete_tool_stub(tool_name: str):
    """Stub for deleting a tool."""
    return {"message": "Not implemented yet", "tool_name": tool_name}


# MCP server management stubs
@router.post("/mcp-servers/register")
async def register_mcp_server_stub(body: Dict[str, Any]):
    """Stub for MCP server self-registration."""
    return {"message": "Not implemented yet", "request": body}


@router.get("/mcp-servers")
async def list_mcp_servers_stub():
    return {"message": "Not implemented yet", "servers": []}


@router.get("/mcp-servers/active")
async def list_active_mcp_servers_stub():
    return {"message": "Not implemented yet", "servers": []}


@router.get("/mcp-servers/{server_id}")
async def get_mcp_server_stub(server_id: str):
    return {"message": "Not implemented yet", "server_id": server_id}


@router.patch("/mcp-servers/{server_id}")
async def update_mcp_server_stub(server_id: str, body: Dict[str, Any]):
    return {"message": "Not implemented yet", "server_id": server_id, "request": body}


@router.delete("/mcp-servers/{server_id}")
async def delete_mcp_server_stub(server_id: str):
    return {"message": "Not implemented yet", "server_id": server_id}
