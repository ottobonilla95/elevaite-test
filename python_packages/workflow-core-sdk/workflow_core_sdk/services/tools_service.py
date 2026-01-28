from __future__ import annotations

from typing import Optional, List
from uuid import UUID as UUID_type

from sqlmodel import Session, select

from ..db.models import (
    Tool,
    ToolCreate,
    ToolUpdate,
    ToolCategory,
    ToolCategoryCreate,
    ToolCategoryUpdate,
    MCPServer,
    MCPServerCreate,
    MCPServerUpdate,
)


class ToolsService:
    """Encapsulate DB operations for Tools, Categories, and MCP Servers."""

    # ---- Tool helpers ----
    @staticmethod
    def get_db_tool_by_id(session: Session, tool_id: str) -> Optional[Tool]:
        return session.exec(select(Tool).where(Tool.id == UUID_type(tool_id))).first()

    @staticmethod
    def get_db_tool_by_name(session: Session, name: str) -> Optional[Tool]:
        return session.exec(select(Tool).where(Tool.name == name)).first()

    @staticmethod
    def create_tool(session: Session, payload: ToolCreate) -> Tool:
        existing = session.exec(
            select(Tool).where(
                Tool.name == payload.name, Tool.version == payload.version
            )
        ).first()
        if existing:
            raise ValueError("Tool with this name and version already exists")
        db_tool = Tool(**payload.model_dump())
        session.add(db_tool)
        session.commit()
        session.refresh(db_tool)
        return db_tool

    @staticmethod
    def list_db_tools(
        session: Session, *, q: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Tool]:
        query = select(Tool)
        tools = session.exec(query.offset(offset).limit(limit)).all()
        if q:
            ql = q.lower()
            tools = [t for t in tools if ql in (t.name or "").lower()]
        return tools

    @staticmethod
    def update_db_tool(session: Session, tool_id: str, payload: ToolUpdate) -> Tool:
        db_tool = ToolsService.get_db_tool_by_id(session, tool_id)
        if not db_tool:
            raise LookupError("Tool not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(db_tool, k, v)
        session.add(db_tool)
        session.commit()
        session.refresh(db_tool)
        return db_tool

    @staticmethod
    def delete_db_tool(session: Session, tool_id: str) -> bool:
        db_tool = ToolsService.get_db_tool_by_id(session, tool_id)
        if not db_tool:
            return False
        session.delete(db_tool)
        session.commit()
        return True

    # ---- Categories ----
    @staticmethod
    def create_category(session: Session, payload: ToolCategoryCreate) -> ToolCategory:
        existing = session.exec(
            select(ToolCategory).where(ToolCategory.name == payload.name)
        ).first()
        if existing:
            raise ValueError("Category with this name already exists")
        db_cat = ToolCategory(**payload.model_dump())
        session.add(db_cat)
        session.commit()
        session.refresh(db_cat)
        return db_cat

    @staticmethod
    def list_categories(session: Session) -> List[ToolCategory]:
        return session.exec(select(ToolCategory)).all()

    @staticmethod
    def get_category(session: Session, category_id: str) -> Optional[ToolCategory]:
        return session.exec(
            select(ToolCategory).where(ToolCategory.id == UUID_type(category_id))
        ).first()

    @staticmethod
    def update_category(
        session: Session, category_id: str, payload: ToolCategoryUpdate
    ) -> ToolCategory:
        db_cat = ToolsService.get_category(session, category_id)
        if not db_cat:
            raise LookupError("Category not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(db_cat, k, v)
        session.add(db_cat)
        session.commit()
        session.refresh(db_cat)
        return db_cat

    @staticmethod
    def delete_category(session: Session, category_id: str) -> bool:
        db_cat = ToolsService.get_category(session, category_id)
        if not db_cat:
            return False
        session.delete(db_cat)
        session.commit()
        return True

    # ---- MCP Servers ----
    @staticmethod
    def create_mcp_server(session: Session, payload: MCPServerCreate) -> MCPServer:
        existing = session.exec(
            select(MCPServer).where(MCPServer.name == payload.name)
        ).first()
        if existing:
            raise ValueError("MCP server with this name already exists")
        db_server = MCPServer(**payload.model_dump())
        session.add(db_server)
        session.commit()
        session.refresh(db_server)
        return db_server

    @staticmethod
    def list_mcp_servers(session: Session) -> List[MCPServer]:
        return session.exec(select(MCPServer)).all()

    @staticmethod
    def get_mcp_server(session: Session, server_id: str) -> Optional[MCPServer]:
        return session.exec(
            select(MCPServer).where(MCPServer.id == UUID_type(server_id))
        ).first()

    @staticmethod
    def update_mcp_server(
        session: Session, server_id: str, payload: MCPServerUpdate
    ) -> MCPServer:
        db_server = ToolsService.get_mcp_server(session, server_id)
        if not db_server:
            raise LookupError("MCP server not found")
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(db_server, k, v)
        session.add(db_server)
        session.commit()
        session.refresh(db_server)
        return db_server

    @staticmethod
    def delete_mcp_server(session: Session, server_id: str) -> bool:
        db_server = ToolsService.get_mcp_server(session, server_id)
        if not db_server:
            return False
        session.delete(db_server)
        session.commit()
        return True
