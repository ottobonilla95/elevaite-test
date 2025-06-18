import uuid
import hashlib
from datetime import datetime
from typing import List, Optional
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

from sqlalchemy.orm import Session
from sqlalchemy import func

from agents.tools import tool_schemas
from . import models, schemas


def create_prompt(db: Session, prompt: schemas.PromptCreate) -> models.Prompt:
    # Generate a hash if one isn't provided
    sha_hash = prompt.sha_hash
    if sha_hash is None:
        # Create a hash based on the prompt content, label, and timestamp
        content_to_hash = f"{prompt.prompt}{prompt.prompt_label}{datetime.now().isoformat()}"
        sha_hash = hashlib.sha256(content_to_hash.encode()).hexdigest()[:40]

    db_prompt = models.Prompt(
        prompt_label=prompt.prompt_label,
        prompt=prompt.prompt,
        sha_hash=sha_hash,
        unique_label=prompt.unique_label,
        app_name=prompt.app_name,
        version=prompt.version,
        ai_model_provider=prompt.ai_model_provider,
        ai_model_name=prompt.ai_model_name,
        tags=prompt.tags,
        hyper_parameters=prompt.hyper_parameters,
        variables=prompt.variables,
        created_time=datetime.now(),
        is_deployed=False,
    )
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt


def get_prompt(db: Session, prompt_id: uuid.UUID) -> Optional[models.Prompt]:
    return db.query(models.Prompt).filter(models.Prompt.pid == prompt_id).first()


def get_prompt_by_app_and_label(db: Session, app_name: str, prompt_label: str) -> List[models.Prompt]:
    return (
        db.query(models.Prompt)
        .filter(
            models.Prompt.app_name == app_name,
            models.Prompt.prompt_label == prompt_label,
        )
        .all()
    )


def get_deployed_prompt(db: Session, app_name: str, prompt_label: str) -> Optional[models.Prompt]:
    return (
        db.query(models.Prompt)
        .filter(
            models.Prompt.app_name == app_name,
            models.Prompt.prompt_label == prompt_label,
            models.Prompt.is_deployed,
        )
        .first()
    )


def get_prompts(db: Session, skip: int = 0, limit: int = 100, app_name: Optional[str] = None) -> List[models.Prompt]:
    query = db.query(models.Prompt)
    if app_name:
        query = query.filter(models.Prompt.app_name == app_name)
    return query.offset(skip).limit(limit).all()


def update_prompt(db: Session, prompt_id: uuid.UUID, prompt_update: schemas.PromptUpdate) -> Optional[models.Prompt]:
    db_prompt = get_prompt(db, prompt_id)
    if not db_prompt:
        return None

    update_data = prompt_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prompt, key, value)

    db.commit()
    db.refresh(db_prompt)
    return db_prompt


def deploy_prompt(db: Session, prompt_id: uuid.UUID, app_name: str, environment: str = "production") -> Optional[models.Prompt]:
    db_prompt = get_prompt(db, prompt_id)
    if db_prompt is None or str(db_prompt.app_name) != app_name:
        return None

    prompt_label = str(db_prompt.prompt_label)
    currently_deployed = get_deployed_prompt(db, app_name, prompt_label)
    if currently_deployed is not None and str(currently_deployed.pid) != str(prompt_id):
        setattr(currently_deployed, "is_deployed", False)
        setattr(currently_deployed, "last_deployed", currently_deployed.deployed_time)

    setattr(db_prompt, "is_deployed", True)
    setattr(db_prompt, "deployed_time", datetime.now())
    setattr(db_prompt, "last_deployed", datetime.now())

    deployment = models.PromptDeployment(
        prompt_id=prompt_id,
        environment=environment,
        version_number=db_prompt.version,
        deployed_at=datetime.now(),
        is_active=True,
    )
    db.add(deployment)

    db.commit()
    db.refresh(db_prompt)
    return db_prompt


def delete_prompt(db: Session, prompt_id: uuid.UUID) -> bool:
    db_prompt = get_prompt(db, prompt_id)
    if not db_prompt:
        return False

    db.delete(db_prompt)
    db.commit()
    return True


# Agent CRUD operations
def validate_agent_functions(functions: List[schemas.AgentFunction]) -> List[ChatCompletionToolParam]:
    validated_functions = []
    for _func in functions:
        __func = schemas.AgentFunction.model_validate(_func)
        func_name = __func.function.name
        if func_name and func_name in tool_schemas:
            validated_functions.append(tool_schemas[func_name])
        else:
            raise ValueError(f"Function {func_name} not found in tool_schemas")

    return validated_functions


def create_agent(db: Session, agent: schemas.AgentCreate) -> models.Agent:
    # Validate and normalize functions before storing
    validated_functions = validate_agent_functions(agent.functions)

    db_agent = models.Agent(
        name=agent.name,
        parent_agent_id=agent.parent_agent_id,
        system_prompt_id=agent.system_prompt_id,
        persona=agent.persona,
        functions=validated_functions,
        routing_options=agent.routing_options,
        short_term_memory=agent.short_term_memory,
        long_term_memory=agent.long_term_memory,
        reasoning=agent.reasoning,
        input_type=agent.input_type,
        output_type=agent.output_type,
        response_type=agent.response_type,
        max_retries=agent.max_retries,
        timeout=agent.timeout,
        deployed=agent.deployed,
        status=agent.status,
        priority=agent.priority,
        failure_strategies=agent.failure_strategies,
        collaboration_mode=agent.collaboration_mode,
        available_for_deployment=agent.available_for_deployment,
        deployment_code=agent.deployment_code,
        last_active=datetime.now(),
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


def get_agent(db: Session, agent_id: uuid.UUID) -> Optional[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.agent_id == agent_id).first()


def get_agent_with_functions(db: Session, agent_id: uuid.UUID) -> Optional[models.Agent]:
    agent = db.query(models.Agent).filter(models.Agent.agent_id == agent_id).first()
    if not agent:
        return None

    reconstructed_functions = []
    for func_schema in agent.functions:
        if isinstance(func_schema, dict) and "function" in func_schema:
            func_name = func_schema["function"].get("name")
            if func_name and func_name in tool_schemas:
                reconstructed_functions.append(tool_schemas[func_name])
            else:
                reconstructed_functions.append(func_schema)
        else:
            reconstructed_functions.append(func_schema)

    agent.functions = reconstructed_functions
    return agent


def get_agent_by_name(db: Session, name: str) -> Optional[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.name == name).first()


def get_agent_by_name_with_functions(db: Session, name: str) -> Optional[models.Agent]:
    agent = db.query(models.Agent).filter(models.Agent.name == name).first()
    if not agent:
        return None

    reconstructed_functions = []
    for func_schema in agent.functions:
        if isinstance(func_schema, dict) and "function" in func_schema:
            func_name = func_schema["function"].get("name")
            if func_name and func_name in tool_schemas:
                reconstructed_functions.append(tool_schemas[func_name])
            else:
                reconstructed_functions.append(func_schema)
        else:
            reconstructed_functions.append(func_schema)

    agent.functions = reconstructed_functions
    return agent


def get_agents(db: Session, skip: int = 0, limit: int = 100, deployed: Optional[bool] = None) -> List[models.Agent]:
    query = db.query(models.Agent)
    if deployed is not None:
        query = query.filter(models.Agent.deployed == deployed)
    return query.offset(skip).limit(limit).all()


def get_available_agents(db: Session) -> List[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.available_for_deployment).all()


def get_agent_by_deployment_code(db: Session, code: str) -> Optional[models.Agent]:
    return db.query(models.Agent).filter(models.Agent.deployment_code == code).first()


def update_agent(db: Session, agent_id: uuid.UUID, agent_update: schemas.AgentUpdate) -> Optional[models.Agent]:
    db_agent = get_agent(db, agent_id)
    if not db_agent:
        return None

    update_data = agent_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_agent, key, value)

    if "functions" in update_data:
        setattr(db_agent, "functions", validate_agent_functions(update_data["functions"]))

    db.commit()
    db.refresh(db_agent)
    return db_agent


def delete_agent(db: Session, agent_id: uuid.UUID) -> bool:
    db_agent = get_agent(db, agent_id)
    if not db_agent:
        return False

    db.delete(db_agent)
    db.commit()
    return True


# Workflow CRUD operations
def create_workflow(db: Session, workflow: schemas.WorkflowCreate) -> models.Workflow:
    db_workflow = models.Workflow(
        name=workflow.name,
        description=workflow.description,
        version=workflow.version,
        configuration=workflow.configuration,
        created_by=workflow.created_by,
        is_active=workflow.is_active,
        tags=workflow.tags,
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow


def get_workflow(db: Session, workflow_id: uuid.UUID) -> Optional[models.Workflow]:
    return db.query(models.Workflow).filter(models.Workflow.workflow_id == workflow_id).first()


def get_workflow_by_name(db: Session, name: str, version: Optional[str] = None) -> Optional[models.Workflow]:
    query = db.query(models.Workflow).filter(models.Workflow.name == name)
    if version:
        query = query.filter(models.Workflow.version == version)
    return query.first()


def get_workflows(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    is_deployed: Optional[bool] = None,
) -> List[models.Workflow]:
    query = db.query(models.Workflow)
    if is_active is not None:
        query = query.filter(models.Workflow.is_active == is_active)
    if is_deployed is not None:
        query = query.filter(models.Workflow.is_deployed == is_deployed)
    return query.offset(skip).limit(limit).all()


def update_workflow(db: Session, workflow_id: uuid.UUID, workflow_update: schemas.WorkflowUpdate) -> Optional[models.Workflow]:
    db_workflow = get_workflow(db, workflow_id)
    if not db_workflow:
        return None

    update_data = workflow_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_workflow, key, value)

    db.commit()
    db.refresh(db_workflow)
    return db_workflow


def delete_workflow(db: Session, workflow_id: uuid.UUID) -> bool:
    db_workflow = get_workflow(db, workflow_id)
    if not db_workflow:
        return False

    deployment = get_workflow_deployment_by_workflow_id(db, workflow_id)
    if deployment is not None:
        delete_workflow_deployment(db, deployment.deployment_id)

    db.delete(db_workflow)
    db.commit()
    return True


# WorkflowAgent CRUD operations
def create_workflow_agent(db: Session, workflow_agent: schemas.WorkflowAgentCreate) -> models.WorkflowAgent:
    db_workflow_agent = models.WorkflowAgent(
        workflow_id=workflow_agent.workflow_id,
        agent_id=workflow_agent.agent_id,
        position_x=workflow_agent.position_x,
        position_y=workflow_agent.position_y,
        node_id=workflow_agent.node_id,
        agent_config=workflow_agent.agent_config,
    )
    db.add(db_workflow_agent)
    db.commit()
    db.refresh(db_workflow_agent)
    return db_workflow_agent


def get_workflow_agents(db: Session, workflow_id: uuid.UUID) -> List[models.WorkflowAgent]:
    return db.query(models.WorkflowAgent).filter(models.WorkflowAgent.workflow_id == workflow_id).all()


def delete_workflow_agent(db: Session, workflow_id: uuid.UUID, agent_id: uuid.UUID) -> bool:
    db_workflow_agent = (
        db.query(models.WorkflowAgent)
        .filter(
            models.WorkflowAgent.workflow_id == workflow_id,
            models.WorkflowAgent.agent_id == agent_id,
        )
        .first()
    )

    if not db_workflow_agent:
        return False

    db.delete(db_workflow_agent)
    db.commit()
    return True


# WorkflowConnection CRUD operations
def create_workflow_connection(db: Session, connection: schemas.WorkflowConnectionCreate) -> models.WorkflowConnection:
    db_connection = models.WorkflowConnection(
        workflow_id=connection.workflow_id,
        source_agent_id=connection.source_agent_id,
        target_agent_id=connection.target_agent_id,
        connection_type=connection.connection_type,
        conditions=connection.conditions,
        priority=connection.priority,
        source_handle=connection.source_handle,
        target_handle=connection.target_handle,
    )
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    return db_connection


def get_workflow_connections(db: Session, workflow_id: uuid.UUID) -> List[models.WorkflowConnection]:
    return db.query(models.WorkflowConnection).filter(models.WorkflowConnection.workflow_id == workflow_id).all()


def delete_workflow_connection(
    db: Session,
    workflow_id: uuid.UUID,
    source_agent_id: uuid.UUID,
    target_agent_id: uuid.UUID,
) -> bool:
    db_connection = (
        db.query(models.WorkflowConnection)
        .filter(
            models.WorkflowConnection.workflow_id == workflow_id,
            models.WorkflowConnection.source_agent_id == source_agent_id,
            models.WorkflowConnection.target_agent_id == target_agent_id,
        )
        .first()
    )

    if not db_connection:
        return False

    db.delete(db_connection)
    db.commit()
    return True


# WorkflowDeployment CRUD operations
def create_workflow_deployment(db: Session, deployment: schemas.WorkflowDeploymentCreate) -> models.WorkflowDeployment:
    db_deployment = models.WorkflowDeployment(
        workflow_id=deployment.workflow_id,
        environment=deployment.environment,
        deployment_name=deployment.deployment_name,
        deployed_by=deployment.deployed_by,
        runtime_config=deployment.runtime_config,
    )
    db.add(db_deployment)
    db.commit()
    db.refresh(db_deployment)

    # Update workflow deployment status
    db_workflow = get_workflow(db, deployment.workflow_id)
    if db_workflow:
        db_workflow.is_deployed = True
        db_workflow.deployed_at = datetime.now()
        db.commit()

    return db_deployment


def get_workflow_deployment(db: Session, deployment_id: uuid.UUID) -> Optional[models.WorkflowDeployment]:
    return db.query(models.WorkflowDeployment).filter(models.WorkflowDeployment.deployment_id == deployment_id).first()


def get_workflow_deployment_by_workflow_id(db: Session, workflow_id: uuid.UUID) -> Optional[models.WorkflowDeployment]:
    return db.query(models.WorkflowDeployment).filter(models.WorkflowDeployment.workflow_id == workflow_id).first()


def get_workflow_deployment_by_name(
    db: Session, deployment_name: str, environment: str = "production"
) -> Optional[models.WorkflowDeployment]:
    return (
        db.query(models.WorkflowDeployment)
        .filter(
            models.WorkflowDeployment.deployment_name == deployment_name,
            models.WorkflowDeployment.environment == environment,
        )
        .first()
    )


def get_active_workflow_deployments(db: Session) -> List[models.WorkflowDeployment]:
    return db.query(models.WorkflowDeployment).filter(models.WorkflowDeployment.status == "active").all()


def update_workflow_deployment(
    db: Session,
    deployment_id: uuid.UUID,
    deployment_update: schemas.WorkflowDeploymentUpdate,
) -> Optional[models.WorkflowDeployment]:
    db_deployment = get_workflow_deployment(db, deployment_id)
    if not db_deployment:
        return None

    update_data = deployment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_deployment, key, value)

    if deployment_update.status == "inactive":
        db_deployment.stopped_at = datetime.now()

    db.commit()
    db.refresh(db_deployment)
    return db_deployment


def delete_workflow_deployment(db: Session, deployment_id: uuid.UUID) -> bool:
    db_deployment = get_workflow_deployment(db, deployment_id)
    if not db_deployment:
        return False

    db.delete(db_deployment)
    db.commit()
    return True


# Tool Category CRUD operations
def create_tool_category(db: Session, category: schemas.ToolCategoryCreate) -> models.ToolCategory:
    db_category = models.ToolCategory(
        name=category.name,
        description=category.description,
        icon=category.icon,
        color=category.color,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def get_tool_category(db: Session, category_id: uuid.UUID) -> Optional[models.ToolCategory]:
    return db.query(models.ToolCategory).filter(models.ToolCategory.category_id == category_id).first()


def get_tool_category_by_name(db: Session, name: str) -> Optional[models.ToolCategory]:
    return db.query(models.ToolCategory).filter(models.ToolCategory.name == name).first()


def get_tool_categories(db: Session, skip: int = 0, limit: int = 100) -> List[models.ToolCategory]:
    return db.query(models.ToolCategory).offset(skip).limit(limit).all()


def update_tool_category(
    db: Session, category_id: uuid.UUID, category_update: schemas.ToolCategoryUpdate
) -> Optional[models.ToolCategory]:
    db_category = get_tool_category(db, category_id)
    if not db_category:
        return None

    update_data = category_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_category, key, value)

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


# MCP Server CRUD operations
def create_mcp_server(db: Session, server: schemas.MCPServerCreate) -> models.MCPServer:
    db_server = models.MCPServer(
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


def get_mcp_server(db: Session, server_id: uuid.UUID) -> Optional[models.MCPServer]:
    return db.query(models.MCPServer).filter(models.MCPServer.server_id == server_id).first()


def get_mcp_server_by_name(db: Session, name: str) -> Optional[models.MCPServer]:
    return db.query(models.MCPServer).filter(models.MCPServer.name == name).first()


def get_mcp_servers(db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None) -> List[models.MCPServer]:
    query = db.query(models.MCPServer)
    if status:
        query = query.filter(models.MCPServer.status == status)
    return query.offset(skip).limit(limit).all()


def get_active_mcp_servers(db: Session) -> List[models.MCPServer]:
    return db.query(models.MCPServer).filter(models.MCPServer.status == "active").all()


def update_mcp_server(db: Session, server_id: uuid.UUID, server_update: schemas.MCPServerUpdate) -> Optional[models.MCPServer]:
    db_server = get_mcp_server(db, server_id)
    if not db_server:
        return None

    update_data = server_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_server, key, value)

    db.commit()
    db.refresh(db_server)
    return db_server


def update_mcp_server_health(db: Session, server_id: uuid.UUID, is_healthy: bool) -> Optional[models.MCPServer]:
    db_server = get_mcp_server(db, server_id)
    if not db_server:
        return None

    db_server.last_health_check = datetime.now()
    db_server.last_seen = datetime.now()

    if is_healthy:
        db_server.consecutive_failures = 0
        if db_server.status == "error":
            db_server.status = "active"
    else:
        db_server.consecutive_failures += 1
        if db_server.consecutive_failures >= 3:
            db_server.status = "error"

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


# Tool CRUD operations
def create_tool(db: Session, tool: schemas.ToolCreate) -> models.Tool:
    db_tool = models.Tool(
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
        category_id=tool.category_id,
        tags=tool.tags,
        requires_auth=tool.requires_auth,
        timeout_seconds=tool.timeout_seconds,
        retry_count=tool.retry_count,
        rate_limit_per_minute=tool.rate_limit_per_minute,
        created_by=tool.created_by,
    )
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return db_tool


def get_tool(db: Session, tool_id: uuid.UUID) -> Optional[models.Tool]:
    return db.query(models.Tool).filter(models.Tool.tool_id == tool_id).first()


def get_tool_by_name(db: Session, name: str, version: Optional[str] = None) -> Optional[models.Tool]:
    query = db.query(models.Tool).filter(models.Tool.name == name)
    if version:
        query = query.filter(models.Tool.version == version)
    return query.first()


def get_tools(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    tool_type: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    is_available: Optional[bool] = None,
) -> List[models.Tool]:
    query = db.query(models.Tool)
    if tool_type:
        query = query.filter(models.Tool.tool_type == tool_type)
    if category_id:
        query = query.filter(models.Tool.category_id == category_id)
    if is_active is not None:
        query = query.filter(models.Tool.is_active == is_active)
    if is_available is not None:
        query = query.filter(models.Tool.is_available == is_available)
    return query.offset(skip).limit(limit).all()


def get_tools_by_mcp_server(db: Session, server_id: uuid.UUID) -> List[models.Tool]:
    return db.query(models.Tool).filter(models.Tool.mcp_server_id == server_id).all()


def get_available_tools(db: Session) -> List[models.Tool]:
    return db.query(models.Tool).filter(models.Tool.is_active == True, models.Tool.is_available == True).all()


def update_tool(db: Session, tool_id: uuid.UUID, tool_update: schemas.ToolUpdate) -> Optional[models.Tool]:
    db_tool = get_tool(db, tool_id)
    if not db_tool:
        return None

    update_data = tool_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tool, key, value)

    db.commit()
    db.refresh(db_tool)
    return db_tool


def update_tool_usage_stats(db: Session, tool_id: uuid.UUID, execution_time_ms: int, success: bool) -> Optional[models.Tool]:
    db_tool = get_tool(db, tool_id)
    if not db_tool:
        return None

    db_tool.usage_count += 1
    db_tool.last_used = datetime.now()

    if success:
        db_tool.success_count += 1
    else:
        db_tool.error_count += 1

    # Update average execution time (simple moving average)
    if db_tool.average_execution_time_ms is None:
        db_tool.average_execution_time_ms = float(execution_time_ms)
    else:
        # Weighted average with more weight on recent executions
        db_tool.average_execution_time_ms = db_tool.average_execution_time_ms * 0.8 + execution_time_ms * 0.2

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


def create_agent_execution_metrics(db: Session, metrics: schemas.AgentExecutionMetricsCreate) -> models.AgentExecutionMetrics:
    db_metrics = models.AgentExecutionMetrics(
        execution_id=metrics.execution_id or uuid.uuid4(),
        agent_id=metrics.agent_id,
        agent_name=metrics.agent_name,
        start_time=metrics.start_time or datetime.now(),
        status="in_progress",
        query=metrics.query,
        session_id=metrics.session_id,
        user_id=metrics.user_id,
        correlation_id=metrics.correlation_id,
    )
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics


def update_agent_execution_metrics(
    db: Session,
    execution_id: uuid.UUID,
    metrics_update: schemas.AgentExecutionMetricsUpdate,
) -> Optional[models.AgentExecutionMetrics]:
    db_metrics = (
        db.query(models.AgentExecutionMetrics).filter(models.AgentExecutionMetrics.execution_id == execution_id).first()
    )
    if not db_metrics:
        return None

    update_data = metrics_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metrics, key, value)

    db.commit()
    db.refresh(db_metrics)
    return db_metrics


def get_agent_execution_metrics(db: Session, execution_id: uuid.UUID) -> Optional[models.AgentExecutionMetrics]:
    return db.query(models.AgentExecutionMetrics).filter(models.AgentExecutionMetrics.execution_id == execution_id).first()


def create_tool_usage_metrics(db: Session, metrics: schemas.ToolUsageMetricsCreate) -> models.ToolUsageMetrics:
    db_metrics = models.ToolUsageMetrics(
        usage_id=metrics.usage_id or uuid.uuid4(),
        tool_name=metrics.tool_name,
        execution_id=metrics.execution_id,
        start_time=metrics.start_time or datetime.now(),
        status="in_progress",
        input_data=metrics.input_data,
        external_api_called=metrics.external_api_called,
    )
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics


def update_tool_usage_metrics(
    db: Session, usage_id: uuid.UUID, metrics_update: schemas.ToolUsageMetricsUpdate
) -> Optional[models.ToolUsageMetrics]:
    db_metrics = db.query(models.ToolUsageMetrics).filter(models.ToolUsageMetrics.usage_id == usage_id).first()
    if not db_metrics:
        return None

    update_data = metrics_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metrics, key, value)

    db.commit()
    db.refresh(db_metrics)
    return db_metrics


def create_workflow_metrics(db: Session, metrics: schemas.WorkflowMetricsCreate) -> models.WorkflowMetrics:
    db_metrics = models.WorkflowMetrics(
        workflow_id=metrics.workflow_id or uuid.uuid4(),
        workflow_type=metrics.workflow_type,
        start_time=metrics.start_time or datetime.now(),
        status="in_progress",
        agents_involved=metrics.agents_involved,
        agent_count=len(metrics.agents_involved) if metrics.agents_involved else 1,
        session_id=metrics.session_id,
        user_id=metrics.user_id,
    )
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics


def update_workflow_metrics(
    db: Session, workflow_id: uuid.UUID, metrics_update: schemas.WorkflowMetricsUpdate
) -> Optional[models.WorkflowMetrics]:
    db_metrics = db.query(models.WorkflowMetrics).filter(models.WorkflowMetrics.workflow_id == workflow_id).first()
    if not db_metrics:
        return None

    update_data = metrics_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metrics, key, value)

    db.commit()
    db.refresh(db_metrics)
    return db_metrics


def create_session_metrics(db: Session, metrics: schemas.SessionMetricsCreate) -> models.SessionMetrics:
    db_metrics = models.SessionMetrics(
        session_id=metrics.session_id,
        start_time=metrics.start_time or datetime.now(),
        user_id=metrics.user_id,
        user_agent=metrics.user_agent,
        ip_address=metrics.ip_address,
    )
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics


def update_session_metrics(
    db: Session, session_id: str, metrics_update: schemas.SessionMetricsUpdate
) -> Optional[models.SessionMetrics]:
    db_metrics = db.query(models.SessionMetrics).filter(models.SessionMetrics.session_id == session_id).first()
    if not db_metrics:
        return None

    update_data = metrics_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metrics, key, value)

    db.commit()
    db.refresh(db_metrics)
    return db_metrics


def get_session_metrics(db: Session, session_id: str) -> Optional[models.SessionMetrics]:
    return db.query(models.SessionMetrics).filter(models.SessionMetrics.session_id == session_id).first()


def get_agent_usage_stats(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[schemas.AgentUsageStats]:
    query = db.query(models.AgentExecutionMetrics)

    if start_date:
        query = query.filter(models.AgentExecutionMetrics.start_time >= start_date)
    if end_date:
        query = query.filter(models.AgentExecutionMetrics.start_time <= end_date)

    # Get basic stats first
    basic_stats = (
        query.with_entities(
            models.AgentExecutionMetrics.agent_name,
            func.count(models.AgentExecutionMetrics.id).label("total_executions"),
            func.avg(models.AgentExecutionMetrics.duration_ms).label("avg_duration"),
            func.sum(models.AgentExecutionMetrics.tool_count).label("total_tools"),
            func.max(models.AgentExecutionMetrics.start_time).label("last_used"),
        )
        .group_by(models.AgentExecutionMetrics.agent_name)
        .all()
    )

    result = []
    for stat in basic_stats:
        # Get success/failure counts separately
        success_count = query.filter(
            models.AgentExecutionMetrics.agent_name == stat.agent_name,
            models.AgentExecutionMetrics.status == "success",
        ).count()

        failure_count = query.filter(
            models.AgentExecutionMetrics.agent_name == stat.agent_name,
            models.AgentExecutionMetrics.status == "failure",
        ).count()

        success_rate = success_count / stat.total_executions * 100 if stat.total_executions > 0 else 0

        result.append(
            schemas.AgentUsageStats(
                agent_name=stat.agent_name,
                total_executions=stat.total_executions,
                successful_executions=success_count,
                failed_executions=failure_count,
                average_duration_ms=stat.avg_duration,
                total_tool_calls=stat.total_tools or 0,
                success_rate=success_rate,
                last_used=stat.last_used,
            )
        )

    return result


def get_tool_usage_stats(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[schemas.ToolUsageStats]:
    query = db.query(models.ToolUsageMetrics)

    if start_date:
        query = query.filter(models.ToolUsageMetrics.start_time >= start_date)
    if end_date:
        query = query.filter(models.ToolUsageMetrics.start_time <= end_date)

    # Get basic stats first
    basic_stats = (
        query.with_entities(
            models.ToolUsageMetrics.tool_name,
            func.count(models.ToolUsageMetrics.id).label("total_calls"),
            func.avg(models.ToolUsageMetrics.duration_ms).label("avg_duration"),
        )
        .group_by(models.ToolUsageMetrics.tool_name)
        .all()
    )

    result = []
    for stat in basic_stats:
        # Get success/failure counts separately
        success_count = query.filter(
            models.ToolUsageMetrics.tool_name == stat.tool_name,
            models.ToolUsageMetrics.status == "success",
        ).count()

        failure_count = query.filter(
            models.ToolUsageMetrics.tool_name == stat.tool_name,
            models.ToolUsageMetrics.status == "failure",
        ).count()

        success_rate = success_count / stat.total_calls * 100 if stat.total_calls > 0 else 0

        # Get most used by agent (simplified)
        most_used_agent = "Unknown"  # Simplified for now

        result.append(
            schemas.ToolUsageStats(
                tool_name=stat.tool_name,
                total_calls=stat.total_calls,
                successful_calls=success_count,
                failed_calls=failure_count,
                average_duration_ms=stat.avg_duration,
                success_rate=success_rate,
                most_used_by_agent=most_used_agent,
            )
        )

    return result


def get_workflow_performance_stats(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[schemas.WorkflowPerformanceStats]:
    query = db.query(models.WorkflowMetrics)

    if start_date:
        query = query.filter(models.WorkflowMetrics.start_time >= start_date)
    if end_date:
        query = query.filter(models.WorkflowMetrics.start_time <= end_date)

    # Get basic stats first
    basic_stats = (
        query.with_entities(
            models.WorkflowMetrics.workflow_type,
            func.count(models.WorkflowMetrics.id).label("total_workflows"),
            func.avg(models.WorkflowMetrics.duration_ms).label("avg_duration"),
            func.avg(models.WorkflowMetrics.agent_count).label("avg_agent_count"),
        )
        .group_by(models.WorkflowMetrics.workflow_type)
        .all()
    )

    result = []
    for stat in basic_stats:
        # Get success/failure counts separately
        success_count = query.filter(
            models.WorkflowMetrics.workflow_type == stat.workflow_type,
            models.WorkflowMetrics.status == "success",
        ).count()

        failure_count = query.filter(
            models.WorkflowMetrics.workflow_type == stat.workflow_type,
            models.WorkflowMetrics.status == "failure",
        ).count()

        success_rate = success_count / stat.total_workflows * 100 if stat.total_workflows > 0 else 0

        result.append(
            schemas.WorkflowPerformanceStats(
                workflow_type=stat.workflow_type,
                total_workflows=stat.total_workflows,
                successful_workflows=success_count,
                failed_workflows=failure_count,
                average_duration_ms=stat.avg_duration,
                average_agent_count=stat.avg_agent_count or 1,
                success_rate=success_rate,
            )
        )

    return result


def get_error_summary(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[schemas.ErrorSummary]:
    exec_query = db.query(models.AgentExecutionMetrics).filter(models.AgentExecutionMetrics.status == "failure")

    if start_date:
        exec_query = exec_query.filter(models.AgentExecutionMetrics.start_time >= start_date)
    if end_date:
        exec_query = exec_query.filter(models.AgentExecutionMetrics.start_time <= end_date)

    total_errors = exec_query.count()

    # Group by error type (simplified - using first word of error message)
    error_stats = (
        exec_query.with_entities(
            func.split_part(models.AgentExecutionMetrics.error_message, " ", 1).label("error_type"),
            func.count().label("count"),
            models.AgentExecutionMetrics.agent_name,
        )
        .group_by(
            func.split_part(models.AgentExecutionMetrics.error_message, " ", 1),
            models.AgentExecutionMetrics.agent_name,
        )
        .all()
    )

    # Process and aggregate results
    error_dict = {}
    for stat in error_stats:
        error_type = stat.error_type or "Unknown"
        if error_type not in error_dict:
            error_dict[error_type] = {"count": 0, "agents": {}}
        error_dict[error_type]["count"] += stat.count
        error_dict[error_type]["agents"][stat.agent_name] = stat.count

    result = []
    for error_type, data in error_dict.items():
        percentage = (data["count"] / total_errors * 100) if total_errors > 0 else 0
        most_affected_agent = max(data["agents"], key=data["agents"].get) if data["agents"] else None

        result.append(
            schemas.ErrorSummary(
                error_type=error_type,
                count=data["count"],
                percentage=percentage,
                most_affected_agent=most_affected_agent,
                most_affected_tool=None,  # Could be enhanced to track tool errors
            )
        )

    return sorted(result, key=lambda x: x.count, reverse=True)


def get_session_activity_stats(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> schemas.SessionActivityStats:
    session_query = db.query(models.SessionMetrics)
    exec_query = db.query(models.AgentExecutionMetrics)

    if start_date:
        session_query = session_query.filter(models.SessionMetrics.start_time >= start_date)
        exec_query = exec_query.filter(models.AgentExecutionMetrics.start_time >= start_date)
    if end_date:
        session_query = session_query.filter(models.SessionMetrics.start_time <= end_date)
        exec_query = exec_query.filter(models.AgentExecutionMetrics.start_time <= end_date)

    total_sessions = session_query.count()
    active_sessions = session_query.filter(models.SessionMetrics.is_active).count()

    avg_duration = session_query.with_entities(func.avg(models.SessionMetrics.duration_ms)).scalar()

    avg_queries = session_query.with_entities(func.avg(models.SessionMetrics.total_queries)).scalar()

    # Query stats
    total_queries = exec_query.count()
    successful_queries = exec_query.filter(models.AgentExecutionMetrics.status == "success").count()
    failed_queries = exec_query.filter(models.AgentExecutionMetrics.status == "failure").count()

    query_success_rate = successful_queries / total_queries * 100 if total_queries > 0 else 0

    return schemas.SessionActivityStats(
        total_sessions=total_sessions,
        active_sessions=active_sessions,
        average_session_duration_ms=avg_duration,
        average_queries_per_session=avg_queries or 0,
        total_queries=total_queries,
        successful_queries=successful_queries,
        failed_queries=failed_queries,
        query_success_rate=query_success_rate,
    )
