"""
Request Adapter - Converts Agent Studio API requests to SDK format

This adapter handles the conversion of incoming API requests from Agent Studio's
format to the SDK's expected format.

Node Type Discrimination:
- Uses `node_type` field to discriminate between "agent" and "tool" nodes
- `node_type` = "agent": Agent execution step (uses LLM, has agent_type like "router", "web_search", etc.)
- `node_type` = "tool": Tool execution step (calls a specific tool function)
- `agent_type` field is preserved for agent-specific information (router, web_search, data, etc.)
- Backward compatibility: Falls back to checking `agent_type == "tool"` if `node_type` is not present
"""

from typing import Dict, Any, Optional, List
from uuid import UUID


class RequestAdapter:
    """Adapts Agent Studio API requests to SDK format"""

    @staticmethod
    def adapt_workflow_execute_request(as_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Agent Studio workflow execution request to SDK format

        Agent Studio format:
        {
            "user_message": "...",
            "session_id": "...",
            "user_id": "...",
            "attachments": [...],
            "metadata": {...}
        }

        SDK format:
        {
            "input": {
                "message": "...",
                "attachments": [...]
            },
            "user_context": {
                "user_id": "...",
                "session_id": "...",
                "organization_id": "..."
            },
            "metadata": {...}
        }
        """
        # Extract user message (could be in different fields)
        message = (
            as_request.get("user_message") or as_request.get("message") or as_request.get("input", {}).get("message") or ""
        )

        # Build input data
        input_data = {
            "message": message,
        }

        # Add attachments if present
        if "attachments" in as_request:
            input_data["attachments"] = as_request["attachments"]

        # Add any other input fields
        if "input" in as_request and isinstance(as_request["input"], dict):
            input_data.update(as_request["input"])

        # Build user context
        user_context = {}

        if "user_id" in as_request:
            user_context["user_id"] = as_request["user_id"]

        if "session_id" in as_request:
            user_context["session_id"] = as_request["session_id"]

        if "organization_id" in as_request:
            user_context["organization_id"] = as_request["organization_id"]

        # Build SDK request
        sdk_request = {
            "input": input_data,
            "user_context": user_context,
        }

        # Add metadata if present
        if "metadata" in as_request:
            sdk_request["metadata"] = as_request["metadata"]

        # Add execution backend if specified
        if "execution_backend" in as_request:
            sdk_request["execution_backend"] = as_request["execution_backend"]

        return sdk_request

    @staticmethod
    def adapt_workflow_create_request(as_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Agent Studio workflow creation request to SDK format

        Agent Studio format:
        {
            "name": "...",
            "version": "...",
            "configuration": {
                "agents": [...],
                "connections": [...],
                "steps": [...]
            }
        }

        SDK format:
        {
            "name": "...",
            "version": "...",
            "configuration": {
                "steps": [...]  // Unified steps array
            }
        }
        """
        # Start with base fields
        sdk_request = {
            "name": as_request.get("name", "Untitled Workflow"),
            "description": as_request.get("description", ""),
            "version": as_request.get("version", "1.0.0"),
        }

        # Convert configuration
        as_config = as_request.get("configuration", {})
        sdk_steps = []

        # Convert agents to agent_execution steps
        agents = as_config.get("agents", [])
        connections = as_config.get("connections", [])

        # Build a map of agent_id -> agent for quick lookup (needed for callable agent pattern)
        agent_map = {agent.get("agent_id") or agent.get("node_id"): agent for agent in agents}

        # Identify which agents are targets of agent-to-agent connections
        # These will be added as callable functions, not as separate steps
        target_agent_ids = set()
        for connection in connections:
            source_id = connection.get("source_agent_id")
            target_id = connection.get("target_agent_id")

            if source_id and target_id:
                # Check if both are agents (not tools)
                source_agent = agent_map.get(source_id)
                target_agent = agent_map.get(target_id)

                if source_agent and target_agent:
                    source_node_type = source_agent.get("node_type") or (
                        "tool" if source_agent.get("agent_type") == "tool" else "agent"
                    )
                    target_node_type = target_agent.get("node_type") or (
                        "tool" if target_agent.get("agent_type") == "tool" else "agent"
                    )

                    # If both are agents, mark target as callable (not a step)
                    if source_node_type == "agent" and target_node_type == "agent":
                        target_agent_ids.add(target_id)

        # Convert agents to steps, but skip target agents (they'll be callable functions)
        for agent in agents:
            agent_id = agent.get("agent_id") or agent.get("node_id")

            # Skip agents that are targets of agent-to-agent connections
            if agent_id in target_agent_ids:
                continue

            # Determine node type: check node_type first (preferred), fall back to agent_type for backward compatibility
            node_type = agent.get("node_type") or ("tool" if agent.get("agent_type") == "tool" else "agent")

            # Check if this is a tool node
            if node_type == "tool":
                # Create a tool execution step
                config = agent.get("config", {})
                tool_name = config.get("tool_name", "unknown_tool")
                step_id = agent_id or f"tool_{tool_name}"

                # Optional UI metadata for labeling/description of tool steps
                step_label = agent.get("step_label") or config.get("step_label")
                step_description = agent.get("step_description") or config.get("step_description") or agent.get("description")

                # Build config, keeping optional metadata inside config for round-tripping
                step_config = {
                    "tool_name": tool_name,
                    "param_mapping": config.get("param_mapping", {}),
                    "static_params": config.get("static_params", {}),
                }
                if step_label:
                    step_config["step_label"] = step_label
                if step_description:
                    step_config["step_description"] = step_description

                # Preserve any additional arbitrary keys from the incoming config for round-trip fidelity
                known_keys = {"tool_name", "param_mapping", "static_params", "step_label", "step_description", "name"}
                for k, v in (config or {}).items():
                    if k not in known_keys:
                        step_config[k] = v

                step = {
                    "step_id": step_id,
                    "step_type": "tool_execution",
                    "name": config.get("name", tool_name),
                    "config": step_config,
                    "dependencies": [],
                    "input_mapping": {},
                }

                # Preserve position data if present (for UI metadata)
                if "position" in agent:
                    step["position"] = agent["position"]

                sdk_steps.append(step)
                continue

            # Create agent execution step (all agents become steps now)
            step = {
                "step_id": agent_id,
                "step_type": "agent_execution",
                "name": agent.get("name", "Agent"),
                "config": agent.get("config", {}),
                "parameters": agent.get("parameters", {}),
                "dependencies": [],
                "input_mapping": {},
            }

            # Preserve position data if present (for UI metadata)
            if "position" in agent:
                step["position"] = agent["position"]

            sdk_steps.append(step)

        # Build dependencies and input mappings from connections
        # Also add target agents as callable functions for agent-to-agent communication
        for connection in connections:
            source_id = connection.get("source_agent_id")
            target_id = connection.get("target_agent_id")

            if source_id and target_id:
                # Determine if this is an agent-to-agent connection or agent-to-tool connection
                source_node_type = None
                target_node_type = None

                # Find the node types
                for agent in agents:
                    agent_id = agent.get("agent_id") or agent.get("node_id")
                    if agent_id == source_id:
                        source_node_type = agent.get("node_type") or ("tool" if agent.get("agent_type") == "tool" else "agent")
                    if agent_id == target_id:
                        target_node_type = agent.get("node_type") or ("tool" if agent.get("agent_type") == "tool" else "agent")

                # For agent-to-agent connections, add target as a callable function to source
                if source_node_type == "agent" and target_node_type == "agent":
                    # Find source step and add target agent as a callable function
                    for step in sdk_steps:
                        if step["step_id"] == source_id and step["step_type"] == "agent_execution":
                            # Ensure config exists
                            if "config" not in step:
                                step["config"] = {}
                            if "functions" not in step["config"]:
                                step["config"]["functions"] = []

                            # Get target agent info
                            target_agent = agent_map.get(target_id)
                            if target_agent:
                                # Add target agent as a callable function
                                agent_tool = {
                                    "type": "function",
                                    "function": {
                                        "name": target_agent.get("agent_type")
                                        or target_agent.get("name", f"agent_{target_id}"),
                                        "description": target_agent.get(
                                            "description", f"Call the {target_agent.get('name', 'agent')} to help with the task"
                                        ),
                                        "parameters": {
                                            "type": "object",
                                            "properties": {
                                                "query": {
                                                    "type": "string",
                                                    "description": "The query or request to send to the agent",
                                                }
                                            },
                                            "required": ["query"],
                                        },
                                        # Store agent_id for execution
                                        "agent_id": target_id,
                                    },
                                }
                                step["config"]["functions"].append(agent_tool)
                            break
                else:
                    # For tool connections, add dependencies and input mappings
                    for step in sdk_steps:
                        if step["step_id"] == target_id:
                            # Add dependency
                            if source_id not in step["dependencies"]:
                                step["dependencies"].append(source_id)

                            # Set up input_mapping to pass source output to target
                            if step["step_type"] == "tool_execution":
                                # Pass the entire source step output as input_data
                                step["input_mapping"][source_id] = source_id
                            elif step["step_type"] == "agent_execution":
                                # For agent steps, also pass the source output
                                step["input_mapping"][source_id] = source_id
                            break

        # Add other steps from configuration
        other_steps = as_config.get("steps", [])
        sdk_steps.extend(other_steps)

        # Build SDK configuration with steps
        sdk_config = {"steps": sdk_steps}

        # Store callable agents metadata so the UI can retrieve them
        # These are agents that are targets of agent-to-agent connections
        callable_agents = []
        for agent_id in target_agent_ids:
            agent = agent_map.get(agent_id)
            if agent:
                callable_agents.append(agent)

        if callable_agents:
            sdk_config["callable_agents"] = callable_agents

        # Preserve connections array for UI metadata (convert AS format to SDK format)
        if connections:
            sdk_connections = []
            for conn in connections:
                sdk_conn = {
                    "source_step_id": conn.get("source_agent_id"),
                    "target_step_id": conn.get("target_agent_id"),
                    "connection_type": conn.get("connection_type", "default"),
                }
                sdk_connections.append(sdk_conn)
            sdk_config["connections"] = sdk_connections

        sdk_request["configuration"] = sdk_config

        # Add optional fields
        if "tags" in as_request:
            sdk_request["tags"] = as_request["tags"]

        if "created_by" in as_request:
            sdk_request["created_by"] = as_request["created_by"]

        if "is_editable" in as_request:
            sdk_request["editable"] = as_request["is_editable"]
        elif "editable" in as_request:
            sdk_request["editable"] = as_request["editable"]

        # Map status fields
        if "is_active" in as_request:
            sdk_request["status"] = "active" if as_request["is_active"] else "inactive"

        return sdk_request

    @staticmethod
    def adapt_workflow_update_request(as_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Agent Studio workflow update request to SDK format

        Similar to create but handles partial updates
        """
        sdk_request = {}

        # Only include fields that are present in the request
        if "name" in as_request:
            sdk_request["name"] = as_request["name"]

        if "description" in as_request:
            sdk_request["description"] = as_request["description"]

        if "version" in as_request:
            sdk_request["version"] = as_request["version"]

        if "configuration" in as_request:
            # Use the same conversion as create
            full_request = {"configuration": as_request["configuration"]}
            converted = RequestAdapter.adapt_workflow_create_request(full_request)
            sdk_request["configuration"] = converted["configuration"]

        if "tags" in as_request:
            sdk_request["tags"] = as_request["tags"]

        if "is_editable" in as_request:
            sdk_request["editable"] = as_request["is_editable"]

        if "is_active" in as_request:
            sdk_request["status"] = "active" if as_request["is_active"] else "inactive"

        return sdk_request

    @staticmethod
    def adapt_execution_list_params(
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Convert Agent Studio execution list parameters to SDK format

        Agent Studio uses: status="queued|running|completed|failed"
        SDK uses: status="pending|running|completed|failed"
        """
        params = {
            "limit": limit,
            "offset": offset,
        }

        # Map status values
        if status:
            status_map = {
                "queued": "pending",
                "running": "running",
                "completed": "completed",
                "failed": "failed",
                "cancelled": "cancelled",
            }
            params["status"] = status_map.get(status, status)

        if user_id:
            params["user_id"] = user_id

        return params
