"""
Workflow agent builders and helper functions.

This module contains all the agent building logic that was previously
in workflow_endpoints.py, including:
- Agent building from workflow configurations
- Dynamic agent store creation
- OpenAI schema generation
- Root agent detection
"""

import inspect
import uuid
import json
import re
from typing import Dict, Any, List, Optional, Union, get_type_hints
from datetime import datetime
from sqlalchemy.orm import Session

from db import crud, models
from agents.command_agent import CommandAgent
from agents.agent_base import Agent
from fastapi_logger import ElevaiteLogger
from prompts import command_agent_system_prompt


logger = ElevaiteLogger()


def build_toshiba_agent_from_workflow(db: Session, workflow, agent_config):
    """Build ToshibaAgent from workflow configuration"""
    from agents.toshiba_agent import create_toshiba_agent
    from prompts import toshiba_agent_system_prompt
    from agents.tools import tool_schemas

    # Get ToshibaAgent-specific configuration
    functions = [tool_schemas.get("query_retriever2")] if "query_retriever2" in tool_schemas else []

    return create_toshiba_agent(system_prompt=toshiba_agent_system_prompt, functions=functions)


def build_single_agent_from_workflow(db: Session, workflow: models.Workflow, agent_config):
    """Build a single agent from workflow configuration using its configured prompt and tools"""
    from agents.agent_base import Agent

    # Get agent type and ID from config
    agent_type = agent_config.get("agent_type", "CommandAgent")
    agent_id = agent_config.get("agent_id")
    # Try to get the agent from database if agent_id is provided
    db_agent = None
    if agent_id:
        try:
            import uuid

            db_agent = crud.get_agent(db, uuid.UUID(agent_id))
        except (ValueError, TypeError) as e:
            # If agent_id is invalid, try to find by name
            db_agent = crud.get_agent_by_name(db, agent_type)
    else:
        # Find agent by type/name
        db_agent = crud.get_agent_by_name(db, agent_type)

    if not db_agent:
        # Fallback to CommandAgent if agent not found
        return build_command_agent_from_workflow(db, workflow)

    from typing import cast
    from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam
    from data_classes import PromptObject

    try:
        # Check if system_prompt exists and has required attributes
        if not hasattr(db_agent, "system_prompt") or db_agent.system_prompt is None:
            # Use a simple fallback
            system_prompt = db_agent.system_prompt
        else:
            from datetime import datetime
            import uuid

            system_prompt = PromptObject(
                appName="",
                createdTime=getattr(db_agent.system_prompt, "created_time", datetime.now()),
                prompt=getattr(db_agent.system_prompt, "prompt", ""),
                uniqueLabel=getattr(db_agent.system_prompt, "unique_label", ""),
                pid=getattr(db_agent.system_prompt, "pid", uuid.uuid4()),
                last_deployed=getattr(db_agent.system_prompt, "last_deployed", None),
                deployedTime=getattr(db_agent.system_prompt, "deployed_time", None),
                isDeployed=getattr(db_agent.system_prompt, "is_deployed", False),
                modelProvider=getattr(db_agent.system_prompt, "ai_model_provider", ""),
                modelName=getattr(db_agent.system_prompt, "ai_model_name", ""),
                sha_hash=getattr(db_agent.system_prompt, "sha_hash", ""),
                tags=getattr(db_agent.system_prompt, "tags", []),
                version=getattr(db_agent.system_prompt, "version", ""),
                variables=getattr(db_agent.system_prompt, "variables", {}),
                hyper_parameters=getattr(db_agent.system_prompt, "hyper_parameters", {}),
                prompt_label=getattr(db_agent.system_prompt, "prompt_label", ""),
            )
    except Exception as e:
        # Fallback to original system_prompt if PromptObject construction fails
        system_prompt = db_agent.system_prompt

    return Agent(
        name=db_agent.name,
        agent_id=db_agent.agent_id,
        system_prompt=system_prompt,
        persona=db_agent.persona,
        functions=cast(List[ChatCompletionToolParam], db_agent.functions or []),
        routing_options=db_agent.routing_options or {},
        model="gpt-4o-mini",
        temperature=0.7,
        short_term_memory=db_agent.short_term_memory or False,
        long_term_memory=db_agent.long_term_memory or False,
        reasoning=db_agent.reasoning or False,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=db_agent.max_retries or 3,
        timeout=db_agent.timeout,
        deployed=True,
        status="active",
        priority=db_agent.priority,
        failure_strategies=db_agent.failure_strategies or [],
        session_id=None,
        last_active=datetime.now(),
        collaboration_mode="single",
    )


def sanitize_function_name(name: str) -> str:
    """Convert agent name to valid OpenAI function name"""
    # Remove spaces and special characters, convert to camelCase
    import re

    # Replace spaces and special chars with underscores, then remove multiple underscores
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    sanitized = re.sub(r"_+", "_", sanitized)  # Remove multiple underscores
    sanitized = sanitized.strip("_")  # Remove leading/trailing underscores

    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = f"agent_{sanitized}"

    return sanitized or "unknown_agent"


def build_openai_schema_from_db_agent(db_agent: models.Agent):
    """Build OpenAI function schema from database agent"""
    try:
        # Sanitize the agent name for use as function name
        function_name = sanitize_function_name(db_agent.name)

        # Create a simplified schema that only exposes essential parameters
        # for agent-to-agent communication
        schema = {
            "type": "function",
            "function": {
                "name": function_name,
                "description": db_agent.description or f"Execute {db_agent.name} agent",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query or task to send to the agent",
                        },
                        "chat_history": {
                            "type": "array",
                            "description": "Optional chat history for context",
                            "items": {"type": "object"},
                        },
                    },
                    "required": ["query"],
                },
            },
        }

        return schema

    except Exception as e:
        # Return None if schema generation fails completely
        return None


def build_dynamic_agent_store(db: Session, workflow):
    """Build agent store dynamically from database agents in the workflow"""
    agent_store = {}

    try:
        # Get all agents in this workflow
        workflow_agents = crud.get_workflow_agents(db, workflow.workflow_id)

        for workflow_agent in workflow_agents:
            db_agent = crud.get_agent(db, workflow_agent.agent_id)
            if db_agent:
                # Create a callable function for this agent
                def create_agent_executor(agent_id):
                    def execute_agent(
                        query: str,
                        session_id: Optional[str] = None,
                        user_id: Optional[str] = None,
                        chat_history: Optional[list] = None,
                        enable_analytics: bool = False,
                        **kwargs,
                    ):
                        # Build the agent dynamically and execute
                        try:
                            agent = build_single_agent_from_workflow(db, workflow, {"agent_id": str(agent_id)})
                            result = agent.execute(
                                query=query,
                                session_id=session_id,
                                user_id=user_id,
                                chat_history=chat_history,
                                enable_analytics=enable_analytics,
                                **kwargs,
                            )

                            # Ensure result is JSON serializable
                            if isinstance(result, (dict, list)):
                                import json

                                return json.dumps(result)
                            elif hasattr(result, "__iter__") and not isinstance(result, str):
                                # Handle generators and other iterables (e.g., AgentStreamChunk generators)
                                import json

                                chunks = []
                                for item in result:
                                    # Convert Pydantic models to dicts
                                    if hasattr(item, "model_dump"):
                                        chunks.append(item.model_dump())
                                    elif hasattr(item, "message"):
                                        # AgentStreamChunk-like object
                                        chunks.append({"type": getattr(item, "type", "content"), "message": item.message})
                                    else:
                                        chunks.append(str(item))
                                return json.dumps({"chunks": chunks})
                            else:
                                return str(result)
                        except Exception as e:
                            return f"Error executing agent: {str(e)}"

                    return execute_agent

                # Use sanitized function name to match OpenAI schema
                function_name = sanitize_function_name(db_agent.name)
                agent_store[function_name] = create_agent_executor(db_agent.agent_id)

        return agent_store

    except Exception as e:
        # Return empty store if building fails
        return {}


def find_root_agent(db: Session, workflow):
    """Find the true root agent by analyzing workflow connections"""
    workflow_agents = crud.get_workflow_agents(db, workflow.workflow_id)
    workflow_connections = crud.get_workflow_connections(db, workflow.workflow_id)

    # Get all agent IDs that appear as targets (have incoming connections)
    target_agent_ids = {conn.target_agent_id for conn in workflow_connections}

    # Get all agent IDs that appear as sources (have outgoing connections)
    source_agent_ids = {conn.source_agent_id for conn in workflow_connections}

    # Root agent is one that is a source but never a target
    root_agent_ids = source_agent_ids - target_agent_ids

    if len(root_agent_ids) == 1:
        root_agent_id = list(root_agent_ids)[0]
        return crud.get_agent(db, root_agent_id)
    elif len(root_agent_ids) == 0:
        # No clear root - might be a single agent workflow
        if len(workflow_agents) == 1:
            return crud.get_agent(db, workflow_agents[0].agent_id)

    # Multiple roots or unclear structure - fallback to None
    return None


def build_root_agent_with_workflow_functions(db: Session, workflow):
    """Build the root agent with workflow functions instead of creating a temporary CommandAgent"""
    # Find the true root agent
    root_agent = find_root_agent(db, workflow)

    if not root_agent:
        # Fallback to creating a temporary CommandAgent if no root found
        return build_command_agent_from_workflow(db, workflow)

    # Get workflow connections to build functions list
    workflow_connections = crud.get_workflow_connections(db, workflow.workflow_id)

    # Build functions list from target agents that the root agent can call
    workflow_functions = []

    for connection in workflow_connections:
        # Only include connections where the root agent is the source
        if connection.source_agent_id == root_agent.agent_id:
            target_agent = crud.get_agent(db, connection.target_agent_id)
            if target_agent:
                dynamic_schema = build_openai_schema_from_db_agent(target_agent)
                if dynamic_schema:
                    workflow_functions.append(dynamic_schema)

    # Create a CommandAgent using the root agent's properties but with workflow functions
    from agents.command_agent import CommandAgent
    from data_classes import PromptObject

    # Create a PromptObject from the database prompt
    if root_agent.system_prompt:
        system_prompt_obj = PromptObject(
            pid=root_agent.system_prompt.pid,
            prompt_label=root_agent.system_prompt.prompt_label,
            prompt=root_agent.system_prompt.prompt,
            sha_hash=root_agent.system_prompt.sha_hash or "default_hash",
            uniqueLabel=root_agent.system_prompt.unique_label,
            appName=root_agent.system_prompt.app_name,
            version=root_agent.system_prompt.version,
            createdTime=root_agent.system_prompt.created_time,
            deployedTime=root_agent.system_prompt.deployed_time,
            last_deployed=root_agent.system_prompt.last_deployed,
            modelProvider=root_agent.system_prompt.ai_model_provider,
            modelName=root_agent.system_prompt.ai_model_name,
            isDeployed=root_agent.system_prompt.is_deployed,
            tags=root_agent.system_prompt.tags,
            hyper_parameters=root_agent.system_prompt.hyper_parameters,
            variables=root_agent.system_prompt.variables,
        )
    else:
        # Fallback to default prompt
        system_prompt_obj = PromptObject(
            pid=uuid.uuid4(),
            prompt_label="Default Workflow Agent",
            prompt="You are a workflow orchestrator agent.",
            sha_hash="default_hash",
            uniqueLabel="DefaultWorkflowAgent",
            appName="agent_studio",
            version="1.0",
            createdTime=datetime.now(),
            deployedTime=None,
            last_deployed=None,
            modelProvider="OpenAI",
            modelName="gpt-4o",
            isDeployed=False,
            tags=[],
            hyper_parameters={},
            variables={},
        )

    command_agent = CommandAgent(
        name=root_agent.name,
        agent_id=root_agent.agent_id,  # Use the real agent_id from database
        system_prompt=system_prompt_obj,  # Use proper PromptObject
        persona=root_agent.persona,
        functions=workflow_functions,  # Use workflow-specific functions
        routing_options={
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        model="gpt-4o",
        temperature=0.7,
        short_term_memory=root_agent.short_term_memory,
        long_term_memory=root_agent.long_term_memory,
        reasoning=root_agent.reasoning,
        input_type=["text", "voice"],  # Use default values to avoid type issues
        output_type=["text", "voice"],
        response_type="json",
        max_retries=5,
        timeout=None,
        deployed=True,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        session_id=None,
        last_active=datetime.now(),
        collaboration_mode="single",
    )

    return command_agent


def build_command_agent_from_workflow(db: Session, workflow) -> CommandAgent:
    """Build a CommandAgent from a workflow configuration"""
    # Get workflow agents and connections
    workflow_agents = crud.get_workflow_agents(db, workflow.workflow_id)
    workflow_connections = crud.get_workflow_connections(db, workflow.workflow_id)

    # Build functions list for CommandAgent
    functions = []
    for connection in workflow_connections:
        target_agent = crud.get_agent(db, connection.target_agent_id)

        # Build OpenAI schema dynamically from database agent
        if target_agent:
            dynamic_schema = build_openai_schema_from_db_agent(target_agent)
            if dynamic_schema:
                functions.append(dynamic_schema)

    # Create CommandAgent
    command_agent = CommandAgent(
        name=f"WorkflowCommandAgent_{workflow.name}",
        agent_id=uuid.uuid4(),
        system_prompt=command_agent_system_prompt,
        persona="Command Agent",
        functions=functions,
        routing_options={
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        model="gpt-4o",
        temperature=0.7,
        short_term_memory=True,
        long_term_memory=False,
        reasoning=False,
        input_type=["text", "voice"],
        output_type=["text", "voice"],
        response_type="json",
        max_retries=5,
        timeout=None,
        deployed=True,
        status="active",
        priority=None,
        failure_strategies=["retry", "escalate"],
        session_id=None,
        last_active=datetime.now(),
        collaboration_mode="single",
    )

    return command_agent
