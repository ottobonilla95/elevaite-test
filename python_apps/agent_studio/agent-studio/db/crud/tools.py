import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from ..models import Tool, ToolCategory, MCPServer
from ..schemas import (
    ToolCreate,
    ToolUpdate,
    ToolCategoryCreate,
    ToolCategoryUpdate,
    MCPServerCreate,
    MCPServerUpdate,
)


def create_tool_category(db: Session, category: ToolCategoryCreate) -> ToolCategory:
    db_category = ToolCategory(
        name=category.name,
        description=category.description,
        icon=category.icon,
        color=category.color,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_tool_category(db: Session, category_id: uuid.UUID) -> Optional[ToolCategory]:
    return (
        db.query(ToolCategory).filter(ToolCategory.category_id == category_id).first()
    )


def get_tool_category_by_name(db: Session, name: str) -> Optional[ToolCategory]:
    return db.query(ToolCategory).filter(ToolCategory.name == name).first()


def get_tool_categories(
    db: Session, skip: int = 0, limit: int = 100
) -> List[ToolCategory]:
    return db.query(ToolCategory).offset(skip).limit(limit).all()


def update_tool_category(
    db: Session, category_id: uuid.UUID, category_update: ToolCategoryUpdate
) -> Optional[ToolCategory]:
    db_category = get_tool_category(db, category_id)
    if not db_category:
        return None

    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

    db_category.updated_at = datetime.now()
    db.commit()
    db.refresh(db_category)
    return db_category


def delete_tool_category(db: Session, category_id: uuid.UUID) -> bool:
    db_category = get_tool_category(db, category_id)
    if not db_category:
        return False

    db.delete(db_category)
    db.commit()
    return True


def create_mcp_server(db: Session, server: MCPServerCreate) -> MCPServer:
    db_server = MCPServer(
        name=server.name,
        description=server.description,
        host=server.host,
        port=server.port,
        protocol=server.protocol,
        endpoint=server.endpoint,
        auth_type=server.auth_type,
        auth_config=server.auth_config,
        version=server.version,
        capabilities=server.capabilities,
        tags=server.tags,
        health_check_interval=server.health_check_interval,
    )
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server


def get_mcp_server(db: Session, server_id: uuid.UUID) -> Optional[MCPServer]:
    return db.query(MCPServer).filter(MCPServer.server_id == server_id).first()


def get_mcp_server_by_name(db: Session, name: str) -> Optional[MCPServer]:
    return db.query(MCPServer).filter(MCPServer.name == name).first()


def get_mcp_servers(
    db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None
) -> List[MCPServer]:
    query = db.query(MCPServer)
    if status:
        query = query.filter(MCPServer.status == status)
    return query.offset(skip).limit(limit).all()


def get_active_mcp_servers(db: Session) -> List[MCPServer]:
    return db.query(MCPServer).filter(MCPServer.status == "active").all()


def update_mcp_server(
    db: Session, server_id: uuid.UUID, server_update: MCPServerUpdate
) -> Optional[MCPServer]:
    db_server = get_mcp_server(db, server_id)
    if not db_server:
        return None

    update_data = server_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_server, key, value)

    db_server.updated_at = datetime.now()
    db.commit()
    db.refresh(db_server)
    return db_server


def delete_mcp_server(db: Session, server_id: uuid.UUID) -> bool:
    db_server = get_mcp_server(db, server_id)
    if not db_server:
        return False

    db.delete(db_server)
    db.commit()
    return True


def update_mcp_server_health(
    db: Session, server_id: uuid.UUID, is_healthy: bool
) -> Optional[MCPServer]:
    db_server = get_mcp_server(db, server_id)
    if not db_server:
        return None

    db_server.last_health_check = datetime.now()
    if is_healthy:
        db_server.consecutive_failures = 0
        db_server.last_seen = datetime.now()
        if db_server.status == "error":
            db_server.status = "active"
    else:
        db_server.consecutive_failures += 1
        if db_server.consecutive_failures >= 3:
            db_server.status = "error"

    db.commit()
    db.refresh(db_server)
    return db_server


def create_tool(db: Session, tool: ToolCreate) -> Tool:
    db_tool = Tool(
        name=tool.name,
        display_name=tool.display_name,
        description=tool.description,
        version=tool.version,
        tool_type=tool.tool_type,
        execution_type=tool.execution_type,
        parameters_schema=tool.parameters_schema,
        return_schema=tool.return_schema,
        module_path=tool.module_path,
        function_name=tool.function_name,
        mcp_server_id=tool.mcp_server_id,
        remote_name=tool.remote_name,
        api_endpoint=tool.api_endpoint,
        http_method=tool.http_method,
        headers=tool.headers,
        auth_required=tool.auth_required,
        category_id=tool.category_id,
        tags=tool.tags,
        documentation=tool.documentation,
        examples=tool.examples,
    )
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return db_tool


def get_tool(db: Session, tool_id: uuid.UUID) -> Optional[Tool]:
    return db.query(Tool).filter(Tool.tool_id == tool_id).first()


def get_tool_by_name(
    db: Session, name: str, version: Optional[str] = None
) -> Optional[Tool]:
    query = db.query(Tool).filter(Tool.name == name)
    if version:
        query = query.filter(Tool.version == version)
    return query.first()


def get_tools(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    is_available: Optional[bool] = None,
    tool_type: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
) -> List[Tool]:
    query = db.query(Tool)
    if is_active is not None:
        query = query.filter(Tool.is_active == is_active)
    if is_available is not None:
        query = query.filter(Tool.is_available == is_available)
    if tool_type:
        query = query.filter(Tool.tool_type == tool_type)
    if category_id:
        query = query.filter(Tool.category_id == category_id)
    return query.offset(skip).limit(limit).all()


def get_tools_by_category(db: Session, category_id: uuid.UUID) -> List[Tool]:
    return db.query(Tool).filter(Tool.category_id == category_id).all()


def get_tools_by_mcp_server(db: Session, mcp_server_id: uuid.UUID) -> List[Tool]:
    return db.query(Tool).filter(Tool.mcp_server_id == mcp_server_id).all()


def get_available_tools(db: Session) -> List[Tool]:
    return (
        db.query(Tool).filter(Tool.is_active == True, Tool.is_available == True).all()
    )


def update_tool(
    db: Session, tool_id: uuid.UUID, tool_update: ToolUpdate
) -> Optional[Tool]:
    db_tool = get_tool(db, tool_id)
    if not db_tool:
        return None

    update_data = tool_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tool, key, value)

    db_tool.updated_at = datetime.now()
    db.commit()
    db.refresh(db_tool)
    return db_tool


def delete_tool(db: Session, tool_id: uuid.UUID) -> bool:
    db_tool = get_tool(db, tool_id)
    if not db_tool:
        return False

    db.delete(db_tool)
    db.commit()
    return True


def update_tool_usage_stats(
    db: Session,
    tool_id: uuid.UUID,
    success: bool,
    execution_time_ms: Optional[float] = None,
) -> Optional[Tool]:
    db_tool = get_tool(db, tool_id)
    if not db_tool:
        return None

    db_tool.usage_count += 1
    db_tool.last_used = datetime.now()

    # Only update success/error counts if the attributes exist (graceful handling)
    if hasattr(db_tool, 'success_count') and hasattr(db_tool, 'error_count'):
        if success:
            db_tool.success_count += 1
        else:
            db_tool.error_count += 1

    # Only update average execution time if the attribute exists
    if hasattr(db_tool, 'average_execution_time_ms') and execution_time_ms is not None:
        if db_tool.average_execution_time_ms is None:
            db_tool.average_execution_time_ms = execution_time_ms
        else:
            total_time = (
                db_tool.average_execution_time_ms * (db_tool.usage_count - 1)
                + execution_time_ms
            )
            db_tool.average_execution_time_ms = total_time / db_tool.usage_count

    db.commit()
    db.refresh(db_tool)
    return db_tool
