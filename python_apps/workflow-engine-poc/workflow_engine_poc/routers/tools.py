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
from ..tools.registry import tool_registry


router = APIRouter(prefix="/tools", tags=["tools"])


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
            db_record = session.exec(select(Tool).where(Tool.id == ut.db_id)).first()
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
    db_tool = session.exec(select(Tool).where(Tool.name == tool_name)).first()
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
