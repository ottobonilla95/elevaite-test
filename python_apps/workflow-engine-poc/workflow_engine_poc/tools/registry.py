"""
Unified Tool Registry for Workflow Engine POC

Aggregates tools from:
- Local provider (basic_tools)
- DB provider (Tool table)
- MCP provider (stub for now)

Provides unified listing and lookup, plus optional sync of local tools into DB.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass
from datetime import datetime, timezone
import uuid

from sqlmodel import Session, select

from ..db.models import Tool as DBTool, ToolCreate
from ..tools.basic_tools import get_all_tools, get_all_schemas

ToolSource = Literal["local", "db", "mcp"]


@dataclass
class UnifiedTool:
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    return_schema: Optional[Dict[str, Any]]
    execution_type: str
    version: str
    source: ToolSource
    uri: str
    # Optional DB linkage
    db_id: Optional[uuid.UUID] = None


class ToolRegistry:
    _instance: Optional["ToolRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # -------- Providers --------
    def _load_local(self) -> Dict[str, UnifiedTool]:
        tools = get_all_tools()  # name -> function
        schemas = get_all_schemas()  # name -> openai schema
        out: Dict[str, UnifiedTool] = {}
        for name, func in tools.items():
            schema = schemas.get(name) or {}
            func_block = schema.get("function", {}) if isinstance(schema, dict) else {}
            description = func_block.get("description", "")
            parameters = func_block.get("parameters", {"type": "object", "properties": {}, "required": []})
            uri = f"local://{func.__module__}:{getattr(func, '__name__', name)}"
            out[name] = UnifiedTool(
                name=name,
                description=description,
                parameters_schema=parameters,
                return_schema=None,
                execution_type="function",
                version="1.0.0",
                source="local",
                uri=uri,
            )
        return out

    def _load_db(self, session: Session) -> Dict[str, UnifiedTool]:
        records = session.exec(select(DBTool)).all()
        out: Dict[str, UnifiedTool] = {}
        for r in records:
            uri = f"db://{r.id}"
            out[r.name] = UnifiedTool(
                name=r.name,
                description=r.description,
                parameters_schema=r.parameters_schema or {"type": "object", "properties": {}, "required": []},
                return_schema=r.return_schema,
                execution_type=r.execution_type or "function",
                version=r.version or "1.0.0",
                source="db",
                uri=uri,
                db_id=r.id,
            )
        return out

    # Placeholder for future MCP provider. For now we rely on DB persistence of MCP tools if any.
    def _load_mcp(self, session: Session) -> Dict[str, UnifiedTool]:
        return {}

    # -------- Public API --------
    def get_unified_tools(self, session: Session) -> List[UnifiedTool]:
        db_map = self._load_db(session)
        local_map = self._load_local()
        mcp_map = self._load_mcp(session)

        # Merge by precedence: DB > Local > MCP (DB wins on collisions)
        merged: Dict[str, UnifiedTool] = {}
        # Start with local and mcp
        for name, ut in {**local_map, **mcp_map}.items():
            merged[name] = ut
        # Overlay DB entries
        for name, ut in db_map.items():
            merged[name] = ut
        return list(merged.values())

    def get_tool_by_name(self, session: Session, name: str) -> Optional[UnifiedTool]:
        # Prefer DB
        rec = session.exec(select(DBTool).where(DBTool.name == name)).first()
        if rec:
            return UnifiedTool(
                name=rec.name,
                description=rec.description,
                parameters_schema=rec.parameters_schema or {"type": "object", "properties": {}, "required": []},
                return_schema=rec.return_schema,
                execution_type=rec.execution_type or "function",
                version=rec.version or "1.0.0",
                source="db",
                uri=f"db://{rec.id}",
                db_id=rec.id,
            )
        # Fallback to local
        local = self._load_local()
        if name in local:
            return local[name]
        # MCP: none for now
        return None

    # Optional: sync local tools to DB with upsert semantics (by name+version)
    def sync_local_to_db(self, session: Session) -> Dict[str, int]:
        created = 0
        updated = 0
        local_map = self._load_local()
        for name, ut in local_map.items():
            _c, _u = self._upsert_local_tool(session, ut)
            created += _c
            updated += _u
        return {"created": created, "updated": updated}

    def sync_local_tool_by_name(self, session: Session, name: str) -> Optional[uuid.UUID]:
        """Ensure a single local tool exists in DB; return its id.
        Creates or updates the DB row as needed; returns None if the local tool is unknown.
        """
        local_map = self._load_local()
        ut = local_map.get(name)
        if not ut:
            return None
        created, _updated = self._upsert_local_tool(session, ut)
        # Fetch id
        rec = session.exec(select(DBTool).where(DBTool.name == name, DBTool.version == ut.version)).first()
        return getattr(rec, "id", None)

    # Internal helper
    def _upsert_local_tool(self, session: Session, ut: UnifiedTool) -> tuple[int, int]:
        existing = session.exec(select(DBTool).where(DBTool.name == ut.name, DBTool.version == ut.version)).first()
        if existing:
            changed = False
            if existing.description != ut.description:
                existing.description = ut.description
                changed = True
            if existing.parameters_schema != ut.parameters_schema:
                existing.parameters_schema = ut.parameters_schema
                changed = True
            if existing.execution_type != ut.execution_type:
                existing.execution_type = ut.execution_type
                changed = True
            if changed:
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return (0, 1)
            return (0, 0)
        create = ToolCreate(
            name=ut.name,
            description=ut.description,
            version=ut.version,
            tool_type="local",
            execution_type=ut.execution_type,
            parameters_schema=ut.parameters_schema,
            return_schema=ut.return_schema,
            module_path=None,
            function_name=ut.name,
            tags=[],
        )
        obj = DBTool(**create.model_dump())
        session.add(obj)
        session.commit()
        return (1, 0)


# Global singleton
tool_registry = ToolRegistry()
