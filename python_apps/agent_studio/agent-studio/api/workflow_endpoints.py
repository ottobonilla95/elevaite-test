"""
Workflow endpoints for Agent Studio.

✅ FULLY MIGRATED TO SDK with adapter layer for backwards compatibility.
All endpoints use workflow-core-sdk with WorkflowAdapter for format conversion.

Note: This is a simplified version focusing on core CRUD and execution.
Legacy features (deployments, agents/connections model) are deprecated.
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
import asyncio
import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status, Request
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# SDK imports
from workflow_core_sdk import WorkflowsService, ExecutionsService

# Adapter imports
from adapters import WorkflowAdapter, ExecutionAdapter, RequestAdapter, ResponseAdapter

# Database
from db.database import get_db
from db import schemas

# In-memory stub store of deployed workflow IDs (non-persistent)
DEPLOYED_WORKFLOW_IDS: set[str] = set()


router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post("/")
def create_workflow(workflow: schemas.WorkflowCreate, db: Session = Depends(get_db)):
    """
    Create a new workflow.

    ✅ MIGRATED TO SDK with adapter layer for backwards compatibility.
    """
    # Adapt request from AS to SDK format
    sdk_workflow_data = RequestAdapter.adapt_workflow_create_request(workflow.model_dump())

    # Create workflow via SDK
    sdk_workflow = WorkflowsService.create_workflow(db, sdk_workflow_data)

    # Adapt response to Agent Studio format (pass db for agent data lookup)
    as_response = ResponseAdapter.adapt_workflow_response(sdk_workflow, db)

    return as_response


@router.get("/")
def list_workflows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    List all workflows.

    ✅ MIGRATED TO SDK with adapter layer for backwards compatibility.
    """
    # Get workflows from SDK
    sdk_workflows = WorkflowsService.list_workflows_entities(db, offset=skip, limit=limit)

    # Adapt response to Agent Studio format (pass db for agent data lookup)
    as_response = [ResponseAdapter.adapt_workflow_response(wf, db) for wf in sdk_workflows]

    return as_response


@router.get("/{workflow_id}")
def get_workflow(workflow_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Get a specific workflow by ID.

    ✅ MIGRATED TO SDK with adapter layer for backwards compatibility.
    """
    # Get workflow from SDK
    sdk_workflow = WorkflowsService.get_workflow_entity(db, str(workflow_id))

    if not sdk_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Adapt response to Agent Studio format (pass db for agent data lookup)
    as_response = ResponseAdapter.adapt_workflow_response(sdk_workflow, db)

    return as_response


@router.put("/{workflow_id}")
def update_workflow(
    workflow_id: uuid.UUID,
    workflow_update: schemas.WorkflowUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a workflow.

    ✅ MIGRATED TO SDK with adapter layer for backwards compatibility.
    """
    # Get existing workflow
    sdk_workflow = WorkflowsService.get_workflow_entity(db, str(workflow_id))

    if not sdk_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Build update data from the workflow_update
    update_data = workflow_update.model_dump(exclude_unset=True)

    # Convert Agent Studio update payload to SDK format (especially configuration)
    sdk_update = RequestAdapter.adapt_workflow_update_request(update_data)

    # Start from existing configuration and merge in the updated configuration
    existing_config = sdk_workflow.configuration.copy() if sdk_workflow.configuration else {}
    if "configuration" in sdk_update:
        # Shallow merge is sufficient because steps/connections replace whole arrays
        existing_config.update(sdk_update["configuration"])  # replaces steps if provided

    # Build payload expected by DatabaseService.save_workflow (must nest under "configuration")
    save_payload: Dict[str, Any] = {
        "configuration": existing_config,
    }

    # Apply top-level fields if provided
    if "name" in update_data:
        save_payload["name"] = update_data["name"]
    if "description" in update_data:
        save_payload["description"] = update_data["description"]
    if "version" in update_data:
        save_payload["version"] = update_data["version"]
    if "tags" in update_data:
        save_payload["tags"] = update_data["tags"]

    # Save updated workflow (save_workflow handles updates)
    from workflow_core_sdk.db.service import DatabaseService

    db_service = DatabaseService()
    db_service.save_workflow(db, str(workflow_id), save_payload)

    # Get updated workflow
    updated_workflow = WorkflowsService.get_workflow_entity(db, str(workflow_id))

    # Adapt response to Agent Studio format (pass db for agent data lookup)
    as_response = ResponseAdapter.adapt_workflow_response(updated_workflow, db)

    return as_response


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Delete a workflow.

    ✅ MIGRATED TO SDK with adapter layer for backwards compatibility.
    """
    # Delete workflow via SDK
    success = WorkflowsService.delete_workflow(db, str(workflow_id))

    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"message": "Workflow deleted successfully", "workflow_id": str(workflow_id)}


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: uuid.UUID,
    execution_request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Execute a workflow synchronously (with timeout).

    ✅ MIGRATED TO SDK - Uses SDK's WorkflowEngine for execution.

    Note: This is a simplified synchronous execution. For streaming, use /{workflow_id}/stream
    """
    from workflow_core_sdk.execution.context_impl import ExecutionContext

    # Check if execution engine is available
    if not hasattr(request.app.state, "workflow_engine"):
        raise HTTPException(
            status_code=503, detail="Workflow execution engine not initialized. Please restart the application."
        )

    workflow_engine = request.app.state.workflow_engine

    # Get workflow from SDK
    sdk_workflow = WorkflowsService.get_workflow_entity(db, str(workflow_id))

    if not sdk_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Create execution context
    execution_id = str(uuid.uuid4())

    # Build workflow config with workflow_id for execution context
    workflow_config_for_execution = sdk_workflow.configuration.copy() if sdk_workflow.configuration else {}
    workflow_config_for_execution["workflow_id"] = str(workflow_id)
    workflow_config_for_execution["name"] = sdk_workflow.name

    # Build execution order from connections/dependencies and expand "$prev" based on graph (non-streaming)
    try:
        steps_list = workflow_config_for_execution.get("steps") or []
        connections = workflow_config_for_execution.get("connections") or []

        # Index steps by id and ensure config exists
        step_by_id = {}
        for s in steps_list:
            if "config" not in s or s["config"] is None:
                s["config"] = {}
            sid = s.get("step_id")
            if sid:
                step_by_id[sid] = s

        # Build graph: incoming and outgoing adjacency
        incoming = {sid: [] for sid in step_by_id.keys()}
        outgoing = {sid: [] for sid in step_by_id.keys()}
        if connections:
            for c in connections:
                src = c.get("source_step_id") or c.get("source_agent_id")
                tgt = c.get("target_step_id") or c.get("target_agent_id")
                if src in step_by_id and tgt in step_by_id and src != tgt:
                    incoming[tgt].append(src)
                    outgoing[src].append(tgt)
        else:
            # Fall back to explicit dependencies on steps
            for sid, s in step_by_id.items():
                for dep in s.get("dependencies") or []:
                    if dep in step_by_id and dep != sid:
                        incoming[sid].append(dep)
                        outgoing[dep].append(sid)

        # Topologically sort (stable with respect to original order)
        sid_order_idx = {s.get("step_id"): i for i, s in enumerate(steps_list)}
        in_deg = {sid: len(incoming[sid]) for sid in step_by_id.keys()}
        from collections import deque

        queue = [sid for sid, d in in_deg.items() if d == 0]
        queue.sort(key=lambda x: sid_order_idx.get(x, 0))
        dq = deque(queue)
        topo_order = []
        visited = set()
        while dq:
            u = dq.popleft()
            topo_order.append(u)
            visited.add(u)
            for v in outgoing.get(u, []):
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    dq.append(v)

        # Tree-shake using connections: keep only reachable from roots if connections exist
        if connections:
            reachable = set()
            roots = [sid for sid in step_by_id.keys() if len(incoming[sid]) == 0]
            stack = list(roots)
            while stack:
                u = stack.pop()
                if u in reachable:
                    continue
                reachable.add(u)
                for v in outgoing.get(u, []):
                    if v not in reachable:
                        stack.append(v)
            topo_order = [sid for sid in topo_order if sid in reachable]

        # Fallback: append any unvisited steps in original order
        for sid in [s.get("step_id") for s in steps_list]:
            if sid and sid not in topo_order:
                topo_order.append(sid)

        # Reorder steps_list to topological order
        workflow_config_for_execution["steps"] = [step_by_id[sid] for sid in topo_order if sid in step_by_id]

        # Normalize each step using graph-aware previous (single dependency)
        for sid in topo_order:
            s = step_by_id.get(sid)
            if not s:
                continue
            # Guarantee config exists
            if "config" not in s or s["config"] is None:
                s["config"] = {}

            # Ensure dependencies reflect the graph if missing
            if not s.get("dependencies") and incoming.get(sid):
                # preserve order and uniqueness
                seen = set()
                s["dependencies"] = [d for d in incoming[sid] if not (d in seen or seen.add(d))]

            # Pick a unique previous dependency if unambiguous
            unique_dep = None
            deps = s.get("dependencies") or []
            if isinstance(deps, list) and len(deps) == 1:
                unique_dep = deps[0]
            elif len(incoming.get(sid, [])) == 1:
                unique_dep = incoming[sid][0]

            s["config"]["previous_step_id"] = unique_dep

            # Normalize param_mapping and input_mapping
            imap = s.get("input_mapping") or s["config"].get("input_mapping") or {}
            pmap = s["config"].get("param_mapping")

            if isinstance(pmap, dict):
                need_response_alias = False
                new_pmap = {}
                for k, v in pmap.items():
                    if isinstance(v, str):
                        if v.startswith("$prev.response."):
                            need_response_alias = True
                            parts = v.split(".", 2)
                            new_pmap[k] = f"response.{parts[2]}" if len(parts) > 2 else "response"
                        elif v.startswith("response."):
                            need_response_alias = True
                            new_pmap[k] = v
                        else:
                            new_pmap[k] = v
                    else:
                        new_pmap[k] = v
                s["config"]["param_mapping"] = new_pmap
                if need_response_alias and "response" not in imap:
                    imap["response"] = "$prev"

            # Expand $prev using unique_dep if available
            if isinstance(imap, dict):
                new_imap = {}
                for k, v in imap.items():
                    if isinstance(v, str) and unique_dep:
                        if v == "$prev":
                            new_imap[k] = unique_dep
                        elif v.startswith("$prev."):
                            new_imap[k] = f"{unique_dep}.{v.split('.', 1)[1]}"
                        else:
                            new_imap[k] = v
                    else:
                        new_imap[k] = v
                s["input_mapping"] = new_imap
            else:
                s["input_mapping"] = imap or {}
    except Exception as _e:
        logger.debug(f"Graph-based mapping preparation (sync) skipped: {_e}")

    # Build user context
    from workflow_core_sdk.execution.context_impl import UserContext

    user_context = UserContext(
        user_id=execution_request.get("user_id"),
        session_id=execution_request.get("session_id"),
    )

    # Create execution context
    execution_context = ExecutionContext(
        workflow_config=workflow_config_for_execution,
        user_context=user_context,
        execution_id=execution_id,
        workflow_engine=workflow_engine,
    )

    try:
        # Execute workflow synchronously
        await workflow_engine.execute_workflow(execution_context)

        # Convert step results to serializable format
        step_results = {}
        for step_id, result in execution_context.step_results.items():
            step_results[step_id] = {
                "step_id": result.step_id,
                "status": result.status.value,
                "output_data": result.output_data,
                "error_message": result.error_message,
                "execution_time_ms": result.execution_time_ms,
            }

        # Return response
        return {
            "execution_id": execution_id,
            "status": execution_context.status.value
            if hasattr(execution_context.status, "value")
            else str(execution_context.status),
            "step_results": step_results,
            "step_io_data": execution_context.step_io_data,
            "global_variables": execution_context.global_variables,
            "execution_summary": execution_context.get_execution_summary(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.post("/{workflow_id}/execute/async", status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow_async(
    workflow_id: uuid.UUID,
    execution_request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Execute a workflow asynchronously in the background.

    ✅ MIGRATED TO SDK - Uses SDK's WorkflowEngine for async execution.

    Returns immediately with execution_id. Use GET /api/executions/{execution_id} to check status.
    """
    from workflow_core_sdk.execution.context_impl import ExecutionContext

    # Check if execution engine is available
    if not hasattr(request.app.state, "workflow_engine"):
        raise HTTPException(
            status_code=503, detail="Workflow execution engine not initialized. Please restart the application."
        )

    workflow_engine = request.app.state.workflow_engine

    # Get workflow from SDK
    sdk_workflow = WorkflowsService.get_workflow_entity(db, str(workflow_id))

    if not sdk_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Create execution context
    execution_id = str(uuid.uuid4())

    # Build workflow config with workflow_id for execution context
    workflow_config_for_execution = sdk_workflow.configuration.copy() if sdk_workflow.configuration else {}
    workflow_config_for_execution["workflow_id"] = str(workflow_id)
    workflow_config_for_execution["name"] = sdk_workflow.name

    # Build user context
    from workflow_core_sdk.execution.context_impl import UserContext

    user_context = UserContext(
        user_id=execution_request.get("user_id"),
        session_id=execution_request.get("session_id"),
    )

    # Create execution context
    execution_context = ExecutionContext(
        workflow_config=workflow_config_for_execution,
        user_context=user_context,
        execution_id=execution_id,
        workflow_engine=workflow_engine,
    )

    # Execute workflow in background
    async def run_workflow():
        try:
            await workflow_engine.execute_workflow(execution_context)
        except Exception as e:
            execution_context.fail_execution(str(e))

    # Start execution as background task
    asyncio.create_task(run_workflow())

    # Return immediately with execution_id
    return {
        "execution_id": execution_id,
        "status": "queued",
        "message": "Workflow execution started in background",
    }


@router.post("/{workflow_id}/stream")
async def execute_workflow_stream(
    workflow_id: uuid.UUID,
    execution_request: schemas.WorkflowStreamExecutionRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Execute a workflow with streaming response.

    ✅ MIGRATED TO SDK - Uses SDK's WorkflowEngine with streaming support.
    """
    from workflow_core_sdk.execution.context_impl import ExecutionContext
    from workflow_core_sdk.execution.streaming import stream_manager, create_sse_stream, get_sse_headers, create_status_event

    # Check if execution engine is available
    if not hasattr(request.app.state, "workflow_engine"):
        raise HTTPException(
            status_code=503, detail="Workflow execution engine not initialized. Please restart the application."
        )

    workflow_engine = request.app.state.workflow_engine

    # Get workflow from SDK
    sdk_workflow = WorkflowsService.get_workflow_entity(db, str(workflow_id))

    if not sdk_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Create execution context
    execution_id = str(uuid.uuid4())

    # Build workflow config with workflow_id for execution context
    workflow_config_for_execution = sdk_workflow.configuration.copy() if sdk_workflow.configuration else {}
    workflow_config_for_execution["workflow_id"] = str(workflow_id)
    workflow_config_for_execution["name"] = sdk_workflow.name

    # Enable streaming for all agent steps in the workflow
    # AND fetch agent configuration from database if config is empty
    if "steps" in workflow_config_for_execution:
        for step in workflow_config_for_execution["steps"]:
            if step.get("step_type") == "agent_execution":
                if "config" not in step:
                    step["config"] = {}

                # Resolve the agent identifier correctly: prefer config.agent_id
                step_config = step["config"]
                agent_id = step_config.get("agent_id") or step.get("agent_id") or step.get("step_id")

                # Ensure step_id is available inside config for streaming emissions
                try:
                    step_config["step_id"] = step.get("step_id")
                except Exception:
                    pass

                # If config is missing critical fields, fetch from database
                if not step_config.get("system_prompt") or not step_config.get("model"):
                    logger.info(f"Fetching agent configuration from database for agent: {agent_id}")

                    try:
                        # Fetch agent from database using SDK service
                        from workflow_core_sdk import AgentsService, PromptsService

                        sdk_agent = AgentsService.get_agent(db, agent_id)
                        if sdk_agent:
                            logger.info(f"Found agent in database: {sdk_agent.name}")
                            # Ensure downstream step sees the agent by name for DB tool lookup
                            step_config["agent_name"] = sdk_agent.name

                            # Fetch system prompt
                            system_prompt = PromptsService.get_prompt(db, str(sdk_agent.system_prompt_id))
                            if system_prompt:
                                logger.info(f"Found system prompt: {system_prompt.prompt_label}")

                                # Merge agent configuration into step config
                                step_config["system_prompt"] = system_prompt.prompt
                                step_config["model"] = system_prompt.ai_model_name or "gpt-4o-mini"

                                # Extract temperature from hyper_parameters
                                if system_prompt.hyper_parameters and "temperature" in system_prompt.hyper_parameters:
                                    try:
                                        temp_value = system_prompt.hyper_parameters["temperature"]
                                        step_config["temperature"] = (
                                            float(temp_value) if isinstance(temp_value, (str, int, float)) else 0.7
                                        )
                                    except (ValueError, TypeError):
                                        step_config["temperature"] = 0.7
                                else:
                                    step_config["temperature"] = 0.7

                                # Extract AS-specific fields from provider_config
                                provider_config = sdk_agent.provider_config or {}
                                step_config["response_type"] = provider_config.get("response_type", "json")
                                step_config["routing_options"] = provider_config.get("routing_options", {})
                                step_config["max_retries"] = provider_config.get("max_retries", 3)

                                # Fetch agent's tool bindings and convert to functions format
                                tool_bindings = AgentsService.list_agent_tools(db, agent_id)
                                functions = []

                                for binding in tool_bindings:
                                    if binding.is_active:
                                        # Fetch the actual tool to get its name and schema
                                        from workflow_core_sdk.services.tools_service import ToolsService
                                        from workflow_core_sdk.tools.registry import tool_registry

                                        tool_name = None
                                        tool_description = ""
                                        tool_parameters = {}

                                        # Try to get tool from database first
                                        try:
                                            db_tool = ToolsService.get_db_tool_by_id(db, str(binding.tool_id))
                                            if db_tool:
                                                tool_name = db_tool.name
                                                tool_description = db_tool.description or ""
                                                if db_tool.parameters_schema:
                                                    tool_parameters = db_tool.parameters_schema
                                        except Exception:
                                            pass

                                        # If not found in DB, try getting from unified registry
                                        if not tool_name:
                                            try:
                                                unified_tools = tool_registry.get_unified_tools(db)
                                                for unified_tool in unified_tools:
                                                    if unified_tool.db_id and str(unified_tool.db_id) == str(binding.tool_id):
                                                        tool_name = unified_tool.name
                                                        tool_description = unified_tool.description or ""
                                                        if unified_tool.parameters_schema:
                                                            tool_parameters = unified_tool.parameters_schema
                                                        break
                                            except Exception:
                                                pass

                                        # Fallback to tool_id if we couldn't find the tool
                                        if not tool_name:
                                            tool_name = str(binding.tool_id)

                                        # Convert tool binding to ChatCompletionToolParam format
                                        functions.append(
                                            {
                                                "type": "function",
                                                "function": {
                                                    "name": tool_name,
                                                    "description": tool_description,
                                                    "parameters": binding.override_parameters or tool_parameters,
                                                },
                                            }
                                        )

                                # Merge with existing functions (e.g., agent tools from RequestAdapter)
                                existing_functions = step_config.get("functions", [])
                                if existing_functions:
                                    # Add DB tools to existing functions (agent tools take precedence)
                                    step_config["functions"] = existing_functions + functions
                                else:
                                    step_config["functions"] = functions
                                logger.info(
                                    f"Merged agent config: model={step_config['model']}, functions={len(step_config['functions'])}"
                                )
                            else:
                                logger.warning(f"System prompt not found for agent {agent_id}")
                        else:
                            logger.warning(f"Agent not found in database: {agent_id}")

                    except Exception as e:
                        logger.error(f"Error fetching agent configuration: {e}", exc_info=True)
                        # Continue execution - step will fail with proper error message

                # ALWAYS disable interactive mode for workflow-based agent execution
                # (agents should execute immediately, not wait for user input)
                step["config"]["interactive"] = False

                # Enable streaming for this agent step
                step["config"]["stream"] = True
                logger.info(f"Enabled streaming for agent step: {step.get('step_id')}")

    # Build execution order from connections/dependencies and expand "$prev" based on graph (streaming)
    # - Topologically order steps using connections (fallback to dependencies)
    # - Expand "$prev" only when a single dependency exists
    # - Promote config.input_mapping to top-level input_mapping if needed
    try:
        steps_list = workflow_config_for_execution.get("steps") or []
        connections = workflow_config_for_execution.get("connections") or []

        # Index steps by id and ensure config exists
        step_by_id = {}
        for s in steps_list:
            if "config" not in s or s["config"] is None:
                s["config"] = {}
            sid = s.get("step_id")
            if sid:
                step_by_id[sid] = s

        # Build graph from connections (or dependencies)
        incoming = {sid: [] for sid in step_by_id.keys()}
        outgoing = {sid: [] for sid in step_by_id.keys()}
        if connections:
            for c in connections:
                src = c.get("source_step_id") or c.get("source_agent_id")
                tgt = c.get("target_step_id") or c.get("target_agent_id")
                if src in step_by_id and tgt in step_by_id and src != tgt:
                    incoming[tgt].append(src)
                    outgoing[src].append(tgt)
        else:
            for sid, s in step_by_id.items():
                for dep in s.get("dependencies") or []:
                    if dep in step_by_id and dep != sid:
                        incoming[sid].append(dep)
                        outgoing[dep].append(sid)

        # Stable topological ordering
        sid_order_idx = {s.get("step_id"): i for i, s in enumerate(steps_list)}
        in_deg = {sid: len(incoming[sid]) for sid in step_by_id.keys()}
        from collections import deque

        queue = [sid for sid, d in in_deg.items() if d == 0]
        queue.sort(key=lambda x: sid_order_idx.get(x, 0))
        dq = deque(queue)
        topo_order = []
        visited = set()
        while dq:
            u = dq.popleft()
            topo_order.append(u)
            visited.add(u)
            for v in outgoing.get(u, []):
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    dq.append(v)

        # Tree-shake reachable nodes when connections exist
        if connections:
            reachable = set()
            roots = [sid for sid in step_by_id.keys() if len(incoming[sid]) == 0]
            stack = list(roots)
            while stack:
                u = stack.pop()
                if u in reachable:
                    continue
                reachable.add(u)
                for v in outgoing.get(u, []):
                    if v not in reachable:
                        stack.append(v)
            topo_order = [sid for sid in topo_order if sid in reachable]

        # Fallback append any missing by original order
        for sid in [s.get("step_id") for s in steps_list]:
            if sid and sid not in topo_order:
                topo_order.append(sid)

        # Reorder steps
        workflow_config_for_execution["steps"] = [step_by_id[sid] for sid in topo_order if sid in step_by_id]

        # Per-step normalization
        for sid in topo_order:
            s = step_by_id.get(sid)
            if not s:
                continue
            if "config" not in s or s["config"] is None:
                s["config"] = {}

            # Ensure dependencies reflect the graph if missing
            if not s.get("dependencies") and incoming.get(sid):
                seen = set()
                s["dependencies"] = [d for d in incoming[sid] if not (d in seen or seen.add(d))]

            # Resolve unique previous dependency
            unique_dep = None
            deps = s.get("dependencies") or []
            if isinstance(deps, list) and len(deps) == 1:
                unique_dep = deps[0]
            elif len(incoming.get(sid, [])) == 1:
                unique_dep = incoming[sid][0]

            s["config"]["previous_step_id"] = unique_dep

            # Normalize/expand mappings
            imap = s.get("input_mapping") or s["config"].get("input_mapping") or {}
            pmap = s["config"].get("param_mapping")

            if isinstance(pmap, dict):
                need_response_alias = False
                new_pmap = {}
                for k, v in pmap.items():
                    if isinstance(v, str):
                        if v.startswith("$prev.response."):
                            need_response_alias = True
                            parts = v.split(".", 2)
                            new_pmap[k] = f"response.{parts[2]}" if len(parts) > 2 else "response"
                        elif v.startswith("response."):
                            need_response_alias = True
                            new_pmap[k] = v
                        else:
                            new_pmap[k] = v
                    else:
                        new_pmap[k] = v
                s["config"]["param_mapping"] = new_pmap
                if need_response_alias and "response" not in imap:
                    imap["response"] = "$prev"

            if isinstance(imap, dict):
                new_imap = {}
                for k, v in imap.items():
                    if isinstance(v, str) and unique_dep:
                        if v == "$prev":
                            new_imap[k] = unique_dep
                        elif v.startswith("$prev."):
                            new_imap[k] = f"{unique_dep}.{v.split('.', 1)[1]}"
                        else:
                            new_imap[k] = v
                    else:
                        new_imap[k] = v
                s["input_mapping"] = new_imap
            else:
                s["input_mapping"] = imap or {}
    except Exception as _e:
        logger.debug(f"Graph-based mapping preparation (stream) skipped: {_e}")

    # Build user context
    from workflow_core_sdk.execution.context_impl import UserContext

    user_context = UserContext(
        user_id=execution_request.user_id,
        session_id=execution_request.session_id,
    )

    # Create execution context
    execution_context = ExecutionContext(
        workflow_config=workflow_config_for_execution,
        user_context=user_context,
        execution_id=execution_id,
        workflow_engine=workflow_engine,
    )

    # Pass query and chat_history to the execution context as trigger data
    # Normalize chat history coming from various frontends (actor/role/isBot formats),
    # drop any trailing duplicate of the current user query, and build LLM-ready messages.
    if execution_request.query:
        def _normalize_history(raw_history: Optional[List[Dict[str, Any]]], current_query: str) -> List[Dict[str, str]]:
            normalized: List[Dict[str, str]] = []
            if not raw_history:
                return normalized
            for item in raw_history:
                try:
                    role = None
                    content = None
                    if isinstance(item, dict):
                        if "role" in item and "content" in item:
                            role = str(item.get("role"))
                            content = str(item.get("content"))
                        elif "actor" in item and "content" in item:
                            actor = str(item.get("actor"))
                            role = "assistant" if actor.lower() in ("bot", "assistant", "model") else "user"
                            content = str(item.get("content"))
                        elif ("isBot" in item or "is_bot" in item) and "text" in item:
                            is_bot = bool(item.get("isBot") if "isBot" in item else item.get("is_bot"))
                            role = "assistant" if is_bot else "user"
                            content = str(item.get("text"))
                    if role and content:
                        normalized.append({"role": role, "content": content})
                except Exception:
                    # Skip malformed entries safely
                    continue
            # Drop trailing duplicate of current query if present (common in UIs that include the in-flight message)
            if normalized and normalized[-1].get("role") == "user" and normalized[-1].get("content") == current_query:
                normalized = normalized[:-1]
            return normalized

        # Build trigger data
        history = _normalize_history(execution_request.chat_history, execution_request.query)
        messages = history + [{"role": "user", "content": execution_request.query}]
        trigger_data = {
            "current_message": execution_request.query,
            "messages": messages,
        }
        if history:
            trigger_data["chat_history"] = history

        # Store trigger data in step_io_data for agent steps to access
        execution_context.step_io_data["trigger"] = trigger_data
        logger.info(f"Added trigger data with query: {execution_request.query[:50]}... (history={len(history)})")

    # Create a queue for streaming
    queue = asyncio.Queue(maxsize=1000)

    async def event_generator():
        try:
            logger.info(f"Starting event generator for execution: {execution_id}")
            # Add this connection to the stream manager
            stream_manager.add_execution_stream(execution_id, queue)
            logger.info("Added execution stream to manager")

            # Start workflow execution in background
            async def run_workflow():
                try:
                    logger.info("Starting workflow execution in background")
                    await workflow_engine.execute_workflow(execution_context)
                    logger.info("Workflow execution completed")
                except Exception as e:
                    logger.error(f"Workflow execution failed: {e}", exc_info=True)
                    execution_context.fail_execution(str(e))

            # Start execution as background task
            asyncio.create_task(run_workflow())
            logger.info(f"Background task created")

            # Stream events from the queue, converting SDK format to Agent Studio format
            from adapters.streaming_adapter import StreamingAdapter

            # Get SDK stream
            logger.info("Creating SDK event stream")
            sdk_event_stream = create_sse_stream(queue, heartbeat_interval=30, max_events=5000)

            # Convert SDK stream to Agent Studio format and yield
            logger.info("Starting to adapt and yield events")
            async for agent_studio_event in StreamingAdapter.adapt_stream(
                sdk_event_stream, execution_id=execution_id, workflow_id=str(workflow_id)
            ):
                yield agent_studio_event

        except asyncio.CancelledError:
            logger.info("Event generator cancelled")
            pass
        except Exception as e:
            logger.error(f"Event generator error: {e}", exc_info=True)
            # Send error event in Agent Studio format
            import json

            error_chunk = {"type": "error", "message": f"Error: {str(e)}\n"}
            yield f"data: {json.dumps(error_chunk)}\n\n"
        finally:
            # Clean up the connection
            stream_manager.remove_execution_stream(execution_id, queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=get_sse_headers())


# Deprecated endpoints (kept for backwards compatibility but return not implemented)


@router.post("/{workflow_id}/agents")
def add_agent_to_workflow(workflow_id: uuid.UUID):
    """
    DEPRECATED: Agent/connection model is deprecated in SDK.
    Returns success to keep frontend working.
    """
    return {
        "message": "Agent/connection model is deprecated. Use workflow configuration with steps instead.",
        "workflow_id": str(workflow_id),
    }


@router.post("/{workflow_id}/connections")
def add_connection_to_workflow(workflow_id: uuid.UUID):
    """
    DEPRECATED: Agent/connection model is deprecated in SDK.
    Returns success to keep frontend working.
    """
    return {
        "message": "Agent/connection model is deprecated. Use workflow configuration with steps instead.",
        "workflow_id": str(workflow_id),
    }


@router.post("/{workflow_id}/deploy", response_model=schemas.WorkflowDeploymentResponse)
def deploy_workflow(
    workflow_id: uuid.UUID,
    deployment: schemas.WorkflowDeploymentRequest,
    db: Session = Depends(get_db),
):
    """
    STUB IMPLEMENTATION: Return a WorkflowDeployment-shaped object so the frontend
    can proceed. No persistent deployment is created.
    """
    # Fetch the workflow and adapt to Agent Studio response for embedding
    sdk_workflow = WorkflowsService.get_workflow_entity(db, str(workflow_id))
    if not sdk_workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    as_workflow = ResponseAdapter.adapt_workflow_response(sdk_workflow, db)

    now = datetime.now(timezone.utc)
    deployment_id = uuid.uuid4()

    # Build a stub deployment object matching the frontend's expected shape
    payload: Dict[str, Any] = {
        "workflow_id": str(workflow_id),
        "environment": deployment.environment or "production",
        "deployment_name": deployment.deployment_name,
        "deployed_by": deployment.deployed_by,
        "runtime_config": deployment.runtime_config,
        "id": 0,
        "deployment_id": str(deployment_id),
        "status": "active",
        "deployed_at": now,
        "stopped_at": None,
        "last_executed": None,
        "execution_count": 0,
        "error_count": 0,
        "last_error": None,
        # Embed the full workflow response; Pydantic will coerce down to WorkflowInDB
        # in the response model as needed
        "workflow": as_workflow,
    }

    # Track as deployed in this process (stubbed, non-persistent)
    DEPLOYED_WORKFLOW_IDS.add(str(workflow_id))
    return payload


@router.get("/deployments/active", response_model=List[schemas.WorkflowDeploymentResponse])
def list_active_deployments(db: Session = Depends(get_db)):
    """
    STUB IMPLEMENTATION: Return synthesized active deployments for workflows that
    were "deployed" via the stub endpoint in this process lifetime.
    Non-persistent; used only for UI convenience.
    """
    if not DEPLOYED_WORKFLOW_IDS:
        return []

    # Fetch workflows and synthesize deployment objects for those in the stub set
    sdk_workflows = WorkflowsService.list_workflows_entities(db, offset=0, limit=1000)
    deployments: list[Dict[str, Any]] = []

    for wf in sdk_workflows:
        as_workflow = ResponseAdapter.adapt_workflow_response(wf, db)
        wf_id = as_workflow.get("workflow_id")
        if not wf_id or wf_id not in DEPLOYED_WORKFLOW_IDS:
            continue

        # Deterministic deployment_id for stability across calls (per process)
        dep_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, f"deploy-{wf_id}")
        deployed_at = as_workflow.get("deployed_at") or datetime.now(timezone.utc)

        deployments.append(
            {
                "workflow_id": wf_id,
                "environment": "production",
                "deployment_name": f"default-{wf_id[:8]}",
                "deployed_by": None,
                "runtime_config": None,
                "id": 0,
                "deployment_id": str(dep_uuid),
                "status": "active",
                "deployed_at": deployed_at,
                "stopped_at": None,
                "last_executed": None,
                "execution_count": 0,
                "error_count": 0,
                "last_error": None,
                "workflow": as_workflow,
            }
        )

    return deployments


@router.post("/deployments/{deployment_name}/stop")
def stop_workflow_deployment(deployment_name: str):
    """
    DEPRECATED: Deployment model is deprecated in SDK.
    Returns success to keep frontend working.
    """
    # Return success instead of error to keep frontend working
    return {"message": "Deployment model is deprecated. No action taken.", "deployment_name": deployment_name}
