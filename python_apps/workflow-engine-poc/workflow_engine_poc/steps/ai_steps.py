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
from typing import Dict, Any, List, Optional, Callable, Union
import logging

# Import tools system
from ..tools import get_tool_by_name

# DB access for dynamic agent tools
from sqlmodel import select
from ..db.database import get_db_session
from ..db.models import Agent as DBAgent, Prompt as DBPrompt, AgentToolBinding as DBAgentToolBinding, Tool as DBTool

from ..execution_context import ExecutionContext, StepResult, StepStatus, ExecutionStatus

# Streaming utilities
from ..streaming import stream_manager, create_step_event

# Initialize logger first
logger = logging.getLogger(__name__)

MAX_AGENT_RECURSION_DEPTH = 5

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


# Import llm-gateway components
try:
    from llm_gateway.services import (
        TextGenerationService,
        RequestType,
        UniversalService,
    )
    from llm_gateway.models.text_generation.core.interfaces import (
        TextGenerationType,
        TextGenerationModelName,
    )

    LLM_GATEWAY_AVAILABLE = True
except ImportError as e:
    logger.error(f"llm-gateway not available: {e}")
    LLM_GATEWAY_AVAILABLE = False
except Exception as e:
    logger.error(f"llm-gateway configuration error: {e}")
    LLM_GATEWAY_AVAILABLE = False


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
        force_real_llm: bool = False,
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
            # Compose sys_msg and initial prompt/messages
            sys_msg = self.system_prompt or ""
            base_prompt = f"{json.dumps(context, indent=2)}\n\nUser query: {query}" if context else query
            current_prompt = base_prompt

            # Build chat messages if available
            messages: List[Dict[str, Any]] = []
            if sys_msg:
                messages.append({"role": "system", "content": sys_msg})
            ctx_messages = []
            if isinstance(context, dict):
                ctx_messages = context.get("messages") or context.get("chat_history") or []
            if isinstance(ctx_messages, list) and ctx_messages:
                # Ensure messages are {role, content}
                for m in ctx_messages:
                    if isinstance(m, dict) and "role" in m and "content" in m:
                        messages.append({"role": str(m["role"]), "content": str(m["content"])})
                # Only add the query if not already the last user message
                if not (messages and messages[-1].get("role") == "user" and messages[-1].get("content") == query):
                    messages.append({"role": "user", "content": query})
            else:
                messages.append({"role": "user", "content": query})

            # Prepare tools: merge explicit tools with dynamic per-agent tools
            dynamic_agent_tools = await self._ensure_dynamic_agent_tools(context)
            explicit_tools = self.tools or []
            # If neither explicit tools nor dynamic agent tools are provided, pass None (no tools)
            llm_tools = None
            if explicit_tools:
                llm_tools = list(explicit_tools)
            if dynamic_agent_tools:
                llm_tools = (llm_tools or []) + list(dynamic_agent_tools)

            # Default provider config; could be made configurable later
            config = {"type": "openai_textgen"}
            # Use GPT-4o (the only supported model in this setup)
            model_name = TextGenerationModelName.OPENAI_gpt_4o  # type: ignore

            # Multi-turn tool loop with a small cap
            tool_calls_trace: List[Dict[str, Any]] = []
            max_tool_iterations = 4

            # Token usage accumulation
            tokens_in_total = 0
            tokens_out_total = 0
            llm_calls = 0
            provider_type = str(config.get("type", "unknown"))
            model_label = str(model_name)

            for _ in range(max_tool_iterations):
                # TextGenerationService is synchronous; run in a thread to avoid blocking
                # Respect optional llm params from context; provide sensible defaults
                _llm = (context or {}).get("_llm_params", {}) if isinstance(context, dict) else {}
                _max_tokens = _llm.get("max_tokens")
                if not isinstance(_max_tokens, int) or _max_tokens <= 0:
                    _max_tokens = 600  # default to avoid premature truncation
                _temperature = _llm.get("temperature")

                response = await asyncio.to_thread(
                    self.llm_service.generate,
                    current_prompt,
                    config,
                    _max_tokens,
                    model_name,
                    sys_msg,
                    None,  # retries
                    _temperature,
                    llm_tools,
                    "auto" if llm_tools else None,  # tool_choice
                    messages,
                )

                # Accumulate token usage
                try:
                    tokens_in_total += int(getattr(response, "tokens_in", 0) or 0)
                    tokens_out_total += int(getattr(response, "tokens_out", 0) or 0)
                    llm_calls += 1
                except Exception:
                    pass

                # If no tool calls, we have a final answer
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

                # Add assistant message with tool_calls (required by OpenAI format)
                assistant_message = {"role": "assistant", "tool_calls": []}

                # Convert tool calls to proper format for the assistant message
                for tool_call in response.tool_calls or []:
                    # Extract tool call info
                    tool_call_id = getattr(tool_call, "id", None) or getattr(tool_call, "tool_call_id", None)
                    function_name = getattr(tool_call, "name", None)
                    function_args = getattr(tool_call, "arguments", None)

                    if function_name is None and hasattr(tool_call, "function"):
                        function_name = getattr(tool_call.function, "name", None)
                        function_args = getattr(tool_call.function, "arguments", None)

                    # Ensure we have a tool_call_id
                    if not tool_call_id:
                        import uuid

                        tool_call_id = str(uuid.uuid4())

                    # Normalize arguments to string if needed
                    if isinstance(function_args, dict):
                        function_args = json.dumps(function_args)
                    elif function_args is None:
                        function_args = "{}"

                    assistant_message["tool_calls"].append(
                        {
                            "id": tool_call_id,
                            "type": "function",
                            "function": {"name": function_name, "arguments": function_args},
                        }
                    )

                messages.append(assistant_message)

                # Execute tool calls and add proper tool response messages
                for tool_call in response.tool_calls or []:
                    try:
                        tool_result = await self._execute_tool_call(tool_call)
                        tool_calls_trace.append(tool_result)

                        # Get tool_call_id for the response
                        tool_call_id = getattr(tool_call, "id", None) or getattr(tool_call, "tool_call_id", None)
                        if not tool_call_id:
                            # Find the corresponding tool call from assistant message
                            function_name = getattr(tool_call, "name", None)
                            if function_name is None and hasattr(tool_call, "function"):
                                function_name = getattr(tool_call.function, "name", None)

                            # Find matching tool call in assistant message
                            for tc in assistant_message["tool_calls"]:
                                if tc["function"]["name"] == function_name:
                                    tool_call_id = tc["id"]
                                    break

                        # Format tool result content
                        if tool_result.get("success"):
                            res_val = tool_result.get("result")
                            # Prefer child agent response when present
                            if isinstance(res_val, dict) and res_val.get("response"):
                                content = str(res_val.get("response"))
                            else:
                                try:
                                    content = res_val if isinstance(res_val, str) else json.dumps(res_val)
                                except Exception:
                                    content = str(res_val)
                        else:
                            content = f"Error: {tool_result.get('error', 'Unknown error')}"

                        # Add proper tool response message
                        messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": content})

                    except Exception as e:
                        err = {
                            "tool_name": getattr(tool_call, "name", "unknown"),
                            "success": False,
                            "error": str(e)[:400],
                        }
                        tool_calls_trace.append(err)

                        # Add error tool response
                        tool_call_id = getattr(tool_call, "id", None) or getattr(tool_call, "tool_call_id", None)
                        if not tool_call_id:
                            import uuid

                            tool_call_id = str(uuid.uuid4())

                        messages.append({"role": "tool", "tool_call_id": tool_call_id, "content": f"Error: {str(e)}"})

                # Keep the current prompt for the next iteration
                current_prompt = base_prompt

            # If iteration cap reached without final text
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

    async def _execute_tool_call(self, tool_call) -> Dict[str, Any]:
        """Execute a tool call from either OpenAI-style or llm-gateway ToolCall
        - Supports both tool_call.name/arguments and tool_call.function.name/arguments
        - Arguments may be dicts or JSON strings
        - Supports both sync and async tool functions
        """
        import time

        try:
            # Extract function name and args from multiple possible shapes
            function_name = getattr(tool_call, "name", None)
            function_args = getattr(tool_call, "arguments", None)

            if function_name is None and hasattr(tool_call, "function"):
                function_name = getattr(tool_call.function, "name", None)
                function_args = getattr(tool_call.function, "arguments", None)

            # Normalize arguments: allow JSON string or dict; default to {}
            if isinstance(function_args, str):
                try:
                    function_args = json.loads(function_args)
                except Exception:
                    function_args = {}
            if function_args is None:
                function_args = {}

            if not function_name:
                raise ValueError("Tool call missing function name")

            # Resolve either a dynamic agent tool or a registered function tool
            dynamic_meta = self._dynamic_agent_tools.get(function_name)
            start_time = time.time()
            if dynamic_meta:
                # Dynamic agent invocation
                target_agent: DBAgent = dynamic_meta["agent"]
                query = function_args.get("query") or function_args.get("input") or ""
                child_context = function_args.get("context") if isinstance(function_args.get("context"), dict) else {}
                result = await self._invoke_agent(target_agent, query=query, context=child_context)
                duration_ms = int((time.time() - start_time) * 1000)
                return {
                    "tool_name": function_name,
                    "arguments": function_args,
                    "result": result,
                    "success": True,
                    "duration_ms": duration_ms,
                    "tool_call_id": getattr(tool_call, "id", None) or getattr(tool_call, "tool_call_id", None),
                    "_agent_invocation_result": True,
                }

            # Fall back to static tool registry
            tool_function = get_tool_by_name(function_name)
            if not tool_function:
                raise ValueError(f"Tool function not found: {function_name}")

            # Determine sync/async and execute accordingly
            is_async = getattr(tool_function, "_is_async", False)
            if not is_async:
                try:
                    import inspect as _inspect

                    is_async = _inspect.iscoroutinefunction(tool_function)
                except Exception:
                    pass

            if is_async:
                result = await tool_function(**function_args)  # type: ignore[arg-type]
            else:
                result = await asyncio.to_thread(tool_function, **function_args)
            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "tool_name": function_name,
                "arguments": function_args,
                "result": result,
                "success": True,
                "duration_ms": duration_ms,
                "tool_call_id": getattr(tool_call, "id", None) or getattr(tool_call, "tool_call_id", None),
            }

        except Exception as e:
            return {
                "tool_name": getattr(
                    tool_call,
                    "name",
                    getattr(getattr(tool_call, "function", None), "name", "unknown"),
                ),
                "error": str(e),
                "success": False,
            }


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

    # Enrich input_data with variables from step_io_data for template interpolation
    # This must happen BEFORE the A2A check so A2A agents can use template interpolation
    try:
        if isinstance(input_data, dict):
            # Add scalar values from step_io_data (e.g., name, order_id from input_data in execution payload)
            for key, value in execution_context.step_io_data.items():
                if key not in input_data and isinstance(value, (str, int, float, bool)):
                    input_data[key] = value

            # Ensure current_message is available from Trigger output if not present
            if "current_message" not in input_data:
                # Prefer normalized trigger; fallback to raw payload seeded by router
                trig = execution_context.step_io_data.get("trigger") or execution_context.step_io_data.get("trigger_raw")
                if isinstance(trig, dict):
                    # Direct current_message if present
                    cm = trig.get("current_message")
                    if isinstance(cm, str) and cm:
                        input_data["current_message"] = cm
                    # Else walk messages for last user content
                    msgs = trig.get("messages") or []
                    if isinstance(msgs, list) and msgs and "current_message" not in input_data:
                        for m in reversed(msgs):
                            if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str):
                                input_data["current_message"] = m["content"]
                                break
    except Exception as e:
        logger.debug(f"Could not enrich input_data from step_io_data: {e}")

    # Check if this is an A2A agent execution - delegate to SDK implementation
    a2a_agent_id = config.get("a2a_agent_id")
    if a2a_agent_id:
        from workflow_core_sdk.steps.ai_steps import _execute_a2a_agent
        from workflow_core_sdk.execution_context import ExecutionContext as SDKExecutionContext, UserContext

        # Ensure workflow_id is included in the config for the SDK context
        sdk_workflow_config = execution_context.workflow_config.copy()
        if "workflow_id" not in sdk_workflow_config and execution_context.workflow_id:
            sdk_workflow_config["workflow_id"] = execution_context.workflow_id

        # Convert POC execution context to SDK execution context
        sdk_context = SDKExecutionContext(
            workflow_config=sdk_workflow_config,
            user_context=UserContext(
                user_id=execution_context.user_context.user_id if execution_context.user_context else None,
                session_id=execution_context.user_context.session_id if execution_context.user_context else None,
                organization_id=execution_context.user_context.organization_id if execution_context.user_context else None,
            ),
            execution_id=execution_context.execution_id,
        )
        # Pass the POC's stream_manager so SSE events are routed correctly
        return await _execute_a2a_agent(step_config, input_data, sdk_context, stream_mgr=stream_manager)

    # Get agent configuration
    agent_name = config.get("agent_name", "Assistant")
    system_prompt = config.get("system_prompt", "You are a helpful assistant.")
    query_template = config.get("query", "")
    force_real_llm = config.get("force_real_llm", False)

    # Include chat history/messages: prefer step-specific messages if present, else Trigger
    try:
        # Step-scoped messages (interactive chat)
        step_msgs = []
        try:
            from ..db.service import DatabaseService
            from ..db.database import get_db_session

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
            # Convert to simple role/content list
            step_msgs = [
                {
                    "role": m.get("role", "user"),
                    "content": m.get("content", ""),
                    **({"metadata": m.get("metadata")} if m.get("metadata") else {}),
                }
                for m in step_msgs
            ]
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

    agent = AgentStep(
        name=agent_name,
        system_prompt=system_prompt,
        tools=load_agent_db_tool_schemas(agent_name=agent_name),
        force_real_llm=force_real_llm,
        connected_agents=connected_agents,
    )

    # If interactive by default unless explicitly disabled
    interactive = config.get("interactive", True)
    multi_turn = bool(config.get("multi_turn", False))

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

    # Optional LLM params from config (e.g., max_tokens, temperature)
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
        if llm_params:
            input_data["_llm_params"] = llm_params
    except Exception:
        pass

    # Execute query, optionally streaming deltas (genuine streaming via llm-gateway when available)
    stream_enabled = bool(config.get("stream", False))
    accumulated = ""
    if stream_enabled:
        try:
            backend = step_config.get("_backend")
            # If tools are available, or backend is DBOS (for now), fall back to pseudo/one-shot to ensure progress
            llm_tools_for_agent = load_agent_db_tool_schemas(agent_name=agent_name)
            if llm_tools_for_agent or backend == "dbos":
                # Pseudo-streaming: run once and emit deltas
                tmp_result = await agent.execute(query, context=input_data)
                full_text = str((tmp_result or {}).get("response") or (tmp_result or {}).get("output") or "")
                chunk_size = max(40, min(400, len(full_text) // 20 or 40))
                sid = step_config.get("step_id") or ""
                for i in range(0, len(full_text), chunk_size):
                    delta = full_text[i : i + chunk_size]
                    accumulated += delta
                    try:
                        if sid:
                            evt = create_step_event(
                                execution_id=execution_context.execution_id,
                                step_id=sid,
                                step_status="running",
                                workflow_id=execution_context.workflow_id,
                                output_data={"delta": delta, "accumulated_len": len(accumulated)},
                            )
                            await stream_manager.emit_execution_event(evt)
                            if execution_context.workflow_id:
                                await stream_manager.emit_workflow_event(evt)
                    except Exception:
                        pass
                result = {**tmp_result, "response": accumulated}
            else:
                # Build messages chronologically from context
                messages: List[Dict[str, str]] = []
                ctx_msgs = input_data.get("messages") or input_data.get("chat_history")
                if isinstance(ctx_msgs, list):
                    # Ensure order and shape
                    for m in ctx_msgs:
                        if isinstance(m, dict) and "role" in m and "content" in m:
                            messages.append({"role": str(m["role"]), "content": str(m["content"])})
                # Ensure the last message is the current user query
                if not (messages and messages[-1].get("role") == "user" and messages[-1].get("content") == query):
                    messages.append({"role": "user", "content": query})

                # LLM params
                _llm = input_data.get("_llm_params", {}) if isinstance(input_data, dict) else {}
                _max_tokens = _llm.get("max_tokens")
                if not isinstance(_max_tokens, int) or _max_tokens <= 0:
                    _max_tokens = 600
                _temperature = _llm.get("temperature")

                # Provider config and model
                provider_config = {"type": "openai_textgen"}
                model_name = TextGenerationModelName.OPENAI_gpt_4o  # type: ignore
                sys_msg_val = system_prompt or "You are a helpful assistant."

                sid = step_config.get("step_id") or ""

                # Use llm-gateway streaming API
                svc = TextGenerationService()  # type: ignore
                for ev in svc.stream(
                    prompt="",
                    config=provider_config,
                    max_tokens=_max_tokens,
                    model_name=model_name,
                    sys_msg=sys_msg_val,
                    retries=None,
                    temperature=_temperature,
                    tools=None,
                    tool_choice=None,
                    messages=messages,
                ):
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
                                    output_data={"delta": delta, "accumulated_len": len(accumulated)},
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
            logger.debug(f"Streaming emission failed, falling back to non-streaming: {_se}, {_se.__traceback__}")
            result = await agent.execute(query, context=input_data)
    else:
        result = await agent.execute(query, context=input_data)

    # Persist assistant response to DB as a message for this step
    try:
        from ..db.service import DatabaseService
        from ..db.database import get_db_session

        sid = step_config.get("step_id")
        if sid and isinstance(result, dict):
            assistant_content = result.get("response") or result.get("output")
            if assistant_content is not None:
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
    except Exception as _persist_e:
        logger.debug(f"Could not persist assistant message: {_persist_e}")

    # If multi_turn and not marked final, keep waiting for more input with agent response
    if interactive and multi_turn and not bool(input_data.get("final_turn")):
        return {
            "status": "waiting",
            "waiting_for": "user_input",
            "step_type": "interactive_agent",
            "agent_response": result,
            "agent_config": {"agent_name": agent_name},
        }

    return result
