"""
AI and LLM Processing Steps

Steps that integrate with AI models and language models for
intelligent processing, agent execution, and AI-powered workflows.
"""

import uuid
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
import logging

# Import tools system
from llm_gateway.a2a.client import A2AClientService
from llm_gateway.a2a.types import A2AAgentInfo, A2AAuthConfig, A2AMessageRequest
from workflow_core_sdk.db.service import DatabaseService
from workflow_core_sdk.tools.basic_tools import get_tool_by_name as get_tool_function
from ..db.database import get_db_session
from ..utils import decrypt_if_encrypted
from workflow_core_sdk import AgentsService

# DB access for dynamic agent tools
from sqlmodel import select
from workflow_core_sdk.db.models import (
    Agent as DBAgent,
    Prompt as DBPrompt,
    AgentToolBinding as DBAgentToolBinding,
    Tool as DBTool,
)

from workflow_core_sdk.execution_context import ExecutionContext

# Streaming utilities
from workflow_core_sdk.execution.streaming import stream_manager, create_step_event

# Import llm-gateway components
from llm_gateway.services import TextGenerationService
from llm_gateway.models.text_generation.core.interfaces import TextGenerationModelName

# Initialize logger first
logger = logging.getLogger(__name__)

MAX_AGENT_RECURSION_DEPTH = 5
LLM_GATEWAY_AVAILABLE = True

# -------- DB helper: load DB-defined tools for an agent and convert to OpenAI tool schemas --------


def load_agent_db_tool_schemas(agent_id: Optional[str] = None, agent_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return OpenAI-compatible tool schemas for tools bound to the given agent.

    - Looks up the agent by UUID or name
    - Resolves AgentToolBinding rows, joins Tool rows
    - Converts Tool.parameters_schema to OpenAI tool schema
    """
    try:
        session = get_db_session()
    except Exception:
        return []

    try:
        from uuid import UUID as _UUID

        agent_obj: Optional[DBAgent] = None
        if agent_id:
            try:
                agent_obj = session.exec(select(DBAgent).where(DBAgent.id == _UUID(str(agent_id)))).first()
            except Exception:
                agent_obj = None
        if not agent_obj and agent_name:
            agent_obj = session.exec(select(DBAgent).where(DBAgent.name == agent_name)).first()
        if not agent_obj:
            return []

        # Fetch bindings
        bindings = session.exec(select(DBAgentToolBinding).where(DBAgentToolBinding.agent_id == agent_obj.id)).all()
        tool_ids = [b.tool_id for b in bindings]
        if not tool_ids:
            return []
        db_tools = session.exec(select(DBTool).where(DBTool.id.in_(tool_ids))).all()  # type: ignore[attr-defined]

        schemas: List[Dict[str, Any]] = []
        for t in db_tools:
            # Convert DB Tool into OpenAI-style function schema
            params = t.parameters_schema or {"type": "object", "properties": {}}
            schemas.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or f"Tool {t.name}",
                        "parameters": params if isinstance(params, dict) else {"type": "object", "properties": {}},
                    },
                }
            )
        return schemas
    except Exception as e:
        logger.warning(f"Failed to load DB tools for agent {agent_id or agent_name}: {e}")
        return []


# -------- Helper: resolve tool schemas by names from local registry and DB --------


def resolve_tool_schemas_by_names(tool_names: List[str]) -> List[Dict[str, Any]]:
    """Resolve a mixed list of tool names into OpenAI-compatible tool schemas.
    - First try local/basic tools
    - Then try DB Tool entries by name
    """
    resolved: List[Dict[str, Any]] = []
    if not tool_names:
        return resolved

    # Try local registry
    from ..tools import get_tool_schema as _get_tool_schema

    remaining: List[str] = []
    for n in tool_names:
        sch = _get_tool_schema(n)
        if sch:
            resolved.append(sch)
        else:
            remaining.append(n)

    if not remaining:
        return resolved

    # Try DB Tools by name
    try:
        session = get_db_session()
    except Exception:
        return resolved

    try:
        db_tools = session.exec(select(DBTool).where(DBTool.name.in_(remaining))).all()  # type: ignore[attr-defined]
        for t in db_tools:
            params = t.parameters_schema or {"type": "object", "properties": {}}
            resolved.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description or f"Tool {t.name}",
                        "parameters": params if isinstance(params, dict) else {"type": "object", "properties": {}},
                    },
                }
            )
    except Exception as e:
        logger.debug(f"Failed resolving DB tools by names {remaining}: {e}")

    return resolved


# ---------------------------------------------------------------------------
# AgentStep helper functions
# ---------------------------------------------------------------------------


def _get_provider_config(context: Optional[Dict[str, Any]]) -> Tuple[Dict[str, str], str]:
    """Resolve provider config and model name from context or use defaults.
    Returns (provider_config, model_name).
    """
    agent_provider_type = context.get("_agent_provider_type") if isinstance(context, dict) else None
    agent_provider_config = context.get("_agent_provider_config") if isinstance(context, dict) else None

    if agent_provider_type and agent_provider_config:
        config = {"type": agent_provider_type}
        model_name_from_config = agent_provider_config.get("model_name", "gpt-4o")
        try:
            model_enum = getattr(TextGenerationModelName, f"OPENAI_{model_name_from_config.replace('-', '_')}", None)
            model_name = model_enum.value if model_enum else model_name_from_config  # type: ignore
        except Exception:
            model_name = model_name_from_config
        return config, model_name

    # Default: OpenAI GPT-4o
    return {"type": "openai_textgen"}, TextGenerationModelName.OPENAI_gpt_4o.value  # type: ignore


def _persist_message(
    context: Optional[Dict[str, Any]],
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Persist a message to the database if context has required IDs."""
    if not context or not isinstance(context, dict):
        return
    execution_id = context.get("_execution_id")
    step_id = context.get("_step_id")
    if not execution_id or not step_id:
        return
    try:
        from ..db.service import DatabaseService
        from ..db.database import get_db_session

        session = get_db_session()
        try:
            DatabaseService().create_agent_message(
                session,
                execution_id=execution_id,
                step_id=step_id,
                role=role,
                content=content,
                metadata=metadata or {},
                user_id=context.get("_user_id"),
                session_id=context.get("_session_id"),
            )
        finally:
            try:
                session.close()
            except Exception:
                pass
    except Exception as e:
        logger.debug(f"Could not persist {role} message: {e}")


async def _emit_tool_event(
    context: Optional[Dict[str, Any]],
    event_type: str,
    data: Dict[str, Any],
) -> None:
    """Emit a tool-related event (tool_call, tool_response, agent_call) via stream_manager."""
    if not context or not isinstance(context, dict):
        return
    execution_id = context.get("_execution_id")
    step_id = context.get("_step_id")
    workflow_id = context.get("_workflow_id")
    if not execution_id or not step_id:
        return
    try:
        evt = create_step_event(
            execution_id=execution_id,
            step_id=step_id,
            step_status="running",
            workflow_id=workflow_id,
            output_data={"event_type": event_type, **data},
        )
        await stream_manager.emit_execution_event(evt)
        if workflow_id:
            await stream_manager.emit_workflow_event(evt)
    except Exception as e:
        logger.warning(f"Failed to emit {event_type} event: {e}")


def _extract_tool_call_info(tc: Any) -> Tuple[str, str, Dict[str, Any]]:
    """Extract (id, name, arguments) from a tool call object.

    Handles both our ToolCall class (tc.name, tc.arguments) and OpenAI raw
    format (tc.function.name, tc.function.arguments).
    """
    # Get id
    tc_id = getattr(tc, "id", None) or getattr(tc, "tool_call_id", None) or str(uuid.uuid4())

    # Get name - prefer direct, fall back to .function
    fn_name = getattr(tc, "name", None)
    if fn_name is None and hasattr(tc, "function"):
        fn_name = getattr(tc.function, "name", None)

    # Get arguments - prefer direct, fall back to .function
    fn_args = getattr(tc, "arguments", None)
    if fn_args is None and hasattr(tc, "function"):
        fn_args = getattr(tc.function, "arguments", None)

    # Normalize to dict
    if isinstance(fn_args, str):
        try:
            fn_args = json.loads(fn_args)
        except Exception:
            fn_args = {}
    fn_args = fn_args or {}

    return tc_id, fn_name or "unknown", fn_args


class AgentStep:
    """
    Simplified agent that can execute queries with optional tools.
    Uses llm-gateway for real LLM integration when available.
    """

    def __init__(
        self,
        name: str = "Assistant",
        system_prompt: str = "You are a helpful assistant.",
        tools: Optional[List[Dict[str, Any]]] = None,
        force_real_llm: bool = True,
        connected_agents: Optional[List[Union[str, Dict[str, Any]]]] = None,  # IDs/names or dicts with {id/name, tools}
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.force_real_llm = force_real_llm
        self.agent_id = str(uuid.uuid4())
        self._connected_agent_specs: List[Union[str, Dict[str, Any]]] = connected_agents or []
        # Derived refs list for DB lookups
        refs: List[str] = []
        for spec in self._connected_agent_specs:
            if isinstance(spec, str):
                refs.append(spec)
            elif isinstance(spec, dict):
                v = spec.get("id") or spec.get("name")
                if isinstance(v, str):
                    refs.append(v)
        self._connected_agent_refs: List[str] = refs

        # Initialize LLM service; must be available
        if not LLM_GATEWAY_AVAILABLE:
            raise RuntimeError("llm-gateway is required but not available")
        try:
            self.llm_service = TextGenerationService()  # type: ignore
            logger.info(f"Agent {name} created with LLM gateway")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM service: {e}") from e

        # Dynamic per-agent tools registry for this AgentStep instance
        self._dynamic_agent_tools: Dict[str, Dict[str, Any]] = {}
        self._recursion_depth: int = 0

    async def _load_connected_agents(self, context: Optional[Dict[str, Any]]) -> List[DBAgent]:
        """Fetch explicitly connected agents from DB based on this agent's configuration.
        connected_agents may be a list of UUID strings or agent names.
        Optional scoping (e.g., organization) can still be applied if desired.
        """
        refs = self._connected_agent_refs or []
        if not refs:
            return []
        try:
            session = get_db_session()
        except Exception:
            return []
        try:
            from uuid import UUID as _UUID

            id_uuids = []
            names = []
            for r in refs:
                try:
                    id_uuids.append(_UUID(str(r)))
                except Exception:
                    names.append(str(r))

            results: List[DBAgent] = []
            if id_uuids:
                q1 = select(DBAgent).where(DBAgent.id.in_(id_uuids))  # type: ignore[attr-defined]
                results.extend(session.exec(q1).all())
            if names:
                q2 = select(DBAgent).where(DBAgent.name.in_(names))  # type: ignore[attr-defined]
                results.extend(session.exec(q2).all())

            # Deduplicate by id
            seen = set()
            unique: List[DBAgent] = []
            for a in results:
                aid = getattr(a, "id", None)
                if aid and aid not in seen:
                    seen.add(aid)
                    unique.append(a)
            return unique
        except Exception as e:
            logger.warning(f"Failed to load connected agents: {e}")
            return []

    def _build_agent_tool_schema(self, agent: DBAgent) -> Dict[str, Any]:
        """Create an OpenAI-compatible tool schema for invoking a specific agent."""
        # Support optional per-connection tool list: if caller provided a dict spec with tools
        allowed_tool_names: Optional[List[str]] = None
        for spec in self._connected_agent_specs:
            if isinstance(spec, dict):
                v = spec.get("id") or spec.get("name")
                if str(v) == str(agent.id) or str(v) == (agent.name or ""):
                    tnames = spec.get("tools")
                    if isinstance(tnames, list) and all(isinstance(x, str) for x in tnames):
                        allowed_tool_names = tnames  # explicit override for this connected agent
                        break

        parameters_properties: Dict[str, Any] = {
            "query": {"type": "string", "description": "User query for the target agent"},
            "context": {"type": "object", "description": "Optional context to pass to the target agent"},
        }
        if allowed_tool_names is not None:
            parameters_properties["allowed_tools"] = {
                "type": "array",
                "items": {"type": "string"},
                "description": "Restrict tool access for the target agent to this list (names)",
            }

        return {
            "type": "function",
            "function": {
                "name": f"call_agent_{str(agent.id).replace('-', '')}",
                "description": agent.description or f"Call agent {agent.name}",
                "parameters": {
                    "type": "object",
                    "properties": parameters_properties,
                    "required": ["query"],
                },
            },
        }

    async def _ensure_dynamic_agent_tools(self, context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate per-agent tools at runtime and cache them for this AgentStep."""
        if self._dynamic_agent_tools:
            return [meta["schema"] for meta in self._dynamic_agent_tools.values()]
        agents = await self._load_connected_agents(context)
        for agent in list(agents or []):
            tool_schema = self._build_agent_tool_schema(agent)
            tool_name = tool_schema["function"]["name"]
            self._dynamic_agent_tools[tool_name] = {
                "schema": tool_schema,
                "agent": agent,
            }
        return [meta["schema"] for meta in self._dynamic_agent_tools.values()]

    def _get_local_tool_schemas_for_agent(self, agent: DBAgent) -> List[Dict[str, Any]]:  # noqa: ARG002
        """Deprecated: local fallback removed. Return empty list to disable implicit tools."""
        return []

    async def _invoke_agent(self, target_agent: DBAgent, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Invoke another agent with recursion protection and prompt loading."""
        if self._recursion_depth >= MAX_AGENT_RECURSION_DEPTH:
            raise RuntimeError(f"Max agent recursion depth {MAX_AGENT_RECURSION_DEPTH} reached")

        # Load system prompt text
        prompt_text = "You are a helpful assistant."
        try:
            session = get_db_session()
            prompt = session.get(DBPrompt, target_agent.system_prompt_id)
            if prompt and getattr(prompt, "prompt", None):
                prompt_text = prompt.prompt
        except Exception as e:
            logger.warning(f"Failed to load prompt for agent {target_agent.id}: {e}")

        # Determine allowed tools and nested connections for this agent invocation
        allowed_tool_names: Optional[List[str]] = None
        nested_connected_agents: Optional[List[Union[str, Dict[str, Any]]]] = None
        for spec in self._connected_agent_specs:
            if isinstance(spec, dict):
                v = spec.get("id") or spec.get("name")
                if str(v) == str(target_agent.id) or str(v) == (target_agent.name or ""):
                    tnames = spec.get("tools")
                    if isinstance(tnames, list) and all(isinstance(x, str) for x in tnames):
                        allowed_tool_names = tnames
                    nca = spec.get("connected_agents")
                    if isinstance(nca, list):
                        nested_connected_agents = nca  # forward nested connections
                    break

        # Create a child AgentStep with appropriate tools
        # Always use DB-bound tools; if allowed_tool_names is provided, restrict to that subset
        child_db_tools = load_agent_db_tool_schemas(agent_id=str(target_agent.id))
        if allowed_tool_names is not None:
            allowed_set = set(allowed_tool_names)
            filtered: List[Dict[str, Any]] = []
            for sch in child_db_tools:
                try:
                    fn = sch.get("function", {}) if isinstance(sch, dict) else {}
                    nm = fn.get("name")
                    if nm in allowed_set:
                        filtered.append(sch)
                except Exception:
                    continue
            child_tools = filtered
        else:
            child_tools = child_db_tools

        child = AgentStep(
            name=target_agent.name,
            system_prompt=prompt_text,
            tools=child_tools,
            force_real_llm=self.force_real_llm,
            connected_agents=nested_connected_agents,
        )
        child._recursion_depth = self._recursion_depth + 1
        return await child.execute(query, context=context or {})

    async def execute(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a query with the agent (must use real LLM; no simulation)."""
        start_time = datetime.now()

        try:
            result = await self._execute_with_llm(query, context)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "query": query,
                "response": result.get("response", ""),
                "tool_calls": result.get("tool_calls", []),
                "execution_time_seconds": execution_time,
                "timestamp": end_time.isoformat(),
                "success": True,
                "mode": result.get("mode", "llm"),
                # Bubble up usage and model when available
                "model": result.get("model"),
                "usage": result.get("usage"),
            }

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "query": query,
                "error": str(e),
                "execution_time_seconds": execution_time,
                "timestamp": end_time.isoformat(),
                "success": False,
                "mode": "error",
            }

    async def _execute_with_llm(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute query using real LLM through llm-gateway"""
        if self.llm_service is None:
            raise Exception("No LLM Service configured.")
        try:
            sys_msg = self.system_prompt or ""
            ctx_messages = (context or {}).get("messages") or (context or {}).get("chat_history") or []
            messages = _build_messages(sys_msg, ctx_messages, query)

            # Prepare tools
            dynamic_tools = await self._ensure_dynamic_agent_tools(context)
            llm_tools = list(self.tools or []) + list(dynamic_tools)
            llm_tools = llm_tools or None
            logger.info(f"🔧 Tools: explicit={len(self.tools or [])}, dynamic={len(dynamic_tools)}")

            # Provider config
            config, model_name = _get_provider_config(context)
            provider_type, model_label = str(config.get("type", "unknown")), str(model_name)
            # Prepare tools: merge explicit tools with dynamic per-agent tools
            dynamic_agent_tools = await self._ensure_dynamic_agent_tools(context)
            explicit_tools = self.tools or []
            # If neither explicit tools nor dynamic agent tools are provided, pass None (no tools)
            llm_tools = None
            if explicit_tools:
                llm_tools = list(explicit_tools)
            if dynamic_agent_tools:
                llm_tools = (llm_tools or []) + list(dynamic_agent_tools)

            # Use agent's provider config from context if available, otherwise default to OpenAI GPT-4o
            agent_provider_type = context.get("_agent_provider_type") if isinstance(context, dict) else None
            agent_provider_config = context.get("_agent_provider_config") if isinstance(context, dict) else None

            if agent_provider_type and agent_provider_config:
                config = {"type": agent_provider_type}
                model_name_from_config = agent_provider_config.get("model_name", "gpt-4o")
                # Map model name to TextGenerationModelName enum
                try:
                    # Try to find matching enum value
                    model_name = getattr(TextGenerationModelName, f"OPENAI_{model_name_from_config.replace('-', '_')}", None)
                    if model_name:
                        model_name = model_name.value  # type: ignore
                    else:
                        # Fallback to string if enum not found
                        model_name = model_name_from_config
                        logger.info(f"Using model name as string (not in enum): {model_name}")
                except Exception as e:
                    logger.warning(f"Failed to map model name to enum: {e}, using string: {model_name_from_config}")
                    model_name = model_name_from_config
                logger.info(f"Using agent provider config: {agent_provider_type}, model: {model_name}")
            else:
                # Default provider config
                config = {"type": "openai_textgen"}
                # Use GPT-4o as default
                model_name = TextGenerationModelName.OPENAI_gpt_4o.value  # type: ignore
                logger.info("Using default provider config: openai_textgen, model: gpt-4o")

            # Multi-turn tool loop with a small cap
            tool_calls_trace: List[Dict[str, Any]] = []
            max_tool_iterations = 4

            # Token usage accumulation
            tokens_in_total = 0
            tokens_out_total = 0
            llm_calls = 0
            provider_type = str(config.get("type", "unknown"))
            model_label = str(model_name)

            # Extract file paths for file search (OpenAI only)
            files_for_search: Optional[List[str]] = None
            attachment = (context or {}).get("_attachment") if isinstance(context, dict) else None
            if isinstance(attachment, dict) and attachment.get("path"):
                files_for_search = [attachment["path"]]
                logger.debug(f"Passing file to LLM for file search: {attachment.get('name')}")

            for iteration_num in range(max_tool_iterations):
                # TextGenerationService is synchronous; run in a thread to avoid blocking
                # Respect optional llm params from context; provide sensible defaults
                _llm = (context or {}).get("_llm_params", {}) if isinstance(context, dict) else {}
                _max_tokens = _llm.get("max_tokens")
                if not isinstance(_max_tokens, int) or _max_tokens <= 0:
                    _max_tokens = 4096  # increased to support large tool call arguments
                _temperature = _llm.get("temperature")
                _response_format = _llm.get("response_format")

                # Only pass files on first iteration (files are uploaded once to vector store)
                files_arg = files_for_search if iteration_num == 0 else None

            # Multi-turn tool loop
            tool_calls_trace: List[Dict[str, Any]] = []
            tokens_in_total, tokens_out_total, llm_calls = 0, 0, 0
            base_prompt = f"{json.dumps(context, indent=2)}\n\nUser query: {query}" if context else query

            for _ in range(4):  # max iterations
                response = await asyncio.to_thread(
                    self.llm_service.generate,
                    base_prompt,
                    config,
                    _max_tokens,
                    model_name,
                    sys_msg,
                    None,
                    _temperature,
                    llm_tools,
                    "auto" if llm_tools else None,
                    messages,
                    _response_format,
                    files_arg,
                )

                # === DEBUG: Log raw LLM response structure ===
                logger.info(f"[LLM_RESPONSE_DEBUG] Response type: {type(response)}")
                logger.info(f"[LLM_RESPONSE_DEBUG] Response repr: {repr(response)}")
                if hasattr(response, "model_dump"):
                    try:
                        logger.info(f"[LLM_RESPONSE_DEBUG] response.model_dump(): {response.model_dump()}")
                    except Exception as dump_err:
                        logger.info(f"[LLM_RESPONSE_DEBUG] model_dump() failed: {dump_err}")
                logger.info(f"[LLM_RESPONSE_DEBUG] response.tool_calls: {getattr(response, 'tool_calls', 'NO_ATTR')}")
                logger.info(f"[LLM_RESPONSE_DEBUG] response.text: {getattr(response, 'text', 'NO_ATTR')}")
                logger.info(f"[LLM_RESPONSE_DEBUG] response.finish_reason: {getattr(response, 'finish_reason', 'NO_ATTR')}")

                # Accumulate token usage
                try:
                    tokens_in_total += int(getattr(response, "tokens_in", 0) or 0)
                    tokens_out_total += int(getattr(response, "tokens_out", 0) or 0)
                    llm_calls += 1
                except Exception:
                    pass

                # Final answer if no tool calls
                if not getattr(response, "tool_calls", None):
                    return {
                        "response": getattr(response, "text", str(response)) or "",
                        "tool_calls": tool_calls_trace,
                        "mode": "llm",
                        "model": {"provider": provider_type, "name": model_label},
                        "usage": {
                            "tokens_in": tokens_in_total,
                            "tokens_out": tokens_out_total,
                            "total_tokens": tokens_in_total + tokens_out_total,
                            "llm_calls": llm_calls,
                        },
                    }

                # Build assistant message with tool_calls
                assistant_message: Dict[str, Any] = {"role": "assistant", "tool_calls": []}
                for tc in response.tool_calls or []:
                    tc_id, fn_name, fn_args = _extract_tool_call_info(tc)
                    args_str = json.dumps(fn_args) if isinstance(fn_args, dict) else str(fn_args)
                    assistant_message["tool_calls"].append(
                        {"id": tc_id, "type": "function", "function": {"name": fn_name, "arguments": args_str}}
                    )
                messages.append(assistant_message)

                # Persist assistant message with tool_calls to database
                try:
                    if context and isinstance(context, dict):
                        execution_id = context.get("_execution_id")
                        step_id = context.get("_step_id")
                        user_id = context.get("_user_id")
                        session_id = context.get("_session_id")
                        if execution_id and step_id and assistant_message.get("content"):
                            from ..db.service import DatabaseService
                            from ..db.database import get_db_session

                            dbs = DatabaseService()
                            session = get_db_session()
                            try:
                                dbs.create_agent_message(
                                    session,
                                    execution_id=execution_id,
                                    step_id=step_id,
                                    role="assistant",
                                    content=str(assistant_message["content"]),
                                    metadata={"tool_calls": assistant_message.get("tool_calls", [])},
                                    user_id=user_id,
                                    session_id=session_id,
                                )
                            finally:
                                try:
                                    session.close()
                                except Exception:
                                    pass
                except Exception as persist_err:
                    logger.debug(f"Could not persist assistant message with tool_calls: {persist_err}")

                # Execute tool calls and add proper tool response messages
                logger.info(f"[TOOL_CALL_DEBUG] response.tool_calls type: {type(response.tool_calls)}")
                logger.info(f"[TOOL_CALL_DEBUG] response.tool_calls value: {response.tool_calls}")
                for idx, tool_call in enumerate(response.tool_calls or []):
                    logger.info(f"[TOOL_CALL_DEBUG] Processing tool_call[{idx}] from response.tool_calls")
                    try:
                        tool_result = await self._execute_tool_call(tc, context=context)
                        tool_calls_trace.append(tool_result)
                        res_val = tool_result.get("result")
                        if tool_result.get("success"):
                            content = (
                                res_val.get("response")
                                if isinstance(res_val, dict) and res_val.get("response")
                                else (res_val if isinstance(res_val, str) else json.dumps(res_val) if res_val else "")
                            )
                        else:
                            content = f"Error: {tool_result.get('error', 'Unknown error')}"
                    except Exception as e:
                        tool_calls_trace.append({"tool_name": fn_name, "success": False, "error": str(e)[:400]})
                        content = f"Error: {e}"

                    messages.append({"role": "tool", "tool_call_id": tc_id, "content": content})
                    _persist_message(context, "tool", str(content), {"tool_call_id": tc_id, "tool_name": fn_name})

            # Max iterations reached
            return {
                "response": "Reached tool iteration limit; see tool_calls for details.",
                "tool_calls": tool_calls_trace,
                "mode": "llm",
                "model": {"provider": provider_type, "name": model_label},
                "usage": {
                    "tokens_in": tokens_in_total,
                    "tokens_out": tokens_out_total,
                    "total_tokens": tokens_in_total + tokens_out_total,
                    "llm_calls": llm_calls,
                },
            }

        except Exception as e:
            logger.error(f"LLM execution failed: {e}")
            raise

    async def _execute_tool_call(self, tool_call, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a tool call from either OpenAI-style or llm-gateway ToolCall
        - Supports both tool_call.name/arguments and tool_call.function.name/arguments
        - Arguments may be dicts or JSON strings
        - Supports both sync and async tool functions
        """
        import time
        function_args = None

        try:
            # === DETAILED LOGGING FOR DEBUGGING TOOL CALL STRUCTURE ===
            logger.info(f"[TOOL_CALL_DEBUG] Raw tool_call type: {type(tool_call)}")
            logger.info(f"[TOOL_CALL_DEBUG] Raw tool_call repr: {repr(tool_call)}")

            # Log all attributes of the tool_call object
            if hasattr(tool_call, "__dict__"):
                logger.info(f"[TOOL_CALL_DEBUG] tool_call.__dict__: {tool_call.__dict__}")
            if hasattr(tool_call, "model_dump"):
                try:
                    logger.info(f"[TOOL_CALL_DEBUG] tool_call.model_dump(): {tool_call.model_dump()}")
                except Exception as dump_err:
                    logger.info(f"[TOOL_CALL_DEBUG] model_dump() failed: {dump_err}")

            # Check if it's a dict (common issue)
            if isinstance(tool_call, dict):
                logger.info(f"[TOOL_CALL_DEBUG] tool_call is a dict with keys: {tool_call.keys()}")
                # Handle dict format directly
                function_name = tool_call.get("name") or (tool_call.get("function", {}) or {}).get("name")
                function_args = tool_call.get("arguments") or (tool_call.get("function", {}) or {}).get("arguments")
                logger.info(f"[TOOL_CALL_DEBUG] Extracted from dict - name: {function_name}, args type: {type(function_args)}")
            else:
                # Extract function name and args from multiple possible shapes
                function_name = getattr(tool_call, "name", None)
                function_args = getattr(tool_call, "arguments", None)
                logger.info(f"[TOOL_CALL_DEBUG] Direct attrs - name: {function_name}, args: {function_args}")

                if function_name is None and hasattr(tool_call, "function"):
                    func_obj = getattr(tool_call, "function", None)
                    logger.info(f"[TOOL_CALL_DEBUG] Has 'function' attr, type: {type(func_obj)}, value: {func_obj}")
                    if isinstance(func_obj, dict):
                        function_name = func_obj.get("name")
                        function_args = func_obj.get("arguments")
                    else:
                        function_name = getattr(func_obj, "name", None)
                        function_args = getattr(func_obj, "arguments", None)
                    logger.info(f"[TOOL_CALL_DEBUG] From function attr - name: {function_name}, args: {function_args}")

            # Log final extracted values
            logger.info(f"[TOOL_CALL_DEBUG] Final function_name: {function_name}, function_args type: {type(function_args)}")

            # Normalize arguments: allow JSON string or dict; default to {}
            if isinstance(function_args, str):
                try:
                    function_args = json.loads(function_args)
                except Exception as e:
                    raise ValueError(f"Invalid JSON in tool arguments: {e}")
            function_args = function_args or {}

            if not function_name:
                logger.warning(f"[TOOL_CALL_DEBUG] Skipping tool call with missing function name: {tool_call}")
                return {
                    "tool_name": None,
                    "arguments": function_args,
                    "result": "Error: Tool call missing function name",
                    "success": False,
                    "error": "Tool call missing function name",
                    "tool_call_id": getattr(tool_call, "id", None) or getattr(tool_call, "tool_call_id", None),
                }

            # Resolve either a dynamic agent tool or a registered function tool
            dynamic_meta = self._dynamic_agent_tools.get(function_name)
            start_time = time.time()

            # Check for dynamic agent tool first
            dynamic_meta = self._dynamic_agent_tools.get(function_name)
            if dynamic_meta:
                target_agent: DBAgent = dynamic_meta["agent"]
                query = function_args.get("query") or function_args.get("input") or ""
                child_context = function_args.get("context") if isinstance(function_args.get("context"), dict) else {}

                await _emit_tool_event(
                    context, "agent_call", {"agent_name": target_agent.name, "query": query, "arguments": function_args}
                )
                result = await self._invoke_agent(target_agent, query=query, context=child_context)

                # Emit tool_response event
                try:
                    if context and isinstance(context, dict):
                        execution_id = context.get("_execution_id")
                        workflow_id = context.get("_workflow_id")
                        step_id = context.get("_step_id")
                        if execution_id and step_id:
                            tool_response_event = create_step_event(
                                execution_id=execution_id,
                                step_id=step_id,
                                step_status="running",
                                workflow_id=workflow_id,
                                output_data={
                                    "event_type": "tool_response",
                                    "agent_name": target_agent.name,
                                    "response": result.get("response") if isinstance(result, dict) else str(result),
                                    "duration_ms": duration_ms,
                                },
                            )
                            await stream_manager.emit_execution_event(tool_response_event)
                            if workflow_id:
                                await stream_manager.emit_workflow_event(tool_response_event)
                except Exception as e:
                    logger.warning(f"Failed to emit tool_response event: {e}")

                return {
                    "tool_name": function_name,
                    "arguments": function_args,
                    "result": result,
                    "success": True,
                    "duration_ms": duration_ms,
                    "tool_call_id": tc_id,
                    "_agent_invocation_result": True,
                }

            # Static tool registry
            tool_function = get_tool_function(function_name)
            if not tool_function:
                raise ValueError(f"Tool function not found: {function_name}")

            await _emit_tool_event(context, "tool_call", {"tool_name": function_name, "arguments": function_args})

            # Execute sync or async
            import inspect as _inspect

            if getattr(tool_function, "_is_async", False) or _inspect.iscoroutinefunction(tool_function):
                result = await tool_function(**function_args)  # type: ignore[arg-type]
            else:
                result = await asyncio.to_thread(tool_function, **function_args)

            duration_ms = int((time.time() - start_time) * 1000)
            await _emit_tool_event(
                context,
                "tool_response",
                {
                    "tool_name": function_name,
                    "result": result if isinstance(result, (str, int, float, bool)) else str(result)[:200],
                    "duration_ms": duration_ms,
                },
            )
            return {
                "tool_name": function_name,
                "arguments": function_args,
                "result": result,
                "success": True,
                "duration_ms": duration_ms,
                "tool_call_id": tc_id,
            }

        except Exception as e:
            logger.error(f"Tool execution failed for {function_name}: {e}")
            return {"tool_name": function_name, "error": str(e), "success": False, "arguments": function_args}


def _build_messages(system_prompt: str, context_msgs: List[Dict], query: str) -> List[Dict[str, Any]]:
    """Build LLM messages array from system prompt, context, and query."""
    messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt or "You are a helpful assistant."}]
    if isinstance(context_msgs, list):
        for m in context_msgs:
            if isinstance(m, dict) and "role" in m and "content" in m and m.get("role") != "system":
                msg = {"role": str(m["role"]), "content": str(m["content"])}
                # Preserve tool_calls for assistant messages
                if m.get("role") == "assistant" and m.get("tool_calls"):
                    msg["tool_calls"] = m["tool_calls"]
                # Preserve tool_call_id for tool messages
                if m.get("role") == "tool" and m.get("tool_call_id"):
                    msg["tool_call_id"] = m["tool_call_id"]
                messages.append(msg)
    # Ensure last message is the current query (avoid duplicates)
    if not (messages and messages[-1].get("role") == "user" and messages[-1].get("content") == query):
        messages.append({"role": "user", "content": query})
    return messages


async def _stream_llm_response(
    messages: List[Dict],
    llm_params: Dict[str, Any],
    tools: Optional[List] = None,
    step_id: str = "",
    execution_context: Optional[ExecutionContext] = None,
    visible_to_user: bool = True,
) -> Tuple[str, List[Dict], Optional[str]]:
    """Stream LLM response and emit delta events. Returns (content, tool_calls, finish_reason)."""
    import functools

    provider_config = {"type": "openai_textgen"}
    model_name = TextGenerationModelName.OPENAI_gpt_4o.value  # type: ignore
    svc = TextGenerationService()  # type: ignore

    stream_gen = svc.stream(
        "",  # prompt not used when messages provided
        provider_config,
        llm_params.get("max_tokens", 4096),
        model_name,
        "",  # sys_msg already in messages
        None,  # retries
        llm_params.get("temperature"),
        tools,
        "auto" if tools else None,
        messages,
        llm_params.get("response_format"),
    )

    collected = ""
    tool_calls = []
    finish_reason = None

    while True:
        try:
            event = await asyncio.get_event_loop().run_in_executor(None, functools.partial(next, stream_gen))
        except StopIteration:
            break

        event_type = event.get("type")
        if event_type == "delta":
            delta = event.get("text", "")
            collected += delta
            if step_id and execution_context:
                try:
                    evt = create_step_event(
                        execution_id=execution_context.execution_id,
                        step_id=step_id,
                        step_status="running",
                        workflow_id=execution_context.workflow_id,
                        output_data={"delta": delta, "accumulated_len": len(collected), "visible_to_user": visible_to_user},
                    )
                    await stream_manager.emit_execution_event(evt)
                    if execution_context.workflow_id:
                        await stream_manager.emit_workflow_event(evt)
                except Exception:
                    pass
        elif event_type == "final":
            tool_calls = event.get("tool_calls", [])
            finish_reason = event.get("finish_reason")
            # Get final text if available
            final_resp = event.get("response", {})
            if final_resp.get("text"):
                collected = final_resp["text"]
            break

    return collected, tool_calls, finish_reason


async def _execute_a2a_agent(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
    stream_mgr: Optional[Any] = None,
) -> Dict[str, Any]:
    """Execute an external A2A agent.

    This is called from agent_execution_step when a2a_agent_id is provided.
    Supports streaming when config.stream is True.

    Args:
        step_config: Step configuration containing a2a_agent_id, query, stream, etc.
        input_data: Input data from previous steps.
        execution_context: Workflow execution context.
        stream_mgr: Optional stream manager for emitting SSE events. If None, uses the
                    SDK's default stream_manager. This allows callers (like workflow-engine-poc)
                    to pass their own stream manager for proper event routing.
    """
    # Use provided stream manager or fall back to SDK's default
    _stream_manager = stream_mgr if stream_mgr is not None else stream_manager
    from uuid import UUID

    from sqlmodel import Session, select

    from ..db.database import engine
    from ..db.models.a2a_agents import A2AAgent, A2AAgentStatus, A2AAuthType

    config = step_config.get("config", {}) or {}
    a2a_agent_id = config.get("a2a_agent_id", "")
    stream = config.get("stream", False)
    step_id = step_config.get("step_id") or ""

    # Get query from template or input_data
    query = config.get("query", "")
    if query and "{" in query:
        try:
            query = query.format_map(type("_", (dict,), {"__missing__": lambda _, k: ""})(input_data))
        except Exception:
            pass
    if not query:
        query = input_data.get("current_message") or input_data.get("query") or ""
    if not query:
        return {"success": False, "error": "query is required"}

    # Fetch A2A agent from database
    try:
        with Session(engine) as session:
            agent = session.exec(select(A2AAgent).where(A2AAgent.id == UUID(a2a_agent_id))).first()
        if not agent:
            return {"success": False, "error": f"A2A agent not found: {a2a_agent_id}"}
        if agent.status != A2AAgentStatus.ACTIVE:
            return {"success": False, "error": f"A2A agent not active: {agent.status}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to fetch A2A agent: {e}"}

    # Build client request - decrypt auth_config if encrypted
    auth = None
    if agent.auth_type != A2AAuthType.NONE and agent.auth_config:
        decrypted_config = decrypt_if_encrypted(agent.auth_config)
        if decrypted_config:
            auth = A2AAuthConfig(auth_type=agent.auth_type.value, credentials=decrypted_config)

    agent_info = A2AAgentInfo(
        base_url=agent.base_url,
        name=agent.name,
        agent_card_url=agent.agent_card_url,
        auth=auth,
        timeout=config.get("timeout", 30.0),
    )

    request = A2AMessageRequest(
        content=query,
        context_id=config.get("context_id") or input_data.get("context_id"),
        task_id=config.get("task_id") or input_data.get("task_id"),
    )

    # Helper to build response dict from A2AMessageResponse
    def build_response(resp):
        return {
            "success": True,
            "response": resp.content or "",
            "task_id": resp.task.task_id if resp.task else None,
            "context_id": resp.task.context_id if resp.task else None,
            "is_complete": resp.is_complete,
            "artifacts": resp.artifacts,
            "error": resp.error,
            "agent_name": agent.name,
            "a2a_agent_id": str(agent.id),
            "mode": "a2a",
        }

    # Execute
    try:
        client = A2AClientService()

        if not (stream and step_id):
            return build_response(await client.send_message(agent_info, request))

        # Streaming mode - emit deltas via SSE
        accumulated = ""
        response = None

        async for response in client.stream_message(agent_info, request):
            new_content = response.content or ""
            if len(new_content) > len(accumulated):
                delta = new_content[len(accumulated) :]
                accumulated = new_content
                evt = create_step_event(
                    execution_id=execution_context.execution_id,
                    step_id=step_id,
                    step_status="running",
                    workflow_id=execution_context.workflow_id,
                    output_data={"delta": delta, "accumulated_len": len(accumulated)},
                )
                await _stream_manager.emit_execution_event(evt)
                if execution_context.workflow_id:
                    await _stream_manager.emit_workflow_event(evt)

        if response:
            return build_response(response)
        return {"success": False, "error": "No response from A2A agent", "a2a_agent_id": str(agent.id)}

    except Exception as e:
        logger.error(f"A2A agent execution failed: {e}")
        return {"success": False, "error": str(e), "a2a_agent_id": str(agent.id)}


async def agent_execution_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """
    Agent execution step that runs an AI agent with a query.

    Config options:
    - agent_name: Name of the agent
    - system_prompt: System prompt for the agent
    - query: Query to execute (can use template variables)
    - tools: List of tools available to the agent
    - force_real_llm: Force use of real LLM even without full config
    - a2a_agent_id: UUID of an external A2A agent (if provided, uses A2A protocol)
    """

    config = step_config.get("config", {})

    # Check if this is an A2A agent execution
    a2a_agent_id = config.get("a2a_agent_id")
    if a2a_agent_id:
        return await _execute_a2a_agent(step_config, input_data, execution_context)

    # Get agent configuration
    agent_name = config.get("agent_name", "Assistant")
    system_prompt = config.get("system_prompt", "You are a helpful assistant.")
    query_template = config.get("query", "")
    force_real_llm = config.get("force_real_llm", False)

    # Load agent from database if agent_id is provided to get provider_config
    agent_provider_type = None
    agent_provider_config = None
    agent_id = config.get("agent_id")

    if agent_id:
        try:
            session = get_db_session()
            try:
                db_agent = AgentsService.get_agent(session, agent_id)
                if db_agent:
                    agent_provider_type = db_agent.provider_type
                    agent_provider_config = db_agent.provider_config or {}
                    # Override agent_name and system_prompt from DB if not explicitly set
                    if not config.get("agent_name"):
                        agent_name = db_agent.name
                    # Load system prompt from database
                    if db_agent.system_prompt_id:
                        from ..db.models.prompts import Prompt
                        from sqlmodel import select

                        prompt = session.exec(select(Prompt).where(Prompt.id == db_agent.system_prompt_id)).first()
                        if prompt and not config.get("system_prompt"):
                            system_prompt = prompt.prompt
                    logger.info(
                        f"Loaded agent from DB: {db_agent.name}, provider: {agent_provider_type}, model: {agent_provider_config.get('model_name')}"
                    )
            finally:
                try:
                    session.close()
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Failed to load agent from database: {e}")

    # Add execution context metadata to input_data for streaming events
    if isinstance(input_data, dict):
        input_data["_execution_id"] = execution_context.execution_id
        input_data["_workflow_id"] = execution_context.workflow_id
        input_data["_step_id"] = step_config.get("step_id")
        # Pass agent provider config through context
        if agent_provider_type:
            input_data["_agent_provider_type"] = agent_provider_type
        if agent_provider_config:
            input_data["_agent_provider_config"] = agent_provider_config

    # Ensure current_message is available from Trigger output if not present
    try:
        if isinstance(input_data, dict) and "current_message" not in input_data:
            # Prefer normalized trigger; fallback to raw payload seeded by router
            trig = execution_context.step_io_data.get("trigger") or execution_context.step_io_data.get("trigger_raw")
            if isinstance(trig, dict):
                # Direct current_message if present
                cm = trig.get("current_message")
                if isinstance(cm, str) and cm:
                    input_data["current_message"] = cm
                # Else walk messages for last user content
                msgs = trig.get("messages") or []
                if isinstance(msgs, list) and msgs:
                    for m in reversed(msgs):
                        if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str):
                            input_data["current_message"] = m["content"]
                            break
    except Exception as e:
        logger.debug(f"Could not derive current_message from trigger: {e}")

    # Extract file attachment from trigger data for file search
    try:
        trig = execution_context.step_io_data.get("trigger") or execution_context.step_io_data.get("trigger_raw")
        if isinstance(trig, dict):
            attachment = trig.get("attachment")
            if isinstance(attachment, dict) and attachment.get("path"):
                input_data["_attachment"] = attachment
                logger.debug(f"File attachment available for agent: {attachment.get('name')} at {attachment.get('path')}")
    except Exception as e:
        logger.debug(f"Could not extract file attachment from trigger: {e}")

    # Include chat history/messages: prefer step-specific messages if present, else Trigger
    try:
        # Step-scoped messages (interactive chat)
        step_msgs = []
        try:
            session = get_db_session()
            try:
                dbs = DatabaseService()
                step_msgs = dbs.list_agent_messages(
                    session, execution_id=execution_context.execution_id, step_id=step_config.get("step_id")
                )
            finally:
                try:
                    session.close()
                except Exception:
                    pass
            # Convert to simple role/content list, handling tool messages specially
            converted_msgs = []
            for m in step_msgs:
                role = m.get("role", "user")
                content = m.get("content", "")
                metadata = m.get("metadata", {})

                msg_dict = {"role": role, "content": content}

                # Tool messages need tool_call_id
                if role == "tool" and isinstance(metadata, dict):
                    tool_call_id = metadata.get("tool_call_id")
                    if tool_call_id:
                        msg_dict["tool_call_id"] = tool_call_id

                # Assistant messages with tool_calls need special structure
                if role == "assistant" and isinstance(metadata, dict):
                    tool_calls = metadata.get("tool_calls")
                    if tool_calls and isinstance(tool_calls, list):
                        msg_dict["tool_calls"] = tool_calls

                converted_msgs.append(msg_dict)

            step_msgs = converted_msgs
        except Exception as _db_err:
            logger.debug(f"No DB messages found or DB unavailable: {_db_err}")

        if step_msgs:
            # DB returns messages newest-first; reverse to chronological order for LLMs
            step_msgs_asc = list(reversed(step_msgs))
            input_data["messages"] = step_msgs_asc
            input_data.setdefault("chat_history", step_msgs_asc)
            # Always set current_message to the latest user message
            for m in reversed(step_msgs_asc):  # iterate newest-first
                if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str):
                    input_data["current_message"] = m["content"]
                    break
        else:
            trig = execution_context.step_io_data.get("trigger") or execution_context.step_io_data.get("trigger_raw")
            if isinstance(trig, dict):
                msgs = trig.get("messages")
                if isinstance(msgs, list) and msgs and "messages" not in input_data:
                    input_data["messages"] = msgs
                    input_data.setdefault("chat_history", msgs)
                if "current_message" not in input_data:
                    cm = trig.get("current_message")
                    if isinstance(cm, str) and cm:
                        input_data["current_message"] = cm
                    elif isinstance(msgs, list) and msgs:
                        for m in reversed(msgs):  # msgs assumed chronological; reversed -> newest-first
                            if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str):
                                input_data["current_message"] = m["content"]
                                break

        # Merge per-step decision flags (e.g., final_turn) written by resume_execution
        try:
            sid = step_config.get("step_id")
            if sid and isinstance(execution_context.step_io_data.get(sid), dict):
                for k, v in execution_context.step_io_data[sid].items():
                    if k not in input_data:
                        input_data[k] = v
                # If current_message still missing, derive from newly merged step-level messages
                if "current_message" not in input_data:
                    merged_msgs = input_data.get("messages")
                    if isinstance(merged_msgs, list):
                        for m in reversed(merged_msgs):
                            if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str):
                                input_data["current_message"] = m["content"]
                                break
        except Exception as _m:
            logger.debug(f"Could not merge step-scoped decision flags: {_m}")
    except Exception as e:
        logger.debug(f"Could not include messages in agent context: {e}")

    # Process query template with input data (e.g., "{current_message}")
    query = query_template
    if isinstance(query_template, str) and "{" in query_template:
        try:

            class _Safe(dict):
                def __missing__(self, k):  # replace missing vars with empty string
                    return ""

            query = query_template.format_map(_Safe(input_data))
        except Exception as e:
            logger.debug(f"Template formatting failed; using raw template. Error: {e}")
            query = query_template

    # Create agent; remove step-config tool support and rely on DB-bound tools only
    connected_agents = config.get("connected_agents", [])

    # Extract agent tools from functions array (those with agent_id)
    functions = config.get("functions", [])
    agent_tool_ids = []
    for func in functions:
        if isinstance(func, dict):
            func_def = func.get("function", {})
            if "agent_id" in func_def:
                agent_tool_ids.append(func_def["agent_id"])

    agent = AgentStep(
        name=agent_name,
        system_prompt=system_prompt,
        tools=load_agent_db_tool_schemas(agent_name=agent_name),
        force_real_llm=force_real_llm,
        connected_agents=connected_agents,
    )

    # Load and register agent tools from functions array
    if agent_tool_ids:
        try:
            session = get_db_session()
            try:
                for agent_id in agent_tool_ids:
                    # Load agent from database
                    db_agent = AgentsService.get_agent(session, agent_id)
                    if db_agent:
                        # Find the corresponding function definition
                        for func in functions:
                            func_def = func.get("function", {})
                            if func_def.get("agent_id") == agent_id:
                                tool_name = func_def.get("name")
                                if tool_name:
                                    # Register in dynamic agent tools
                                    agent._dynamic_agent_tools[tool_name] = {
                                        "schema": func,
                                        "agent": db_agent,
                                    }
                                    logger.info(f"Registered agent tool: {tool_name} -> {db_agent.name}")
                                break
            finally:
                try:
                    session.close()
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Failed to load agent tools from functions array: {e}")

    # If interactive by default unless explicitly disabled
    interactive = config.get("interactive", True)
    multi_turn = bool(config.get("multi_turn", False))
    logger.info(f"Agent step config - interactive: {interactive}, multi_turn: {multi_turn}")

    # If interactive and no user messages yet, pause and wait for input
    if interactive:
        # Determine if we have sufficient messages to proceed
        msgs = input_data.get("messages") or input_data.get("chat_history") or []
        has_user_msg = any(
            isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str) and bool(m.get("content"))
            for m in (msgs or [])
        )
        # Also treat presence of current_message as sufficient input to proceed
        if not has_user_msg and isinstance(input_data.get("current_message"), str) and input_data.get("current_message"):
            has_user_msg = True
        if not has_user_msg:
            return {
                "status": "waiting",
                "waiting_for": "user_input",
                "step_type": "interactive_agent",
                "agent_config": {"agent_name": agent_name},
            }

    # Optional LLM params from config (e.g., max_tokens, temperature, response_format)
    try:
        llm_params: Dict[str, Any] = {}
        mt = config.get("max_tokens")
        if isinstance(mt, int) and mt > 0:
            llm_params["max_tokens"] = mt
        try:
            temp = config.get("temperature")
            if temp is not None:
                llm_params["temperature"] = float(temp)
        except Exception:
            pass
        # Support OpenAI's response_format for JSON mode and structured outputs
        response_format = config.get("response_format")
        if response_format:
            llm_params["response_format"] = response_format
        if llm_params:
            input_data["_llm_params"] = llm_params
    except Exception:
        pass

    # Execute query, optionally streaming deltas
    stream_enabled = bool(config.get("stream", False))
    visible_to_user = config.get("visible_to_user", True)
    result = {}
    sid = step_config.get("step_id") or ""

    if stream_enabled:
        try:
            # Prepare messages and tools
            ctx_msgs = input_data.get("messages") or input_data.get("chat_history") or []
            messages = _build_messages(system_prompt, ctx_msgs, query)

                # LLM params
                _llm = input_data.get("_llm_params", {}) if isinstance(input_data, dict) else {}
                _max_tokens = _llm.get("max_tokens")
                if not isinstance(_max_tokens, int) or _max_tokens <= 0:
                    _max_tokens = 4096  # increased to support large tool call arguments
                _temperature = _llm.get("temperature")
                _response_format = _llm.get("response_format")

                # Provider config - check step_config["model"] first (set by workflow_endpoints),
                # then input_data["_agent_provider_config"], then default
                model_from_step_config = step_config.get("model")
                agent_provider_type = input_data.get("_agent_provider_type") if isinstance(input_data, dict) else None
                agent_provider_config = input_data.get("_agent_provider_config") if isinstance(input_data, dict) else None

                provider_config = {"type": agent_provider_type or "openai_textgen"}

                if model_from_step_config:
                    # Model set directly by workflow_endpoints.py
                    model_name = model_from_step_config
                    logger.info(f"Streaming with model from step_config: {model_name}")
                elif agent_provider_config and agent_provider_config.get("model_name"):
                    model_name_from_config = agent_provider_config.get("model_name")
                    # Try to map to enum, fall back to string
                    try:
                        model_name = getattr(
                            TextGenerationModelName, f"OPENAI_{model_name_from_config.replace('-', '_')}", None
                        )
                        if model_name:
                            model_name = model_name.value  # type: ignore
                        else:
                            model_name = model_name_from_config
                    except Exception:
                        model_name = model_name_from_config
                    logger.info(f"Streaming with agent provider config model: {model_name}")
                else:
                    model_name = TextGenerationModelName.OPENAI_gpt_4o.value  # type: ignore
                    logger.info("Streaming with default model: gpt-4o")

                sid = step_config.get("step_id") or ""

                # Prepare tools for LLM
                await agent._ensure_dynamic_agent_tools(input_data)
                explicit_tools = agent.tools or []
                # Extract only the schemas from dynamic agent tools (not the agent objects)
                dynamic_agent_tools_list = [meta["schema"] for meta in agent._dynamic_agent_tools.values()]
                llm_tools = None
                if explicit_tools:
                    llm_tools = list(explicit_tools)
                if dynamic_agent_tools_list:
                    llm_tools = (llm_tools or []) + dynamic_agent_tools_list

                # Multi-turn conversation loop
                conversation_turns = 0
                max_conversation_turns = 4
                tool_calls_trace: List[Dict[str, Any]] = []
                tokens_in_total = 0
                tokens_out_total = 0

                # Extract file paths for file search (OpenAI only)
                files_for_search: Optional[List[str]] = None
                attachment = input_data.get("_attachment")
                if isinstance(attachment, dict) and attachment.get("path"):
                    files_for_search = [attachment["path"]]
                    logger.debug(f"Passing file to LLM for file search: {attachment.get('name')}")

                while conversation_turns < max_conversation_turns:
                    conversation_turns += 1

                    # Make streaming LLM call with tool support
                    svc = TextGenerationService()  # type: ignore

                    # Create a sync generator and wrap it to run in executor
                    # This allows the blocking I/O from OpenAI to not block the event loop
                    # Note: files_for_search only passed on first turn (files are uploaded once to vector store)
                    files_arg = files_for_search if conversation_turns == 1 else None

                    def create_stream(files_to_pass=files_arg):
                        return svc.stream(
                            "",  # prompt not used when messages provided
                            provider_config,
                            _max_tokens,
                            model_name,
                            "",  # sys_msg already in messages
                            None,  # retries
                            _temperature,
                            llm_tools,
                            "auto" if llm_tools else None,
                            messages,
                            _response_format,
                            files_to_pass,
                        )

                    # Get the generator
                    stream_generator = create_stream()

                    # Process streaming response
                    collected_content = ""
                    tool_calls_from_stream = []
                    finish_reason = None

                    # Iterate through the sync generator, running each next() call in executor
                    while True:
                        try:
                            # Run the blocking next() call in a thread pool to avoid blocking event loop
                            # Use functools.partial to avoid lambda closure issues
                            import functools

                            event = await asyncio.get_event_loop().run_in_executor(
                                None, functools.partial(next, stream_generator)
                            )
                        except StopIteration:
                            break
                        event_type = event.get("type")

                        if event_type == "delta":
                            # Stream content token-by-token
                            delta_text = event.get("text", "")
                            collected_content += delta_text

                            # Emit streaming delta event
                            if sid:
                                evt = create_step_event(
                                    execution_id=execution_context.execution_id,
                                    step_id=sid,
                                    step_status="running",
                                    workflow_id=execution_context.workflow_id,
                                    output_data={
                                        "delta": delta_text,
                                        "accumulated_len": len(collected_content),
                                        "visible_to_user": visible_to_user,
                                    },
                                )
                                await stream_manager.emit_execution_event(evt)
                                if execution_context.workflow_id:
                                    await stream_manager.emit_workflow_event(evt)

                        elif event_type == "final":
                            # Final event contains tool calls if present
                            tool_calls_from_stream = event.get("tool_calls", [])
                            finish_reason = event.get("finish_reason")
                            # Extract token usage from final response
                            final_response = event.get("response", {})
                            if isinstance(final_response, dict):
                                tokens_in_total += final_response.get("tokens_in", 0) or 0
                                tokens_out_total += final_response.get("tokens_out", 0) or 0
                            break

                    if tool_calls_from_stream:
                        # Tool calls detected - add assistant message with tool calls to conversation
                        # Use generic Chat Completions format - providers will convert as needed
                        assistant_message: Dict[str, Any] = {"role": "assistant", "tool_calls": []}
                        for tc in tool_calls_from_stream:
                            # Tool calls from stream are already in dict format
                            tool_call_id = tc.get("id") or str(uuid.uuid4())
                            func_name = tc.get("function", {}).get("name")
                            func_args = tc.get("function", {}).get("arguments", "{}")

                            # Ensure arguments is a JSON string (OpenAI API requirement)
                            if isinstance(func_args, dict):
                                func_args = json.dumps(func_args)
                            elif not func_args:
                                func_args = "{}"

                            assistant_message["tool_calls"].append(
                                {
                                    "id": tool_call_id,
                                    "type": "function",
                                    "function": {
                                        "name": func_name,
                                        "arguments": func_args,
                                    },
                                }
                            )
                        messages.append(assistant_message)

                        # Execute tool calls
                        for tool_call_dict in tool_calls_from_stream:
                            try:
                                func_name = tool_call_dict.get("function", {}).get("name")
                                func_args = tool_call_dict.get("function", {}).get("arguments", "{}")
                                tool_call_id = tool_call_dict.get("id") or str(uuid.uuid4())

                                # Convert dict to object-like structure for _execute_tool_call
                                class ToolCallObj:
                                    def __init__(self, tc_dict):
                                        self.id = tc_dict.get("id")
                                        self.tool_call_id = tc_dict.get("id")
                                        self.name = tc_dict.get("function", {}).get("name")
                                        self.arguments = tc_dict.get("function", {}).get("arguments")

                                        class FunctionObj:
                                            def __init__(self, name, arguments):
                                                self.name = name
                                                self.arguments = arguments

                                        self.function = FunctionObj(self.name, self.arguments)

                                tool_call_obj = ToolCallObj(tool_call_dict)
                                tool_result = await agent._execute_tool_call(tool_call_obj, context=input_data)
                                tool_calls_trace.append(tool_result)

                                # Build result string
                                result_content = tool_result.get("result", {})
                                if isinstance(result_content, dict):
                                    result_str = result_content.get("response") or json.dumps(result_content)
                                else:
                                    result_str = str(result_content)

                                # Add tool response in generic format - providers convert as needed
                                messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": result_str})

                            except Exception as e:
                                logger.error(f"Tool execution failed: {e}")
                                tool_call_id = tool_call_dict.get("id") or str(uuid.uuid4())
                                messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": f"Error: {str(e)}"})

                        # Continue loop to get final response
                        continue

                    else:
                        # No tool calls - this is the final response
                        # Content was already streamed token-by-token during the streaming loop above

                        # Build result
                        result = {
                            "response": collected_content,
                            "tool_calls": tool_calls_trace,
                            "mode": "llm",
                            "model": {"provider": provider_config["type"], "name": str(model_name)},
                            "usage": {
                                "tokens_in": tokens_in_total,
                                "tokens_out": tokens_out_total,
                                "total_tokens": tokens_in_total + tokens_out_total,
                                "llm_calls": conversation_turns,
                            },
                        }
                        break

                # If we hit max turns without a final response
                if conversation_turns >= max_conversation_turns:
                    logger.warning(f"Reached max conversation turns ({max_conversation_turns}), ending loop")
                    result = {
                        "response": "Reached conversation turn limit",
                        "tool_calls": tool_calls_trace,
                        "mode": "llm",
                        "model": {"provider": provider_config["type"], "name": str(model_name)},
                        "usage": {
                            "tokens_in": tokens_in_total,
                            "tokens_out": tokens_out_total,
                            "total_tokens": tokens_in_total + tokens_out_total,
                            "llm_calls": conversation_turns,
                        },
                    }
            else:
                # Build messages chronologically from context
                messages: List[Dict[str, str]] = []

                # Always start with system message for streaming (required for response_format)
                sys_msg_val = system_prompt or "You are a helpful assistant."
                messages.append({"role": "system", "content": sys_msg_val})

                ctx_msgs = input_data.get("messages") or input_data.get("chat_history")
                if isinstance(ctx_msgs, list):
                    # Ensure order and shape
                    for m in ctx_msgs:
                        if isinstance(m, dict) and "role" in m and "content" in m:
                            # Skip system messages from context since we already added one
                            if m.get("role") != "system":
                                messages.append({"role": str(m["role"]), "content": str(m["content"])})
                # Ensure the last message is the current user query
                if not (messages and messages[-1].get("role") == "user" and messages[-1].get("content") == query):
                    messages.append({"role": "user", "content": query})

                # LLM params
                _llm = input_data.get("_llm_params", {}) if isinstance(input_data, dict) else {}
                _max_tokens = _llm.get("max_tokens")
                if not isinstance(_max_tokens, int) or _max_tokens <= 0:
                    _max_tokens = 4096  # increased to support large tool call arguments
                _temperature = _llm.get("temperature")
                _response_format = _llm.get("response_format")

                # Provider config and model - check step_config["model"] first (set by workflow_endpoints),
                # then input_data["_agent_provider_config"], then default
                model_from_step_config = step_config["config"]["model"]
                agent_provider_type = input_data.get("_agent_provider_type") if isinstance(input_data, dict) else None
                agent_provider_config = input_data.get("_agent_provider_config") if isinstance(input_data, dict) else None

                provider_config = {"type": agent_provider_type or "openai_textgen"}

                if model_from_step_config:
                    # Model set directly by workflow_endpoints.py
                    model_name = model_from_step_config
                    logger.info(f"Streaming (no tools) with model from step_config: {model_name}")
                elif agent_provider_config and agent_provider_config.get("model_name"):
                    model_name_from_config = agent_provider_config.get("model_name")
                    # Try to map to enum, fall back to string
                    try:
                        model_name = getattr(
                            TextGenerationModelName, f"OPENAI_{model_name_from_config.replace('-', '_')}", None
                        )
                        if model_name:
                            model_name = model_name.value  # type: ignore
                        else:
                            model_name = model_name_from_config
                    except Exception:
                        model_name = model_name_from_config
                    logger.info(f"Streaming (no tools) with agent provider config model: {model_name}")
                else:
                    model_name = TextGenerationModelName.OPENAI_gpt_4o.value  # type: ignore
                    logger.info("Streaming (no tools) with default model: gpt-4o")

                sid = step_config.get("step_id") or ""

                # Use llm-gateway streaming API
                # Note: sys_msg is not needed since we already added it to messages
                svc = TextGenerationService()  # type: ignore

                # Extract file paths for file search (OpenAI only)
                files_for_search: Optional[List[str]] = None
                attachment = input_data.get("_attachment")
                if isinstance(attachment, dict) and attachment.get("path"):
                    files_for_search = [attachment["path"]]
                    logger.debug(f"Passing file to LLM for file search: {attachment.get('name')}")

                # Create stream generator
                stream_generator = svc.stream(
                    prompt="",
                    config=provider_config,
                    max_tokens=_max_tokens,
                    model_name=model_name,
                    sys_msg="",  # Empty since system message is already in messages array
                    retries=None,
                    temperature=_temperature,
                    tools=None,
                    tool_choice=None,
                    messages=messages,
                    response_format=_response_format,
                    files=files_for_search,
                )

                # Iterate through the sync generator, running each next() call in executor
                while True:
                    try:
                        # Run the blocking next() call in a thread pool to avoid blocking event loop
                        # Use functools.partial to avoid lambda closure issues
                        import functools

                        ev = await asyncio.get_event_loop().run_in_executor(None, functools.partial(next, stream_generator))
                    except StopIteration:
                        break

                    et = (ev.get("type") or "").lower()
                    if et == "delta":
                        delta = ev.get("text") or ""
                        if not isinstance(delta, str) or not delta:
                            continue
                        accumulated += delta
                        try:
                            if sid:
                                evt = create_step_event(
                                    execution_id=execution_context.execution_id,
                                    step_id=sid,
                                    step_status="running",
                                    workflow_id=execution_context.workflow_id,
                                    output_data={
                                        "delta": delta,
                                        "accumulated_len": len(accumulated),
                                        "visible_to_user": visible_to_user,
                                    },
                                )
                                await stream_manager.emit_execution_event(evt)
                                if execution_context.workflow_id:
                                    await stream_manager.emit_workflow_event(evt)
                        except Exception:
                            pass
                    elif et == "final":
                        # Final response payload from gateway
                        final_resp = ev.get("response") or {}
                        text = (final_resp.get("text") or accumulated or "").strip()
                        usage = {
                            "tokens_in": int(final_resp.get("tokens_in", -1) or -1),
                            "tokens_out": int(final_resp.get("tokens_out", -1) or -1),
                            "total_tokens": int(final_resp.get("tokens_in", -1) or -1)
                            + int(final_resp.get("tokens_out", -1) or -1),
                            "llm_calls": 1,
                        }
                        result = {
                            "response": text,
                            "tool_calls": [],
                            "mode": "llm",
                            "model": {"provider": provider_config["type"], "name": str(model_name)},
                            "usage": usage,
                        }
                        break
                else:
                    # If stream ended without final marker, synthesize result
                    result = {
                        "response": accumulated,
                        "tool_calls": [],
                        "mode": "llm",
                        "model": {"provider": provider_config["type"], "name": str(model_name)},
                        "usage": {"tokens_in": -1, "tokens_out": -1, "total_tokens": -1, "llm_calls": 1},
                    }

                # Small flush to ensure the last line breaks after deltas
                if accumulated and sid:
                    try:
                        evt = create_step_event(
                            execution_id=execution_context.execution_id,
                            step_id=sid,
                            step_status="running",
                            workflow_id=execution_context.workflow_id,
                            output_data={"delta": "", "accumulated_len": len(accumulated)},
                        )
                        await stream_manager.emit_execution_event(evt)
                        if execution_context.workflow_id:
                            await stream_manager.emit_workflow_event(evt)
                    except Exception:
                        pass
        except Exception as _se:
            logger.debug(f"Streaming failed, falling back to non-streaming: {_se}")
            result = await agent.execute(query, context=input_data)
    else:
        result = await agent.execute(query, context=input_data)

    # Parse JSON response if response_format was used
    try:
        response_format = config.get("response_format")
        if response_format and isinstance(response_format, dict) and response_format.get("type") == "json_object":
            response_text = result.get("response")
            if isinstance(response_text, str):
                try:
                    parsed_json = json.loads(response_text)
                    result["response"] = parsed_json  # Replace string with parsed dict
                    result["response_raw"] = response_text  # Keep original for reference
                except json.JSONDecodeError as je:
                    logger.warning(f"Failed to parse JSON response: {je}")
    except Exception as _parse_e:
        logger.debug(f"Could not parse JSON response: {_parse_e}")

    # Persist assistant response to DB as a message for this step
    logger.info("=== STARTING DB PERSISTENCE ===")
    try:
        sid = step_config.get("step_id")
        if sid and isinstance(result, dict):
            assistant_content = result.get("response") or result.get("output")
            if assistant_content is not None:
                logger.info(f"Persisting assistant message for step {sid}")
                dbs = DatabaseService()
                session = get_db_session()
                dbs.create_agent_message(
                    session,
                    execution_id=execution_context.execution_id,
                    step_id=sid,
                    role="assistant",
                    content=str(assistant_content),
                    metadata={"model": result.get("model"), "usage": result.get("usage")},
                    user_id=execution_context.user_context.user_id,
                    session_id=execution_context.user_context.session_id,
                )
                logger.info("Successfully persisted assistant message")
    except Exception as _persist_e:
        logger.warning(f"Could not persist assistant message: {_persist_e}")

    # If multi_turn and not marked final, keep waiting for more input with agent response
    if interactive and multi_turn and not bool(input_data.get("final_turn")):
        logger.info(f"Agent step returning WAITING status (interactive={interactive}, multi_turn={multi_turn})")
        return {
            "status": "waiting",
            "waiting_for": "user_input",
            "step_type": "interactive_agent",
            "agent_response": result,
            "agent_config": {"agent_name": agent_name},
        }

    logger.info(f"Agent step returning result (interactive={interactive}, multi_turn={multi_turn})")
    return result
