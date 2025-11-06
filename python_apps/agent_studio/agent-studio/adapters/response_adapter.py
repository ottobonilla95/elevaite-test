"""
Response Adapter - Converts SDK responses to Agent Studio API format

This adapter handles the conversion of SDK responses back to Agent Studio's
expected format for backwards compatibility.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID
from sqlmodel import Session, select


class ResponseAdapter:
    """Adapts SDK responses to Agent Studio API format"""

    @staticmethod
    def _get_agent_response(agent_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """
        Fetch agent data from database and convert to AgentResponse format.

        Returns a dict matching the AgentResponse schema which requires:
        - id, agent_id, name, system_prompt, functions, and other agent fields
        """
        if not db or not agent_id:
            return None

        # Try to fetch from database
        try:
            from workflow_core_sdk.services.agents_service import AgentsService
            from workflow_core_sdk.services.prompts_service import PromptsService

            # Get agent from SDK
            agent = AgentsService.get_agent(db, agent_id)

            if not agent:
                return None

            # Get system prompt
            system_prompt = None
            if agent.system_prompt_id:
                system_prompt = PromptsService.get_prompt(db, str(agent.system_prompt_id))

            # Load bound tools for this agent and convert to OpenAI function specs
            functions: list[dict] = []
            try:
                from workflow_core_sdk.services.agents_service import AgentsService as _AgentsService
                from workflow_core_sdk.services.tools_service import ToolsService as _ToolsService
                from workflow_core_sdk.tools.registry import tool_registry as _tool_registry

                bindings = _AgentsService.list_agent_tools(db, str(agent.id))
                for b in bindings:
                    if not getattr(b, "is_active", True):
                        continue
                    tool_name = None
                    tool_description = ""
                    tool_parameters = {}
                    # Try DB tool first
                    try:
                        db_tool = _ToolsService.get_db_tool_by_id(db, str(b.tool_id))
                        if db_tool:
                            tool_name = db_tool.name
                            tool_description = db_tool.description or ""
                            if db_tool.parameters_schema:
                                tool_parameters = db_tool.parameters_schema
                    except Exception:
                        pass
                    # Fallback to unified registry
                    if not tool_name:
                        try:
                            for ut in _tool_registry.get_unified_tools(db):
                                if getattr(ut, "db_id", None) and str(ut.db_id) == str(b.tool_id):
                                    tool_name = ut.name
                                    tool_description = ut.description or ""
                                    if getattr(ut, "parameters_schema", None):
                                        tool_parameters = ut.parameters_schema
                                    break
                        except Exception:
                            pass
                    if not tool_name:
                        tool_name = str(b.tool_id)
                    functions.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "description": tool_description,
                                "parameters": (
                                    getattr(b, "override_parameters", None)
                                    or tool_parameters
                                    or {"type": "object", "properties": {}}
                                ),
                            },
                        }
                    )
            except Exception as e:
                # If tool loading fails, log the error and continue with empty functions
                import logging

                logger = logging.getLogger(__name__)
                logger.error(f"Error loading tools for agent {agent_id}: {str(e)}", exc_info=True)
                functions = []

            # Build response matching AgentResponse schema
            response = {
                "id": 0,  # Placeholder - Agent Studio uses int IDs
                "agent_id": str(agent.id),
                "name": agent.name,
                "agent_type": "router",
                "description": agent.description or "",
                "functions": functions,
                "routing_options": {},
                "short_term_memory": False,
                "long_term_memory": False,
                "reasoning": False,
                "input_type": ["text"],
                "output_type": ["text"],
                "response_type": "markdown",
                "max_retries": 3,
                "deployed": False,
                "status": agent.status or "active",
                "collaboration_mode": "single",
                "available_for_deployment": False,
                "system_prompt_id": str(agent.system_prompt_id) if agent.system_prompt_id else "",
                "system_prompt": {
                    "id": int(str(system_prompt.id).replace("-", "")[:16], 16) % (2**31) if system_prompt else 0,
                    "pid": str(system_prompt.id) if system_prompt else "",
                    "prompt_label": system_prompt.prompt_label if system_prompt else "Default",
                    "prompt": system_prompt.prompt if system_prompt else "",
                    "unique_label": system_prompt.unique_label if system_prompt else "",
                    "app_name": system_prompt.app_name if system_prompt else "",
                    "ai_model_provider": system_prompt.ai_model_provider if system_prompt else "",
                    "ai_model_name": system_prompt.ai_model_name if system_prompt else "",
                    "tags": system_prompt.tags if system_prompt else [],
                    "hyper_parameters": system_prompt.hyper_parameters if system_prompt else {},
                    "variables": system_prompt.variables if system_prompt else {},
                    "sha_hash": "",
                    "is_deployed": False,
                    "version": "1.0",
                    "created_time": system_prompt.created_time.isoformat()
                    if system_prompt and system_prompt.created_time
                    else "",
                    "deployed_time": None,
                    "last_deployed": None,
                }
                if system_prompt
                else {
                    "id": 0,
                    "pid": "",
                    "prompt_label": "Default",
                    "prompt": "",
                    "unique_label": "",
                    "app_name": "",
                    "ai_model_provider": "",
                    "ai_model_name": "",
                    "tags": [],
                    "hyper_parameters": {},
                    "variables": {},
                    "sha_hash": "",
                    "is_deployed": False,
                    "version": "1.0",
                    "created_time": "",
                    "deployed_time": None,
                    "last_deployed": None,
                },
            }
            return response
        except Exception:
            # If query fails, return None to indicate missing agent
            return None

    @staticmethod
    def adapt_execution_response(sdk_execution: Any) -> Dict[str, Any]:
        """
        Convert SDK execution response to Agent Studio format

        SDK format:
        {
            "id": "...",
            "workflow_id": "...",
            "status": "pending|running|completed|failed",
            "started_at": "...",
            "completed_at": "...",
            "result": {...},
            "error": "...",
            "current_step_id": "..."
        }

        Agent Studio format:
        {
            "execution_id": "...",
            "workflow_id": "...",
            "status": "queued|running|completed|failed",
            "started_at": "...",
            "completed_at": "...",
            "result": {...},
            "error": "...",
            "current_step": "..."
        }
        """
        # Handle both dict and object responses
        if isinstance(sdk_execution, dict):
            exec_dict = sdk_execution
        else:
            # Convert SQLModel/Pydantic object to dict
            exec_dict = (
                sdk_execution.model_dump()
                if hasattr(sdk_execution, "model_dump")
                else sdk_execution.dict()
                if hasattr(sdk_execution, "dict")
                else {}
            )

        # Map status values
        status_map = {
            "pending": "queued",
            "running": "running",
            "completed": "completed",
            "failed": "failed",
            "cancelled": "cancelled",
        }

        sdk_status = exec_dict.get("status", "pending")
        as_status = status_map.get(sdk_status, sdk_status)

        # Build Agent Studio response
        as_response = {
            "execution_id": str(exec_dict.get("id", "")),
            "workflow_id": str(exec_dict.get("workflow_id", "")),
            "status": as_status,
        }

        # Add optional fields if present
        if "started_at" in exec_dict and exec_dict["started_at"]:
            as_response["started_at"] = exec_dict["started_at"]

        if "completed_at" in exec_dict and exec_dict["completed_at"]:
            as_response["completed_at"] = exec_dict["completed_at"]

        if "result" in exec_dict:
            as_response["result"] = exec_dict["result"]

        if "error" in exec_dict:
            as_response["error"] = exec_dict["error"]

        # Map current_step_id to current_step
        if "current_step_id" in exec_dict:
            as_response["current_step"] = exec_dict["current_step_id"]

        # Add metadata if present
        if "metadata" in exec_dict:
            as_response["metadata"] = exec_dict["metadata"]

        # Add user context fields at top level for backwards compat
        if "user_context" in exec_dict and exec_dict["user_context"]:
            user_ctx = exec_dict["user_context"]
            if "user_id" in user_ctx:
                as_response["user_id"] = user_ctx["user_id"]
            if "session_id" in user_ctx:
                as_response["session_id"] = user_ctx["session_id"]

        return as_response

    @staticmethod
    def adapt_execution_list_response(sdk_executions: List[Any]) -> List[Dict[str, Any]]:
        """Convert list of SDK executions to Agent Studio format"""
        return [ResponseAdapter.adapt_execution_response(exec) for exec in sdk_executions]

    @staticmethod
    def adapt_workflow_response(sdk_workflow: Any, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        Convert SDK workflow response to Agent Studio format

        SDK format:
        {
            "id": "...",
            "name": "...",
            "configuration": {
                "steps": [...]
            },
            "status": "draft|active|inactive",
            "editable": true
        }

        Agent Studio format:
        {
            "workflow_id": "...",
            "name": "...",
            "configuration": {
                "agents": [...],
                "connections": [...],
                "steps": [...]
            },
            "is_active": true,
            "is_editable": true
        }
        """
        # Handle both dict and object responses
        if isinstance(sdk_workflow, dict):
            wf_dict = sdk_workflow
        else:
            wf_dict = (
                sdk_workflow.model_dump()
                if hasattr(sdk_workflow, "model_dump")
                else sdk_workflow.dict()
                if hasattr(sdk_workflow, "dict")
                else {}
            )

        # Build Agent Studio response
        # Generate a deterministic integer ID from UUID for backwards compatibility
        workflow_uuid = wf_dict.get("id", "")

        # Try to convert UUID to int, fallback to hash if not a valid UUID
        try:
            int_id = int(str(workflow_uuid).replace("-", "")[:16], 16) % (2**31)
        except (ValueError, AttributeError):
            # If not a valid UUID, use hash of the string
            int_id = abs(hash(str(workflow_uuid))) % (2**31)

        as_response = {
            "id": int_id,  # Integer ID for backwards compatibility
            "workflow_id": str(workflow_uuid),  # UUID as workflow_id
            "name": wf_dict.get("name", ""),
            "description": wf_dict.get("description", ""),
            "version": wf_dict.get("version", "1.0.0"),
        }

        # Convert configuration
        sdk_config = wf_dict.get("configuration", {})
        sdk_steps = sdk_config.get("steps", [])

        # Separate agent steps from other steps
        # Support both "agent" (migrated) and "agent_execution" (new) step types
        agents = []
        connections = []
        other_steps = []

        for step in sdk_steps:
            step_type = step.get("step_type")
            if step_type in ("agent", "agent_execution"):
                # Convert to agent format
                cfg = step.get("config", {}) or {}
                agent = {
                    "agent_id": step.get("step_id"),
                    "node_id": step.get("step_id"),
                    "name": step.get("name", "Agent"),
                    # Only propagate explicit agent_type; do not default to an invalid value
                    "agent_type": cfg.get("agent_type"),
                    "config": cfg,
                    "parameters": step.get("parameters", {}),
                    "node_type": "agent",
                }

                # Include position if available (from migrated workflows)
                if "position" in step:
                    agent["position"] = step["position"]

                agents.append(agent)

                # Create connections from dependencies
                for dep_id in step.get("dependencies", []):
                    connection = {
                        "source_agent_id": dep_id,
                        "target_agent_id": step.get("step_id"),
                        "connection_type": "default",
                    }
                    connections.append(connection)
            elif step_type == "tool_execution":
                # Represent tool steps as nodes for Agent Studio UI
                cfg = step.get("config", {}) or {}
                tool_agent = {
                    "agent_id": step.get("step_id"),
                    "node_id": step.get("step_id"),
                    "name": step.get("name") or cfg.get("tool_name") or "Tool",
                    "agent_type": "tool",
                    "config": cfg,
                    "parameters": step.get("parameters", {}),
                    "node_type": "tool",
                }
                if "position" in step:
                    tool_agent["position"] = step["position"]
                agents.append(tool_agent)

                # Create connections from dependencies (source -> this tool)
                for dep_id in step.get("dependencies", []):
                    connection = {
                        "source_agent_id": dep_id,
                        "target_agent_id": step.get("step_id"),
                        "connection_type": "default",
                    }
                    connections.append(connection)
            else:
                other_steps.append(step)

        # Add connections from SDK configuration (migrated workflows)
        sdk_connections = sdk_config.get("connections", [])
        for conn in sdk_connections:
            connection = {
                "source_agent_id": conn.get("source_step_id"),
                "target_agent_id": conn.get("target_step_id"),
                "connection_type": conn.get("connection_type", "default"),
                "priority": conn.get("priority", 0),
            }
            # Avoid duplicates (connections might be in both dependencies and connections array)
            if connection not in connections:
                connections.append(connection)

        # Build Agent Studio configuration
        as_response["configuration"] = {
            "agents": agents,
            "connections": connections,
            "steps": other_steps,
        }

        # Map status to is_active
        sdk_status = wf_dict.get("status", "draft")
        as_response["is_active"] = sdk_status == "active"
        as_response["is_deployed"] = sdk_status == "active"

        # Map editable to is_editable
        as_response["is_editable"] = wf_dict.get("editable", True)

        # Add optional fields
        if "tags" in wf_dict:
            as_response["tags"] = wf_dict["tags"]

        if "created_by" in wf_dict:
            as_response["created_by"] = wf_dict["created_by"]

        if "created_at" in wf_dict:
            as_response["created_at"] = wf_dict["created_at"]

        # updated_at is required by WorkflowResponse, default to created_at if not present
        if "updated_at" in wf_dict and wf_dict["updated_at"] is not None:
            as_response["updated_at"] = wf_dict["updated_at"]
        else:
            as_response["updated_at"] = wf_dict.get("created_at", wf_dict.get("created_at"))

        # Build workflow_agents array from agents configuration
        # This is what the frontend expects in WorkflowResponse.workflow_agents
        workflow_agents = []
        for idx, agent in enumerate(agents):
            agent_id = agent.get("agent_id")
            agent_response = ResponseAdapter._get_agent_response(agent_id, db)

            # If not found in DB and this is a tool node, synthesize a minimal AgentResponse
            if agent_response is None:
                if agent.get("agent_type") == "tool" or agent.get("node_type") == "tool":
                    cfg = agent.get("config", {}) or {}
                    tool_name = agent.get("name") or cfg.get("tool_name") or "Tool"
                    agent_response = {
                        "id": 0,
                        "agent_id": str(agent_id),
                        "name": tool_name,
                        "agent_type": "tool",
                        "description": "",
                        "functions": [],
                        "routing_options": {},
                        "short_term_memory": False,
                        "long_term_memory": False,
                        "reasoning": False,
                        "input_type": ["text"],
                        "output_type": ["text"],
                        "response_type": "markdown",
                        "max_retries": 3,
                        "deployed": False,
                        "status": "active",
                        "collaboration_mode": "single",
                        "available_for_deployment": False,
                        "system_prompt_id": "",
                        "system_prompt": {
                            "id": 0,
                            "pid": "",
                            "prompt_label": tool_name,
                            "prompt": "",
                            "unique_label": "",
                            "app_name": "",
                            "ai_model_provider": "",
                            "ai_model_name": "",
                            "tags": [],
                            "hyper_parameters": {},
                            "variables": {},
                            "sha_hash": "",
                            "is_deployed": False,
                            "version": "1.0",
                            "created_time": "",
                            "deployed_time": None,
                            "last_deployed": None,
                        },
                    }
                else:
                    # Skip agents that don't exist in database and are not tools
                    continue

            # Override agent_type from configuration if it is an allowed type (not 'tool')
            cfg_type = agent.get("agent_type") or (agent.get("config", {}) or {}).get("agent_type")
            allowed_types = {"router", "web_search", "data", "troubleshooting", "api", "weather", "toshiba", "vectorizer"}
            if isinstance(cfg_type, str) and cfg_type in allowed_types:
                agent_response["agent_type"] = cfg_type

            # Determine node_type for this workflow agent (agent vs tool)
            node_type_val = agent.get("node_type") or ("tool" if (agent.get("agent_type") == "tool") else "agent")

            workflow_agent = {
                "workflow_id": str(workflow_uuid),
                "agent_id": agent_id,
                "node_id": agent.get("node_id"),
                "agent_config": agent.get("config", {}),
                "node_type": node_type_val,
                "id": idx,  # Use index as ID for now
                "added_at": wf_dict.get("created_at", ""),
                # Include position if available
                "position_x": agent.get("position", {}).get("x") if agent.get("position") else None,
                "position_y": agent.get("position", {}).get("y") if agent.get("position") else None,
                # Real or synthesized agent data
                "agent": agent_response,
            }
            workflow_agents.append(workflow_agent)

        # Build workflow_connections array from connections configuration
        # This is what the frontend expects in WorkflowResponse.workflow_connections
        workflow_connections = []
        for idx, conn in enumerate(connections):
            source_agent_id = conn.get("source_agent_id")
            target_agent_id = conn.get("target_agent_id")

            # Try DB lookups first
            source_agent_response = ResponseAdapter._get_agent_response(source_agent_id, db)
            target_agent_response = ResponseAdapter._get_agent_response(target_agent_id, db)

            # If missing, synthesize stubs for tool nodes so UI can render connections
            if source_agent_response is None:
                src_agent = next((a for a in agents if a.get("agent_id") == source_agent_id), None)
                if src_agent and (src_agent.get("agent_type") == "tool" or src_agent.get("node_type") == "tool"):
                    cfg = src_agent.get("config", {}) or {}
                    name = src_agent.get("name") or cfg.get("tool_name") or "Tool"
                    source_agent_response = {
                        "id": 0,
                        "agent_id": str(source_agent_id),
                        "name": name,
                        "agent_type": None,
                        "description": "",
                        "functions": [],
                        "routing_options": {},
                        "short_term_memory": False,
                        "long_term_memory": False,
                        "reasoning": False,
                        "input_type": ["text"],
                        "output_type": ["text"],
                        "response_type": "markdown",
                        "max_retries": 3,
                        "deployed": False,
                        "status": "active",
                        "collaboration_mode": "single",
                        "available_for_deployment": False,
                        "system_prompt_id": "",
                        "system_prompt": {
                            "id": 0,
                            "pid": "",
                            "prompt_label": name,
                            "prompt": "",
                            "unique_label": "",
                            "app_name": "",
                            "ai_model_provider": "",
                            "ai_model_name": "",
                            "tags": [],
                            "hyper_parameters": {},
                            "variables": {},
                            "sha_hash": "",
                            "is_deployed": False,
                            "version": "1.0",
                            "created_time": "",
                            "deployed_time": None,
                            "last_deployed": None,
                        },
                    }

            if target_agent_response is None:
                tgt_agent = next((a for a in agents if a.get("agent_id") == target_agent_id), None)
                if tgt_agent and (tgt_agent.get("agent_type") == "tool" or tgt_agent.get("node_type") == "tool"):
                    cfg = tgt_agent.get("config", {}) or {}
                    name = tgt_agent.get("name") or cfg.get("tool_name") or "Tool"
                    target_agent_response = {
                        "id": 0,
                        "agent_id": str(target_agent_id),
                        "name": name,
                        "agent_type": None,
                        "description": "",
                        "functions": [],
                        "routing_options": {},
                        "short_term_memory": False,
                        "long_term_memory": False,
                        "reasoning": False,
                        "input_type": ["text"],
                        "output_type": ["text"],
                        "response_type": "markdown",
                        "max_retries": 3,
                        "deployed": False,
                        "status": "active",
                        "collaboration_mode": "single",
                        "available_for_deployment": False,
                        "system_prompt_id": "",
                        "system_prompt": {
                            "id": 0,
                            "pid": "",
                            "prompt_label": name,
                            "prompt": "",
                            "unique_label": "",
                            "app_name": "",
                            "ai_model_provider": "",
                            "ai_model_name": "",
                            "tags": [],
                            "hyper_parameters": {},
                            "variables": {},
                            "sha_hash": "",
                            "is_deployed": False,
                            "version": "1.0",
                            "created_time": "",
                            "deployed_time": None,
                            "last_deployed": None,
                        },
                    }

            # Override agent_type from configuration if it is an allowed type (not 'tool')
            allowed_types = {"router", "web_search", "data", "troubleshooting", "api", "weather", "toshiba", "vectorizer"}
            src_agent = next((a for a in agents if a.get("agent_id") == source_agent_id), None)
            if source_agent_response is not None and src_agent is not None:
                cfg_type = src_agent.get("agent_type") or (src_agent.get("config", {}) or {}).get("agent_type")
                if isinstance(cfg_type, str) and cfg_type in allowed_types:
                    source_agent_response["agent_type"] = cfg_type
            tgt_agent = next((a for a in agents if a.get("agent_id") == target_agent_id), None)
            if target_agent_response is not None and tgt_agent is not None:
                cfg_type = tgt_agent.get("agent_type") or (tgt_agent.get("config", {}) or {}).get("agent_type")
                if isinstance(cfg_type, str) and cfg_type in allowed_types:
                    target_agent_response["agent_type"] = cfg_type

            # Skip only if still missing (neither real agent nor tool stub)
            if source_agent_response is None or target_agent_response is None:
                continue

            workflow_connection = {
                "workflow_id": str(workflow_uuid),
                "source_agent_id": source_agent_id,
                "target_agent_id": target_agent_id,
                "connection_type": conn.get("connection_type", "default"),
                "conditions": conn.get("conditions", {}),
                "priority": conn.get("priority", 0),
                "source_handle": conn.get("source_handle"),
                "target_handle": conn.get("target_handle"),
                "id": idx,  # Use index as ID for now
                "created_at": wf_dict.get("created_at", ""),
                # Fetch real agent data from database
                "source_agent": source_agent_response,
                "target_agent": target_agent_response,
            }
            workflow_connections.append(workflow_connection)

        as_response["workflow_agents"] = workflow_agents
        as_response["workflow_connections"] = workflow_connections
        as_response["workflow_deployments"] = []

        # Add deployed_at field
        as_response["deployed_at"] = wf_dict.get("deployed_at")

        return as_response

    @staticmethod
    def adapt_workflow_list_response(sdk_workflows: List[Any], db: Optional[Session] = None) -> List[Dict[str, Any]]:
        """Convert list of SDK workflows to Agent Studio format"""
        return [ResponseAdapter.adapt_workflow_response(wf, db) for wf in sdk_workflows]

    @staticmethod
    def adapt_error_response(error: Exception, status_code: int = 500) -> Dict[str, Any]:
        """
        Convert SDK error to Agent Studio error format

        Maintains consistent error response structure
        """
        return {
            "error": str(error),
            "detail": str(error),
            "status_code": status_code,
        }

    @staticmethod
    def adapt_execution_status_response(sdk_execution: Any) -> Dict[str, Any]:
        """
        Convert SDK execution to Agent Studio status response

        This is the same as adapt_execution_response but may include
        additional status-specific fields in the future
        """
        return ResponseAdapter.adapt_execution_response(sdk_execution)

    @staticmethod
    def adapt_execution_result_response(sdk_execution: Any) -> Any:
        """
        Extract and return just the result from SDK execution

        Agent Studio's /executions/{id}/result endpoint returns just the result,
        not the full execution object
        """
        if isinstance(sdk_execution, dict):
            return sdk_execution.get("result")
        else:
            return getattr(sdk_execution, "result", None)
