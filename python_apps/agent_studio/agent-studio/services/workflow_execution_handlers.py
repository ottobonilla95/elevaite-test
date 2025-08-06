"""
Workflow execution handlers for different workflow types.

This module contains the execution logic for:
- Deterministic workflows
- Hybrid workflows with conditional routing
- Traditional agent workflows
"""

import json
import time
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.workflow_execution_context import WorkflowExecutionContext
from services.workflow_execution_utils import (
    analyze_input_context,
    evaluate_condition,
    convert_to_deterministic_config,
    is_deterministic_workflow,
    is_hybrid_workflow,
)
from services.workflow_agent_builders import (
    build_dynamic_agent_store,
    build_single_agent_from_workflow,
    build_toshiba_agent_from_workflow,
    build_command_agent_from_workflow,
    build_root_agent_with_workflow_functions,
)
from schemas.deterministic_workflow import (
    WorkflowExecutionRequest as DetWorkflowExecutionRequest,
)
from db.schemas import workflows as schemas
from fastapi_logger import ElevaiteLogger
from db import crud


logger = ElevaiteLogger()


async def execute_deterministic_workflow(
    workflow, execution_request: schemas.WorkflowExecutionRequest, db: Session
) -> schemas.WorkflowExecutionResponse:
    """
    Execute a deterministic workflow using the deterministic workflow framework.
    """
    try:
        # Initialize workflow execution context
        workflow_context = WorkflowExecutionContext()

        # Convert the workflow configuration to deterministic workflow format
        deterministic_config = convert_to_deterministic_config(
            workflow, execution_request
        )

        # Create execution request for deterministic workflow
        det_execution_request = DetWorkflowExecutionRequest(
            workflow_id=str(workflow.workflow_id),
            input_data={
                "query": execution_request.query,
                "chat_history": execution_request.chat_history or [],
                "runtime_overrides": execution_request.runtime_overrides or {},
            },
            user_id=execution_request.user_id,
            session_id=execution_request.session_id,
        )

        # Execute the deterministic workflow
        with workflow_context.deterministic_workflow_execution(
            workflow_name=workflow.name,
            workflow_config=deterministic_config,
            session_id=execution_request.session_id,
            user_id=execution_request.user_id,
            db=db,
        ) as execution_id:

            # Add input data to workflow context
            workflow_context._active_workflows[execution_id]["step_data"][
                "input"
            ] = det_execution_request.input_data

            # Execute all steps
            results = await workflow_context.execute_workflow(execution_id, db)

            # Convert results to standard workflow execution response format
            return schemas.WorkflowExecutionResponse(
                status="success",
                response=json.dumps(results) if results else "{}",
                execution_id=execution_id,
                workflow_id=str(workflow.workflow_id),
                deployment_id="",
                timestamp=datetime.now().isoformat(),
            )

    except Exception as e:
        # Return error response in standard format
        return schemas.WorkflowExecutionResponse(
            status="error",
            response=json.dumps({"error": str(e)}),
            execution_id="",
            workflow_id=str(workflow.workflow_id),
            deployment_id="",
            timestamp=datetime.now().isoformat(),
        )


def execute_hybrid_workflow(
    workflow, execution_request: schemas.WorkflowExecutionRequest, db: Session
) -> schemas.WorkflowExecutionResponse:
    """
    Execute a hybrid workflow with conditional routing between deterministic and agent execution.
    """
    try:
        config = workflow.configuration
        execution_logic = config.get("execution_logic", {})
        routing_rules = execution_logic.get("routing_rules", [])

        # Analyze input to determine execution path
        input_context = analyze_input_context(execution_request)

        # Find matching routing rule
        selected_rule = None
        for rule in routing_rules:
            condition = rule.get("condition", "")
            if evaluate_condition(condition, input_context):
                selected_rule = rule
                break

        if not selected_rule:
            # Default to traditional agent execution
            return execute_traditional_workflow(workflow, execution_request, db)

        # Execute based on selected rule
        flow = selected_rule.get("flow", [])
        action = selected_rule.get("action", "")

        if action == "execute_tokenizer_then_router":
            return execute_tokenizer_then_router_flow(
                workflow, execution_request, db, flow
            )
        elif action == "execute_router_directly":
            return execute_router_directly_flow(workflow, execution_request, db, flow)
        else:
            # Fallback to traditional execution
            return execute_traditional_workflow(workflow, execution_request, db)

    except Exception as e:
        return schemas.WorkflowExecutionResponse(
            status="error",
            response=json.dumps(
                {"error": f"Hybrid workflow execution failed: {str(e)}"}
            ),
            execution_id="",
            workflow_id=str(workflow.workflow_id),
            deployment_id="",
            timestamp=datetime.now().isoformat(),
        )


def execute_tokenizer_then_router_flow(
    workflow,
    execution_request: schemas.WorkflowExecutionRequest,
    db: Session,
    flow: List[str],
) -> schemas.WorkflowExecutionResponse:
    """
    Execute tokenizer workflow first, then router agent with enhanced context.
    """
    try:
        # Step 1: Find and execute the tokenizer (deterministic workflow agent)
        agents = workflow.configuration.get("agents", [])
        tokenizer_agent = None
        router_agent = None

        for agent in agents:
            if agent.get("agent_type") == "DeterministicWorkflowAgent":
                tokenizer_agent = agent
            elif agent.get("agent_id") in flow and agent.get("agent_type") in [
                "CommandAgent",
                "RouterAgent",
            ]:
                router_agent = agent

        if not tokenizer_agent:
            raise ValueError(
                "No DeterministicWorkflowAgent found for tokenizer execution"
            )

        # Step 2: Execute tokenizer workflow
        tokenizer_config = tokenizer_agent.get("config", {})
        if tokenizer_config.get("workflow_type") == "deterministic":
            # Convert to deterministic workflow format and execute
            det_config = {
                "workflow_id": str(workflow.workflow_id) + "_tokenizer",
                "workflow_name": tokenizer_config.get("workflow_name", "Tokenizer"),
                "steps": tokenizer_config.get("steps", []),
                "execution_pattern": tokenizer_config.get(
                    "execution_pattern", "sequential"
                ),
            }

            # Execute deterministic workflow
            import asyncio

            workflow_context = WorkflowExecutionContext()

            with workflow_context.deterministic_workflow_execution(
                workflow_name=det_config["workflow_name"],
                workflow_config=det_config,
                session_id=execution_request.session_id,
                user_id=execution_request.user_id,
                db=db,
            ) as execution_id:
                workflow_context._active_workflows[execution_id]["step_data"][
                    "input"
                ] = {
                    "query": execution_request.query,
                    "chat_history": execution_request.chat_history or [],
                    "runtime_overrides": execution_request.runtime_overrides or {},
                }

                tokenizer_results = asyncio.run(
                    workflow_context.execute_workflow(execution_id, db)
                )

        # Step 3: Execute router agent with enhanced context from tokenizer
        if router_agent:
            # Build router agent with enhanced RAG capabilities
            enhanced_request = execution_request
            enhanced_request.runtime_overrides = (
                enhanced_request.runtime_overrides or {}
            )
            enhanced_request.runtime_overrides["tokenizer_results"] = tokenizer_results
            enhanced_request.runtime_overrides["vector_db_available"] = True

            # Execute router agent
            return execute_single_agent_with_config(
                workflow, enhanced_request, db, router_agent
            )
        else:
            # Return tokenizer results if no router agent
            return schemas.WorkflowExecutionResponse(
                status="success",
                response=json.dumps(tokenizer_results),
                workflow_id=str(workflow.workflow_id),
                deployment_id="",
                timestamp=datetime.now().isoformat(),
            )

    except Exception as e:
        return schemas.WorkflowExecutionResponse(
            status="error",
            response=json.dumps({"error": f"Tokenizer-router flow failed: {str(e)}"}),
            workflow_id=str(workflow.workflow_id),
            deployment_id="",
            timestamp=datetime.now().isoformat(),
        )


def execute_router_directly_flow(
    workflow,
    execution_request: schemas.WorkflowExecutionRequest,
    db: Session,
    flow: List[str],
) -> schemas.WorkflowExecutionResponse:
    """
    Execute router agent directly without tokenizer preprocessing.
    """
    try:
        agents = workflow.configuration.get("agents", [])
        router_agent = None

        for agent in agents:
            if agent.get("agent_id") in flow and agent.get("agent_type") in [
                "CommandAgent",
                "RouterAgent",
            ]:
                router_agent = agent
                break

        if not router_agent:
            # Fallback to traditional workflow execution
            return execute_traditional_workflow(workflow, execution_request, db)

        return execute_single_agent_with_config(
            workflow, execution_request, db, router_agent
        )

    except Exception as e:
        return schemas.WorkflowExecutionResponse(
            status="error",
            response=json.dumps({"error": f"Router direct flow failed: {str(e)}"}),
            workflow_id=str(workflow.workflow_id),
            deployment_id="",
            timestamp=datetime.now().isoformat(),
        )


# These functions will need to be imported from the original workflow_endpoints.py
# as they contain agent-specific logic that should remain in the endpoints file


def execute_traditional_workflow(
    workflow, execution_request: schemas.WorkflowExecutionRequest, db: Session
) -> schemas.WorkflowExecutionResponse:
    """
    Execute a traditional agent-based workflow (fallback for hybrid workflows).
    """
    # This reuses the existing workflow execution logic
    agents = workflow.configuration.get("agents", [])
    is_single_agent = len(agents) == 1

    if is_single_agent:
        # Single-agent workflow execution
        agent_config = agents[0]
        agent_type = agent_config.get("agent_type", "CommandAgent")

        if agent_type == "ToshibaAgent":
            agent = build_toshiba_agent_from_workflow(db, workflow, agent_config)
        else:
            agent = build_single_agent_from_workflow(db, workflow, agent_config)

        dynamic_agent_store = build_dynamic_agent_store(db, workflow)

        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                agent.execute,
                query=execution_request.query,
                chat_history=execution_request.chat_history,
                enable_analytics=False,
                dynamic_agent_store=dynamic_agent_store,
            )
            try:
                result = future.result(timeout=60)
            except concurrent.futures.TimeoutError:
                future.cancel()
                raise HTTPException(status_code=504, detail="Agent execution timed out")
    else:
        # Multi-agent workflow execution
        command_agent = build_command_agent_from_workflow(db, workflow)
        dynamic_agent_store = build_dynamic_agent_store(db, workflow)

        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            if execution_request.chat_history:
                future = executor.submit(
                    command_agent.execute_stream,
                    execution_request.query,
                    execution_request.chat_history,
                    dynamic_agent_store,
                )
            else:
                session_id = (
                    execution_request.session_id
                    or f"workflow_{workflow.workflow_id}_{int(time.time())}"
                )
                user_id = execution_request.user_id or "workflow_user"
                future = executor.submit(
                    command_agent.execute,
                    query=execution_request.query,
                    enable_analytics=True,
                    session_id=session_id,
                    user_id=user_id,
                    dynamic_agent_store=dynamic_agent_store,
                )
            try:
                result = future.result(timeout=60)
            except concurrent.futures.TimeoutError:
                future.cancel()
                raise HTTPException(
                    status_code=504, detail="CommandAgent execution timed out"
                )

    # Format response
    def safe_json_serialize(obj):
        try:
            if isinstance(obj, str):
                return json.dumps({"content": obj})
            elif isinstance(obj, (dict, list, int, float, bool)) or obj is None:
                return json.dumps(obj)
            elif hasattr(obj, "__iter__") and not isinstance(obj, str):
                return json.dumps({"content": str(list(obj))})
            else:
                return json.dumps({"content": str(obj)})
        except (TypeError, ValueError) as e:
            return json.dumps({"content": str(obj), "serialization_error": str(e)})

    formatted_response = safe_json_serialize(result)

    return schemas.WorkflowExecutionResponse(
        status="success",
        response=formatted_response,
        workflow_id=str(workflow.workflow_id),
        deployment_id="",
        timestamp=datetime.now().isoformat(),
    )


def execute_single_agent_with_config(
    workflow,
    execution_request: schemas.WorkflowExecutionRequest,
    db: Session,
    agent_config: Dict[str, Any],
) -> schemas.WorkflowExecutionResponse:
    """
    Execute a single agent with specific configuration.
    """
    agent_type = agent_config.get("agent_type", "CommandAgent")

    if agent_type == "ToshibaAgent":
        agent = build_toshiba_agent_from_workflow(db, workflow, agent_config)
    else:
        agent = build_single_agent_from_workflow(db, workflow, agent_config)

    dynamic_agent_store = build_dynamic_agent_store(db, workflow)

    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(
            agent.execute,
            query=execution_request.query,
            chat_history=execution_request.chat_history,
            enable_analytics=False,
            dynamic_agent_store=dynamic_agent_store,
        )
        try:
            result = future.result(timeout=60)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise HTTPException(status_code=504, detail="Agent execution timed out")

    def safe_json_serialize(obj):
        try:
            if isinstance(obj, str):
                return json.dumps({"content": obj})
            elif isinstance(obj, (dict, list, int, float, bool)) or obj is None:
                return json.dumps(obj)
            else:
                return json.dumps({"content": str(obj)})
        except (TypeError, ValueError) as e:
            return json.dumps({"content": str(obj), "serialization_error": str(e)})

    formatted_response = safe_json_serialize(result)

    return schemas.WorkflowExecutionResponse(
        status="success",
        response=formatted_response,
        workflow_id=str(workflow.workflow_id),
        deployment_id="",
        timestamp=datetime.now().isoformat(),
    )


def execute_workflow_background(
    execution_id: str,
    workflow_id: uuid.UUID,
    execution_request: schemas.WorkflowExecutionRequest,
):
    """
    Background task to execute a workflow asynchronously with detailed tracing.
    Updates execution status and workflow trace throughout the process.
    """
    from services.analytics_service import analytics_service, WorkflowStep

    try:
        # Update status to running and initialize tracing
        analytics_service.update_execution(
            execution_id, status="running", current_step="Initializing workflow"
        )

        # Get database session for background task
        from db.database import SessionLocal

        db = SessionLocal()

        try:
            # Get the workflow from database
            workflow = crud.get_workflow(db=db, workflow_id=workflow_id)
            if workflow is None:
                analytics_service.update_execution(
                    execution_id, status="failed", error="Workflow not found"
                )
                return

            # Check if this is a pure deterministic workflow
            if is_deterministic_workflow(workflow.configuration):
                analytics_service.update_execution(
                    execution_id,
                    status="running",
                    current_step="Executing deterministic workflow",
                )
                try:
                    result = asyncio.run(
                        execute_deterministic_workflow(workflow, execution_request, db)
                    )
                    analytics_service.update_execution(
                        execution_id,
                        status="completed",
                        result={"output": result.response},
                    )
                except Exception as e:
                    analytics_service.update_execution(
                        execution_id, status="failed", error=str(e)
                    )
                return

            # Check if this is a hybrid workflow with conditional execution
            if is_hybrid_workflow(workflow.configuration):
                analytics_service.update_execution(
                    execution_id,
                    status="running",
                    current_step="Executing hybrid workflow",
                )
                try:
                    result = execute_hybrid_workflow(workflow, execution_request, db)
                    analytics_service.update_execution(
                        execution_id,
                        status="completed",
                        result={"output": result.response},
                    )
                except Exception as e:
                    analytics_service.update_execution(
                        execution_id, status="failed", error=str(e)
                    )
                return

            # Initialize workflow tracing for traditional agent workflows
            agents = workflow.configuration.get("agents", [])
            connections = workflow.configuration.get("connections", [])
            estimated_steps = (
                len(agents) + len(connections) + 2
            )  # agents + connections + init + finalize

            analytics_service.init_workflow_trace(
                execution_id, str(workflow_id), estimated_steps
            )

            # Add initial step
            init_step = WorkflowStep(
                step_id=f"init_{execution_id}",
                step_type="data_processing",
                status="running",
                step_metadata={"description": "Initializing workflow execution"},
            )
            analytics_service.add_workflow_step(execution_id, init_step)
            analytics_service.update_execution(
                execution_id, current_step="Analyzing workflow structure", progress=0.1
            )

            # Determine workflow type and find root agent
            is_single_agent = len(agents) == 1

            # Find the root agent (entry point) - agent with no incoming connections
            root_agent_id = None
            if connections:
                # Get all target agent IDs (agents that have incoming connections)
                target_agent_ids = {conn.get("target_agent_id") for conn in connections}
                # Find agents that are not targets (no incoming connections)
                for agent in agents:
                    agent_id = agent.get("agent_id")
                    if agent_id and agent_id not in target_agent_ids:
                        root_agent_id = agent_id
                        break
            elif agents:
                # If no connections, use the first agent as root
                root_agent_id = agents[0].get("agent_id")

            if is_single_agent:
                # Single-agent workflow execution with tracing
                agent_config = agents[0]
                agent_type = agent_config.get("agent_type", "CommandAgent")

                # Add agent execution step
                agent_step = WorkflowStep(
                    step_id=f"agent_{agent_config.get('agent_id', 'unknown')}",
                    step_type="agent_execution",
                    agent_id=agent_config.get("agent_id"),
                    agent_name=agent_type,
                    status="pending",
                    input_data={"query": execution_request.query},
                    step_metadata={"agent_type": agent_type},
                )
                analytics_service.add_workflow_step(execution_id, agent_step)
                analytics_service.add_execution_path(execution_id, agent_type)

                analytics_service.update_execution(
                    execution_id, current_step=f"Executing {agent_type}", progress=0.3
                )
                analytics_service.update_workflow_step(
                    execution_id, agent_step.step_id, status="running"
                )

                try:
                    if agent_type == "ToshibaAgent":
                        agent = build_toshiba_agent_from_workflow(
                            db, workflow, agent_config
                        )
                    else:
                        agent = build_single_agent_from_workflow(
                            db, workflow, agent_config
                        )

                    # Build dynamic agent store for inter-agent communication
                    dynamic_agent_store = build_dynamic_agent_store(db, workflow)

                    result = agent.execute(
                        query=execution_request.query,
                        chat_history=execution_request.chat_history,
                        enable_analytics=False,
                        dynamic_agent_store=dynamic_agent_store,
                    )

                    # Update agent step as completed
                    analytics_service.update_workflow_step(
                        execution_id,
                        agent_step.step_id,
                        status="completed",
                        output_data={"result": str(result)},
                    )

                except Exception as agent_error:
                    analytics_service.update_workflow_step(
                        execution_id,
                        agent_step.step_id,
                        status="failed",
                        error=str(agent_error),
                    )
                    raise agent_error

            else:
                # Multi-agent workflow execution using root agent as entry point
                if root_agent_id:
                    # Use the root agent as the entry point
                    analytics_service.update_execution(
                        execution_id,
                        current_step="Executing root agent",
                        progress=0.2,
                    )

                    # Get the root agent from database
                    root_agent = crud.get_agent(db, uuid.UUID(root_agent_id))
                    if root_agent:
                        # Add root agent step
                        # Create root agent step with proper UUID to avoid conflicts
                        root_step = WorkflowStep(
                            step_id=str(uuid.uuid4()),  # Use proper UUID for step_id
                            step_type="agent_execution",
                            agent_id=root_agent_id,
                            agent_name=root_agent.name,
                            status="pending",
                            input_data={
                                "query": execution_request.query,
                                "agent_count": len(agents),
                            },
                            step_metadata={
                                "workflow_type": "multi_agent",
                                "root_agent": True,
                                "agent_type": root_agent.agent_type,
                            },
                        )
                        analytics_service.add_workflow_step(execution_id, root_step)
                        analytics_service.add_execution_path(
                            execution_id, root_agent.name
                        )

                        # Use the root agent with workflow functions
                        command_agent = build_root_agent_with_workflow_functions(
                            db, workflow
                        )
                    else:
                        analytics_service.update_execution(
                            execution_id,
                            status="failed",
                            error=f"Root agent {root_agent_id} not found",
                        )
                        return
                else:
                    # Fallback to CommandAgent orchestrator if no root agent found
                    analytics_service.update_execution(
                        execution_id,
                        current_step="Building CommandAgent orchestrator",
                        progress=0.2,
                    )

                    # Add orchestrator step
                    orchestrator_step = WorkflowStep(
                        step_id=f"orchestrator_{execution_id}",
                        step_type="agent_execution",
                        agent_name="CommandAgent",
                        status="pending",
                        input_data={
                            "query": execution_request.query,
                            "agent_count": len(agents),
                        },
                        step_metadata={
                            "workflow_type": "multi_agent",
                            "orchestrator": True,
                        },
                    )
                    analytics_service.add_workflow_step(execution_id, orchestrator_step)
                    analytics_service.add_execution_path(execution_id, "CommandAgent")

                    command_agent = build_root_agent_with_workflow_functions(
                        db, workflow
                    )
                dynamic_agent_store = build_dynamic_agent_store(db, workflow)

                analytics_service.update_execution(
                    execution_id,
                    current_step="Orchestrating workflow execution",
                    progress=0.4,
                )
                # Update the appropriate step as running
                if root_agent_id:
                    analytics_service.update_workflow_step(
                        execution_id, root_step.step_id, status="running"
                    )
                else:
                    analytics_service.update_workflow_step(
                        execution_id, orchestrator_step.step_id, status="running"
                    )

                # Note: Individual tool calls will be tracked by CommandAgent analytics
                # We don't create placeholder steps here - real tool calls will be captured

                try:
                    if execution_request.chat_history:
                        result = command_agent.execute_stream(
                            execution_request.query,
                            execution_request.chat_history,
                            dynamic_agent_store,
                        )
                        # Convert generator to string for storage
                        result = "".join(str(chunk) for chunk in result if chunk)
                    else:
                        session_id = (
                            execution_request.session_id
                            or f"workflow_{workflow_id}_{int(time.time())}"
                        )
                        user_id = execution_request.user_id or "workflow_user"
                        # Enable analytics with proper execution_id to track tool calls
                        result = command_agent.execute(
                            query=execution_request.query,
                            enable_analytics=True,
                            session_id=session_id,
                            user_id=user_id,
                            dynamic_agent_store=dynamic_agent_store,
                            execution_id=execution_id,  # Pass workflow execution_id
                        )

                    # Update the appropriate step as completed
                    if root_agent_id:
                        analytics_service.update_workflow_step(
                            execution_id,
                            root_step.step_id,
                            status="completed",
                            output_data={"result": str(result)},
                        )
                    else:
                        analytics_service.update_workflow_step(
                            execution_id,
                            orchestrator_step.step_id,
                            status="completed",
                            output_data={"result": str(result)},
                        )

                    # Mark sub-agent steps as completed (simplified for now)
                    for agent_config in agents:
                        agent_id = agent_config.get(
                            "agent_id", f"agent_{agents.index(agent_config)}"
                        )
                        analytics_service.update_workflow_step(
                            execution_id, f"sub_agent_{agent_id}", status="completed"
                        )
                        analytics_service.add_execution_path(
                            execution_id, agent_config.get("agent_type", "Unknown")
                        )

                except Exception as orchestrator_error:
                    # Update the appropriate step as failed
                    if root_agent_id:
                        analytics_service.update_workflow_step(
                            execution_id,
                            root_step.step_id,
                            status="failed",
                            error=str(orchestrator_error),
                        )
                    else:
                        analytics_service.update_workflow_step(
                            execution_id,
                            orchestrator_step.step_id,
                            status="failed",
                            error=str(orchestrator_error),
                        )
                    raise orchestrator_error

            # Add finalization step
            final_step = WorkflowStep(
                step_id=f"finalize_{execution_id}",
                step_type="data_processing",
                status="running",
                step_metadata={"description": "Finalizing workflow execution"},
            )
            analytics_service.add_workflow_step(execution_id, final_step)
            analytics_service.update_execution(
                execution_id, current_step="Finalizing results", progress=0.9
            )

            # Format the final response
            import json

            def safe_json_serialize(obj):
                try:
                    if isinstance(obj, str):
                        return json.dumps({"content": obj})
                    elif isinstance(obj, (dict, list, int, float, bool)) or obj is None:
                        return json.dumps(obj)
                    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
                        return json.dumps({"content": str(list(obj))})
                    else:
                        return json.dumps({"content": str(obj)})
                except (TypeError, ValueError) as e:
                    return json.dumps(
                        {"content": str(obj), "serialization_error": str(e)}
                    )

            formatted_response = safe_json_serialize(result)
            response_data = {
                "status": "success",
                "response": formatted_response,
                "workflow_id": str(workflow_id),
                "execution_id": execution_id,
                "timestamp": datetime.now().isoformat(),
            }

            # Complete finalization step
            analytics_service.update_workflow_step(
                execution_id,
                final_step.step_id,
                status="completed",
                output_data=response_data,
            )

            # Update execution as completed
            analytics_service.update_execution(
                execution_id,
                status="completed",
                progress=1.0,
                current_step="Completed",
                result=response_data,
                db=db,
            )

        finally:
            db.close()

    except Exception as e:
        # Update execution as failed
        analytics_service.update_execution(execution_id, status="failed", error=str(e))
