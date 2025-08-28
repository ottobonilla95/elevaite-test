"""
AI and LLM Processing Steps

Steps that integrate with AI models and language models for
intelligent processing, agent execution, and AI-powered workflows.
"""

import uuid
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Union
import logging

# Import tools system
from ..tools import get_tool_by_name

# DB access for dynamic agent tools
from sqlmodel import select
from ..db.database import get_db_session
from ..db.models import Agent as DBAgent, Prompt as DBPrompt, AgentToolBinding as DBAgentToolBinding, Tool as DBTool

from ..execution_context import ExecutionContext

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
            model_name = TextGenerationModelName.OPENAI_gpt_4o_mini  # type: ignore

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
                response = await asyncio.to_thread(
                    self.llm_service.generate,
                    current_prompt,
                    config,
                    None,  # max_tokens
                    model_name,
                    sys_msg,
                    None,  # retries
                    None,  # temperature
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

                # Execute tool calls and prepare concise summaries for the follow-up LLM call
                iteration_results: List[Dict[str, Any]] = []
                for tool_call in response.tool_calls or []:
                    try:
                        tool_result = await self._execute_tool_call(tool_call)
                        tool_calls_trace.append(tool_result)

                        summary: Dict[str, Any] = {
                            "name": tool_result.get("tool_name"),
                            "success": tool_result.get("success", False),
                        }
                        if tool_result.get("success"):
                            res_val = tool_result.get("result")
                            # Prefer child agent response when present
                            if isinstance(res_val, dict) and res_val.get("response"):
                                summary["output"] = res_val.get("response")
                            else:
                                try:
                                    summary["output"] = res_val if isinstance(res_val, str) else json.dumps(res_val)[:1500]
                                except Exception:
                                    summary["output"] = str(res_val)[:1500]
                        else:
                            summary["error"] = str(tool_result.get("error", "Unknown error"))[:400]
                        iteration_results.append(summary)
                    except Exception as e:
                        err = {
                            "tool_name": getattr(tool_call, "name", "unknown"),
                            "success": False,
                            "error": str(e)[:400],
                        }
                        tool_calls_trace.append(err)
                        iteration_results.append({"name": err["tool_name"], "success": False, "error": err["error"]})

                # Feed tool results back into the next round
                tools_json = json.dumps(iteration_results, ensure_ascii=False)
                # Append assistant tool summary as a message and follow-up user prompt for clarity
                messages.append(
                    {
                        "role": "assistant",
                        "content": f"Tool call results (JSON): {tools_json}",
                    }
                )
                messages.append(
                    {
                        "role": "user",
                        "content": "Using these tool results, provide the best possible answer to the user's query.",
                    }
                )
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
    """

    _ = execution_context  # currently unused, reserved for future scoping/analytics
    config = step_config.get("config", {})

    # Get agent configuration
    agent_name = config.get("agent_name", "Assistant")
    system_prompt = config.get("system_prompt", "You are a helpful assistant.")
    query_template = config.get("query", "")
    force_real_llm = config.get("force_real_llm", False)

    # Ensure current_message is available from Trigger output if not present
    try:
        if isinstance(input_data, dict) and "current_message" not in input_data:
            trig = execution_context.step_io_data.get("trigger")
            if isinstance(trig, dict):
                msgs = trig.get("messages") or []
                if isinstance(msgs, list) and msgs:
                    for m in reversed(msgs):
                        if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str):
                            input_data["current_message"] = m["content"]
                            break
    except Exception as e:
        logger.debug(f"Could not derive current_message from trigger: {e}")

    # Include chat history/messages from Trigger in the agent context
    try:
        trig = execution_context.step_io_data.get("trigger")
        if isinstance(trig, dict):
            msgs = trig.get("messages")
            if isinstance(msgs, list) and msgs and "messages" not in input_data:
                input_data["messages"] = msgs
                # Also provide a common alias
                input_data.setdefault("chat_history", msgs)
    except Exception as e:
        logger.debug(f"Could not include messages from trigger: {e}")

    # Process query template with input data (e.g., "{current_message}")
    query = query_template
    if isinstance(query_template, str) and "{" in query_template:
        try:
            query = query_template.format(**input_data)
        except KeyError as e:
            logger.warning(f"Template variable not found: {e}")

    # Create agent; remove step-config tool support and rely on DB-bound tools only
    connected_agents = config.get("connected_agents", [])

    agent = AgentStep(
        name=agent_name,
        system_prompt=system_prompt,
        tools=load_agent_db_tool_schemas(agent_name=agent_name),
        force_real_llm=force_real_llm,
        connected_agents=connected_agents,
    )

    # Execute query
    result = await agent.execute(query, context=input_data)

    return result
