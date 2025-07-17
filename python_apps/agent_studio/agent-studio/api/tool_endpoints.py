"""
Tool Management API endpoints for Agent Studio
Provides CRUD operations for tools, tool categories, and MCP servers
"""

import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db import crud, schemas
from db.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["tools"])


# Tool Category endpoints
@router.post("/categories", response_model=schemas.ToolCategoryResponse)
def create_tool_category(category: schemas.ToolCategoryCreate, db: Session = Depends(get_db)):
    """Create a new tool category."""
    # Check if category with same name already exists
    existing = crud.get_tool_category_by_name(db, category.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"Tool category with name '{category.name}' already exists")

    return crud.create_tool_category(db=db, category=category)


@router.get("/categories", response_model=List[schemas.ToolCategoryResponse])
def get_tool_categories(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000), db: Session = Depends(get_db)):
    """Get all tool categories."""
    return crud.get_tool_categories(db=db, skip=skip, limit=limit)


@router.get("/categories/{category_id}", response_model=schemas.ToolCategoryResponse)
def get_tool_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific tool category by ID."""
    category = crud.get_tool_category(db, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Tool category not found")
    return category


@router.put("/categories/{category_id}", response_model=schemas.ToolCategoryResponse)
def update_tool_category(category_id: uuid.UUID, category_update: schemas.ToolCategoryUpdate, db: Session = Depends(get_db)):
    """Update a tool category."""
    category = crud.update_tool_category(db, category_id, category_update)
    if not category:
        raise HTTPException(status_code=404, detail="Tool category not found")
    return category


@router.delete("/categories/{category_id}")
def delete_tool_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a tool category."""
    success = crud.delete_tool_category(db, category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tool category not found")
    return {"message": "Tool category deleted successfully"}


# MCP Server endpoints
@router.post("/mcp-servers", response_model=schemas.MCPServerResponse)
def create_mcp_server(server: schemas.MCPServerCreate, db: Session = Depends(get_db)):
    """Create a new MCP server registration."""
    # Check if server with same name already exists
    existing = crud.get_mcp_server_by_name(db, server.name)
    if existing:
        raise HTTPException(status_code=400, detail=f"MCP server with name '{server.name}' already exists")

    return crud.create_mcp_server(db=db, server=server)


@router.get("/mcp-servers", response_model=List[schemas.MCPServerResponse])
def get_mcp_servers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Get all MCP servers with optional status filtering."""
    return crud.get_mcp_servers(db=db, skip=skip, limit=limit, status=status)


@router.get("/mcp-servers/active", response_model=List[schemas.MCPServerResponse])
def get_active_mcp_servers(db: Session = Depends(get_db)):
    """Get all active MCP servers."""
    return crud.get_active_mcp_servers(db)


@router.get("/mcp-servers/{server_id}", response_model=schemas.MCPServerResponse)
def get_mcp_server(server_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific MCP server by ID."""
    server = crud.get_mcp_server(db, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return server


@router.put("/mcp-servers/{server_id}", response_model=schemas.MCPServerResponse)
def update_mcp_server(server_id: uuid.UUID, server_update: schemas.MCPServerUpdate, db: Session = Depends(get_db)):
    """Update an MCP server."""
    server = crud.update_mcp_server(db, server_id, server_update)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return server


@router.post("/mcp-servers/{server_id}/health")
def update_mcp_server_health(server_id: uuid.UUID, is_healthy: bool, db: Session = Depends(get_db)):
    """Update MCP server health status."""
    server = crud.update_mcp_server_health(db, server_id, is_healthy)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return {"message": "Health status updated", "status": server.status}


@router.delete("/mcp-servers/{server_id}")
def delete_mcp_server(server_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete an MCP server."""
    success = crud.delete_mcp_server(db, server_id)
    if not success:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return {"message": "MCP server deleted successfully"}


# MCP Server Self-Registration endpoint
@router.post("/mcp-servers/register", response_model=schemas.MCPServerResponse)
async def register_mcp_server(registration: schemas.MCPServerRegistration, db: Session = Depends(get_db)):
    """
    Self-registration endpoint for MCP servers.
    This allows MCP servers to register themselves on startup.
    """
    # Check if server already exists
    existing = crud.get_mcp_server_by_name(db, registration.name)
    if existing:
        # Update existing server
        server_update = schemas.MCPServerUpdate(
            description=registration.description,
            host=registration.host,
            port=registration.port,
            protocol=registration.protocol,
            endpoint=registration.endpoint,
            version=registration.version,
            capabilities=registration.capabilities,
            status="active",
        )
        server = crud.update_mcp_server(db, existing.server_id, server_update)
    else:
        # Create new server
        server_create = schemas.MCPServerCreate(
            name=registration.name,
            description=registration.description,
            host=registration.host,
            port=registration.port,
            protocol=registration.protocol,
            endpoint=registration.endpoint,
            version=registration.version,
            capabilities=registration.capabilities,
        )
        server = crud.create_mcp_server(db=db, server=server_create)

    # Register tools from the server if provided
    if registration.tools and server:
        from services.mcp_client import mcp_client

        try:
            # Register tools automatically
            registered_tools = await mcp_client.register_tools_from_server(server, db)
            logger.info(f"Registered {len(registered_tools)} tools from server {server.name}")
        except Exception as e:
            logger.error(f"Failed to register tools from server {server.name}: {e}")

    return server


# Tool endpoints
@router.post("/", response_model=schemas.ToolResponse)
def create_tool(tool: schemas.ToolCreate, db: Session = Depends(get_db)):
    """Create a new tool."""
    # Check if tool with same name and version already exists
    existing = crud.get_tool_by_name(db, tool.name, tool.version)
    if existing:
        raise HTTPException(status_code=400, detail=f"Tool '{tool.name}' version '{tool.version}' already exists")

    # Validate category exists if provided
    if tool.category_id:
        category = crud.get_tool_category(db, tool.category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Tool category not found")

    # Validate MCP server exists if provided
    if tool.mcp_server_id:
        server = crud.get_mcp_server(db, tool.mcp_server_id)
        if not server:
            raise HTTPException(status_code=400, detail="MCP server not found")

    return crud.create_tool(db=db, tool=tool)


@router.get("/", response_model=List[schemas.ToolResponse])
def get_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    tool_type: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_available: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """Get all tools with optional filtering."""
    return crud.get_tools(
        db=db,
        skip=skip,
        limit=limit,
        tool_type=tool_type,
        category_id=category_id,
        is_active=is_active,
        is_available=is_available,
    )


@router.get("/available", response_model=List[schemas.ToolResponse])
def get_available_tools(db: Session = Depends(get_db)):
    """Get all available tools (active and available)."""
    return crud.get_available_tools(db)


@router.get("/{tool_id}", response_model=schemas.ToolResponse)
def get_tool(tool_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific tool by ID."""
    tool = crud.get_tool(db, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.put("/{tool_id}", response_model=schemas.ToolResponse)
def update_tool(tool_id: uuid.UUID, tool_update: schemas.ToolUpdate, db: Session = Depends(get_db)):
    """Update a tool."""
    tool = crud.update_tool(db, tool_id, tool_update)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return tool


@router.delete("/{tool_id}")
def delete_tool(tool_id: uuid.UUID, db: Session = Depends(get_db)):
    """Delete a tool."""
    success = crud.delete_tool(db, tool_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"message": "Tool deleted successfully"}


# Tool execution endpoint (for testing and direct execution)
@router.post("/{tool_id}/execute", response_model=schemas.ToolExecutionResponse)
async def execute_tool(tool_id: uuid.UUID, execution_request: schemas.ToolExecutionRequest, db: Session = Depends(get_db)):
    """
    Execute a tool directly.
    Phase 2: Full implementation with local and MCP tool execution.
    """
    from services.tool_registry import tool_registry
    from datetime import datetime

    tool = crud.get_tool(db, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")

    if not tool.is_active or not tool.is_available:
        raise HTTPException(status_code=400, detail="Tool is not available for execution")

    try:
        # Execute the tool using the tool registry
        result = await tool_registry.execute_tool(tool_name=tool.name, parameters=execution_request.parameters, db=db)

        if result["status"] == "success":
            # Ensure result is a dictionary - wrap strings in a dict
            tool_result = result["result"]
            if isinstance(tool_result, str):
                tool_result = {"output": tool_result}
            elif not isinstance(tool_result, dict):
                tool_result = {"result": tool_result}

            return schemas.ToolExecutionResponse(
                status=result["status"],
                result=tool_result,
                execution_time_ms=result["execution_time_ms"],
                tool_id=tool_id,
                timestamp=datetime.fromisoformat(result["timestamp"]),
            )
        else:
            # Handle error case from tool registry
            return schemas.ToolExecutionResponse(
                status=result["status"],
                result={"error": result.get("error_message", "Unknown error")},
                execution_time_ms=result["execution_time_ms"],
                tool_id=tool_id,
                timestamp=datetime.fromisoformat(result["timestamp"]),
                error_message=result.get("error_message"),
            )

    except Exception as e:
        logger.error(f"Tool execution failed for {tool.name}: {e}")
        return schemas.ToolExecutionResponse(
            status="error",
            result={"error": str(e)},
            execution_time_ms=0,
            tool_id=tool_id,
            timestamp=datetime.now(),
            error_message=str(e),
        )
