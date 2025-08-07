from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Literal
from contextlib import contextmanager
import uuid
from sqlalchemy.orm import Session
from threading import Lock
from pydantic import BaseModel

from fastapi_logger import ElevaiteLogger
from db import models


class WorkflowStep(BaseModel):
    step_id: str
    step_type: Literal[
        # Existing AI workflow step types
        "agent_execution",
        "tool_call",
        "decision_point",
        "data_processing",
        # New deterministic workflow step types
        "data_input",
        "data_output",
        "transformation",
        "validation",
        "batch_processing",
        "conditional_branch",
        "parallel_execution",
        "aggregation",
        "notification",
        "file_reader",
        "text_chunking",
        "embedding_generation",
        "vector_storage",
    ]
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    step_metadata: Dict[str, Any] = {}


class WorkflowTrace(BaseModel):
    execution_id: str
    workflow_id: str
    current_step_index: int = 0
    total_steps: int = 0
    steps: List[WorkflowStep] = []
    execution_path: List[str] = []  # Track which agents were executed in order
    branch_decisions: Dict[str, Any] = {}  # Track decision points and outcomes


class ExecutionStatus(BaseModel):
    execution_id: str
    type: Literal["agent", "workflow", "deterministic"]
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    progress: Optional[float] = None  # 0.0 to 1.0
    current_step: Optional[str] = None
    agent_id: Optional[str] = None
    workflow_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    query: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    tools_called: List[str] = []
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    workflow_trace: Optional[WorkflowTrace] = None


class AsyncExecutionResponse(BaseModel):
    execution_id: str
    status: Literal["accepted", "queued"]
    type: Literal["agent", "workflow"]
    estimated_completion_time: Optional[datetime] = None
    status_url: str
    timestamp: datetime


class AnalyticsService:
    def __init__(self):
        self.logger = ElevaiteLogger()
        self.current_executions: Dict[str, Dict[str, Any]] = {}
        self.current_tools: Dict[str, Dict[str, Any]] = {}
        self.current_workflows: Dict[str, Dict[str, Any]] = {}

        # Enhanced execution tracking (from execution manager)
        self._live_executions: Dict[str, ExecutionStatus] = {}
        self._lock = Lock()
        self._cleanup_interval = timedelta(hours=1)

    def create_or_update_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        try:
            if db:
                existing_session = (
                    db.query(models.SessionMetrics)
                    .filter(models.SessionMetrics.session_id == session_id)
                    .first()
                )

                if not existing_session:
                    session_metrics = models.SessionMetrics(
                        session_id=session_id,
                        user_id=user_id,
                        start_time=datetime.now(),
                        is_active=True,
                    )
                    db.add(session_metrics)
                    db.commit()
                    self.logger.info(f"Created new session: {session_id}")
                else:
                    existing_session.is_active = True
                    if user_id:
                        existing_session.user_id = user_id
                    db.commit()
                    self.logger.info(f"Updated existing session: {session_id}")

        except Exception as e:
            self.logger.error(f"Error creating/updating session {session_id}: {e}")

    def _update_session_metrics_after_execution(
        self,
        session_id: str,
        agent_name: str,
        status: str,
        duration_ms: int,
        db: Optional[Session] = None,
    ) -> None:
        """Update session metrics after an agent execution completes."""
        try:
            if not db:
                return

            session = (
                db.query(models.SessionMetrics)
                .filter(models.SessionMetrics.session_id == session_id)
                .first()
            )

            if not session:
                self.logger.warning(
                    f"Session {session_id} not found for metrics update"
                )
                return

            # Update query counts
            session.total_queries += 1
            if status == "success":
                session.successful_queries += 1
            else:
                session.failed_queries += 1

            # Update agents_used dictionary and unique count
            if session.agents_used is None:
                session.agents_used = {}

            if agent_name in session.agents_used:
                session.agents_used[agent_name] += 1
            else:
                session.agents_used[agent_name] = 1
                session.unique_agents_count += 1

            # Update average response time
            if session.total_queries == 1:
                session.average_response_time_ms = duration_ms
            else:
                # Calculate running average
                current_avg = session.average_response_time_ms or 0
                session.average_response_time_ms = (
                    current_avg * (session.total_queries - 1) + duration_ms
                ) / session.total_queries

            db.commit()
            self.logger.info(f"Updated session metrics for session: {session_id}")

        except Exception as e:
            self.logger.error(f"Error updating session metrics for {session_id}: {e}")

    def start_agent_execution(
        self,
        execution_id: str,
        agent_name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        query: Optional[str] = None,
        agent_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        try:
            start_time = datetime.now()
            execution_data = {
                "execution_id": execution_id,
                "agent_name": agent_name,
                "user_id": user_id,
                "session_id": session_id,
                "query": query,
                "agent_id": agent_id,
                "start_time": start_time,
                "tool_count": 0,
            }

            self.current_executions[execution_id] = execution_data

            # Create the database record immediately so tools can reference it
            if db and agent_id:
                try:
                    # First check if the agent exists to avoid foreign key violation
                    agent_exists = (
                        db.query(models.Agent)
                        .filter(models.Agent.agent_id == agent_id)
                        .first()
                    )

                    if agent_exists:
                        metrics = models.AgentExecutionMetrics(
                            execution_id=execution_id,
                            agent_name=agent_name,
                            agent_id=agent_id,
                            start_time=start_time,
                            status="running",  # Initial status
                            query=query,
                            session_id=session_id,
                            user_id=user_id,
                            tool_count=0,
                        )
                        db.add(metrics)
                        db.commit()
                        self.logger.info(
                            f"Created initial execution record: {execution_id}"
                        )
                    else:
                        self.logger.warning(
                            f"Agent {agent_id} not found in database, skipping metrics creation"
                        )
                except Exception as db_error:
                    self.logger.error(
                        f"Failed to create initial execution record: {db_error}"
                    )
                    # Rollback the transaction to prevent session issues
                    try:
                        db.rollback()
                    except:
                        pass
                    # Continue without database record - fallback to old behavior

            self.logger.info(
                f"Started tracking execution: {execution_id} for agent: {agent_name}"
            )

        except Exception as e:
            self.logger.error(f"Error starting agent execution tracking: {e}")

    def end_agent_execution(
        self,
        execution_id: str,
        status: str,
        response: Optional[str] = None,
        tool_count: Optional[int] = None,
        db: Optional[Session] = None,
    ) -> None:
        try:
            if execution_id not in self.current_executions:
                self.logger.warning(
                    f"Execution {execution_id} not found in current executions"
                )
                return

            execution_data = self.current_executions[execution_id]
            end_time = datetime.now()
            duration_ms = int(
                (end_time - execution_data["start_time"]).total_seconds() * 1000
            )

            if db:
                # Try to update existing record first, create new one if it doesn't exist
                try:
                    existing_metrics = (
                        db.query(models.AgentExecutionMetrics)
                        .filter(
                            models.AgentExecutionMetrics.execution_id == execution_id
                        )
                        .first()
                    )

                    if existing_metrics:
                        # Update existing record
                        existing_metrics.end_time = end_time
                        existing_metrics.duration_ms = duration_ms
                        existing_metrics.status = status
                        existing_metrics.response = response
                        existing_metrics.tool_count = tool_count or execution_data.get(
                            "tool_count", 0
                        )
                        db.commit()
                        self.logger.info(
                            f"Updated existing execution record: {execution_id}"
                        )

                        # Update session metrics after successful execution record update
                        session_id = execution_data.get("session_id")
                        if session_id:
                            self._update_session_metrics_after_execution(
                                session_id=session_id,
                                agent_name=execution_data["agent_name"],
                                status=status,
                                duration_ms=duration_ms,
                                db=db,
                            )
                    else:
                        # Create new record (fallback for cases where start didn't create one)
                        agent_id = execution_data.get("agent_id")
                        if agent_id:
                            # Check if agent exists before creating record
                            agent_exists = (
                                db.query(models.Agent)
                                .filter(models.Agent.agent_id == agent_id)
                                .first()
                            )
                            if not agent_exists:
                                self.logger.warning(
                                    f"Agent {agent_id} not found, skipping metrics creation"
                                )
                                return  # Skip creating metrics for non-existent agents

                        metrics = models.AgentExecutionMetrics(
                            execution_id=execution_id,
                            agent_name=execution_data["agent_name"],
                            agent_id=agent_id,  # Guaranteed to be valid since we checked agent_exists
                            start_time=execution_data["start_time"],
                            end_time=end_time,
                            duration_ms=duration_ms,
                            status=status,
                            query=execution_data.get("query"),
                            response=response,
                            tool_count=tool_count
                            or execution_data.get("tool_count", 0),
                            session_id=execution_data.get("session_id"),
                            user_id=execution_data.get("user_id"),
                        )
                        db.add(metrics)
                        db.commit()
                        self.logger.info(
                            f"Created new execution record: {execution_id}"
                        )

                    # Update session metrics after successful execution record creation
                    session_id = execution_data.get("session_id")
                    if session_id:
                        self._update_session_metrics_after_execution(
                            session_id=session_id,
                            agent_name=execution_data["agent_name"],
                            status=status,
                            duration_ms=duration_ms,
                            db=db,
                        )

                except Exception as db_error:
                    self.logger.error(
                        f"Failed to update/create execution record: {db_error}"
                    )
                    # Rollback the transaction to prevent session issues
                    try:
                        db.rollback()
                    except:
                        pass

            del self.current_executions[execution_id]
            self.logger.info(f"Completed tracking execution: {execution_id}")

        except Exception as e:
            self.logger.error(f"Error ending agent execution tracking: {e}")

    def start_tool_usage(
        self,
        usage_id: str,
        tool_name: str,
        execution_id: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            tool_data = {
                "usage_id": usage_id,
                "tool_name": tool_name,
                "execution_id": execution_id,
                "parameters": parameters,
                "start_time": datetime.now(),
            }

            self.current_tools[usage_id] = tool_data

            if execution_id in self.current_executions:
                self.current_executions[execution_id]["tool_count"] += 1

            self.logger.info(
                f"Started tracking tool usage: {usage_id} for tool: {tool_name}"
            )

        except Exception as e:
            self.logger.error(f"Error starting tool usage tracking: {e}")

    def end_tool_usage(
        self,
        usage_id: str,
        status: str,
        result: Optional[Any] = None,
        db: Optional[Session] = None,
    ) -> None:
        try:
            if usage_id not in self.current_tools:
                self.logger.warning(f"Tool usage {usage_id} not found in current tools")
                return

            tool_data = self.current_tools[usage_id]
            end_time = datetime.now()
            duration_ms = int(
                (end_time - tool_data["start_time"]).total_seconds() * 1000
            )

            if db:
                try:
                    metrics = models.ToolUsageMetrics(
                        usage_id=usage_id,
                        tool_name=tool_data["tool_name"],
                        execution_id=tool_data["execution_id"],
                        start_time=tool_data["start_time"],
                        end_time=end_time,
                        duration_ms=duration_ms,
                        status=status,
                        input_data=tool_data.get("parameters"),
                        output_data={"result": result} if result else None,
                    )
                    db.add(metrics)
                    db.commit()
                    self.logger.info(f"Created tool usage record: {usage_id}")
                except Exception as commit_error:
                    db.rollback()
                    self.logger.error(
                        f"Failed to create tool usage record: {commit_error}"
                    )
                    # Don't raise the exception to avoid crashing the workflow

            del self.current_tools[usage_id]
            self.logger.info(f"Completed tracking tool usage: {usage_id}")

        except Exception as e:
            self.logger.error(f"Error ending tool usage tracking: {e}")

    def track_workflow_step(
        self,
        execution_id: str,
        step_type: Literal[
            # Existing AI workflow step types
            "agent_execution",
            "tool_call",
            "decision_point",
            "data_processing",
            # New deterministic workflow step types
            "data_input",
            "data_output",
            "transformation",
            "validation",
            "batch_processing",
            "conditional_branch",
            "parallel_execution",
            "aggregation",
            "notification",
        ],
        step_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        step_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Start tracking a workflow step and return step_id."""
        step_id = f"{step_type}_{step_name}_{str(uuid.uuid4())[:8]}"

        step = WorkflowStep(
            step_id=step_id,
            step_type=step_type,
            agent_id=agent_id,
            agent_name=agent_name,
            tool_name=tool_name,
            status="running",
            input_data=input_data,
            started_at=datetime.now(),
            step_metadata=step_metadata or {},
        )

        self.add_workflow_step(execution_id, step)
        self.logger.info(f"Started tracking workflow step: {step_id}")
        return step_id

    def complete_workflow_step(
        self,
        execution_id: str,
        step_id: str,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        status: Literal["completed", "failed", "skipped"] = "completed",
    ) -> bool:
        """Complete a workflow step with output data."""
        success = self.update_workflow_step(
            execution_id=execution_id,
            step_id=step_id,
            status=status,
            output_data=output_data,
            error=error,
        )

        if success:
            self.logger.info(f"Completed workflow step: {step_id} with status {status}")

        return success

    def start_workflow(
        self,
        workflow_id: str,
        workflow_type: str,
        agents_involved: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        try:
            workflow_data = {
                "workflow_id": workflow_id,
                "workflow_type": workflow_type,
                "agents_involved": agents_involved or [],
                "session_id": session_id,
                "user_id": user_id,
                "start_time": datetime.now(),
                "agent_count": len(agents_involved) if agents_involved else 0,
            }

            self.current_workflows[workflow_id] = workflow_data
            self.logger.info(
                f"Started tracking workflow: {workflow_id} of type: {workflow_type}"
            )

        except Exception as e:
            self.logger.error(f"Error starting workflow tracking: {e}")

    def end_workflow(
        self,
        workflow_id: str,
        status: str,
        db: Optional[Session] = None,
    ) -> None:
        try:
            if workflow_id not in self.current_workflows:
                self.logger.warning(
                    f"Workflow {workflow_id} not found in current workflows"
                )
                return

            workflow_data = self.current_workflows[workflow_id]
            end_time = datetime.now()
            duration_ms = int(
                (end_time - workflow_data["start_time"]).total_seconds() * 1000
            )

            if db:
                metrics = models.WorkflowMetrics(
                    workflow_id=workflow_id,
                    workflow_type=workflow_data["workflow_type"],
                    start_time=workflow_data["start_time"],
                    end_time=end_time,
                    duration_ms=duration_ms,
                    status=status,
                    agents_involved=workflow_data.get("agents_involved", []),
                    agent_count=workflow_data.get("agent_count", 0),
                    session_id=workflow_data.get("session_id"),
                    user_id=workflow_data.get("user_id"),
                )
                db.add(metrics)
                db.commit()

            del self.current_workflows[workflow_id]
            self.logger.info(f"Completed tracking workflow: {workflow_id}")

        except Exception as e:
            self.logger.error(f"Error ending workflow tracking: {e}")

    def update_tool_metrics(
        self,
        usage_id: str,
        output_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        try:
            if usage_id in self.current_tools:
                tool_data = self.current_tools[usage_id]
                if output_data:
                    tool_data["output_data"] = output_data
                self.logger.debug(f"Updated tool metrics for usage_id: {usage_id}")
            else:
                self.logger.warning(
                    f"Tool usage {usage_id} not found for metrics update"
                )

        except Exception as e:
            self.logger.error(f"Error updating tool metrics: {e}")

    def update_execution_metrics(
        self,
        execution_id: str,
        response: Optional[str] = None,
        tools_called: Optional[List[Dict[str, Any]]] = None,
        tool_count: Optional[int] = None,
        retry_count: Optional[int] = None,
        api_calls_count: Optional[int] = None,
    ) -> None:
        try:
            if execution_id in self.current_executions:
                execution_data = self.current_executions[execution_id]
                if response:
                    execution_data["response"] = response
                if tools_called:
                    execution_data["tools_called"] = tools_called
                if tool_count is not None:
                    execution_data["tool_count"] = tool_count
                if retry_count is not None:
                    execution_data["retry_count"] = retry_count
                if api_calls_count is not None:
                    execution_data["api_calls_count"] = api_calls_count

                self.logger.debug(
                    f"Updated execution metrics for execution_id: {execution_id}"
                )
            else:
                self.logger.warning(
                    f"Execution {execution_id} not found for metrics update"
                )

        except Exception as e:
            self.logger.error(f"Error updating execution metrics: {e}")

    @contextmanager
    def track_workflow(
        self,
        workflow_type: str,
        agents_involved: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ):
        workflow_id = str(uuid.uuid4())

        try:
            self.start_workflow(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                agents_involved=agents_involved,
                session_id=session_id,
                user_id=user_id,
            )

            if session_id and db:
                self.create_or_update_session(
                    session_id=session_id,
                    user_id=user_id,
                    db=db,
                )

            yield workflow_id

            self.end_workflow(
                workflow_id=workflow_id,
                status="success",
                db=db,
            )

        except Exception as e:
            self.logger.error(f"Error in workflow {workflow_id}: {e}")
            self.end_workflow(
                workflow_id=workflow_id,
                status="error",
                db=db,
            )
            raise

    @contextmanager
    def track_agent_execution(
        self,
        agent_id: str,
        agent_name: str,
        query: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
        execution_id: Optional[str] = None,  # Allow custom execution_id
    ):

        # Use provided execution_id or generate new one
        original_execution_id = execution_id
        if execution_id is None:
            execution_id = str(uuid.uuid4())
        else:
            # If execution_id is provided, use it as-is (for workflow context)
            # This allows agents to share the same execution_id as their parent workflow
            self.logger.info(
                f"Using provided execution_id {execution_id} for agent execution"
            )

        workflow_step_id = None
        parent_workflow_execution_id = None

        # Check if this agent execution is part of a workflow execution
        # This happens when original_execution_id was provided and matches a workflow execution
        is_sub_agent_in_workflow = False
        if original_execution_id:
            with self._lock:
                if original_execution_id in self._live_executions:
                    execution = self._live_executions[original_execution_id]
                    is_sub_agent_in_workflow = (
                        execution.type == "workflow"
                        and execution.workflow_trace is not None
                    )
                    parent_workflow_execution_id = original_execution_id

        # If this is a sub-agent in a workflow, create a workflow step
        if is_sub_agent_in_workflow:
            workflow_step_id = str(uuid.uuid4())  # Use proper UUID format
            agent_step = WorkflowStep(
                step_id=workflow_step_id,
                step_type="agent_execution",
                agent_id=agent_id,
                agent_name=agent_name,
                status="running",
                input_data={"query": query},
                started_at=datetime.now(),
                step_metadata={
                    "agent_execution_id": execution_id,
                    "auto_created": True,
                },
            )
            self.add_workflow_step(parent_workflow_execution_id, agent_step)
            self.logger.info(f"Auto-created workflow step for agent: {agent_name}")

        try:
            self.start_agent_execution(
                execution_id=execution_id,
                agent_name=agent_name,
                user_id=user_id,
                session_id=session_id,
                query=query,
                agent_id=agent_id,
                db=db,
            )

            # Create or update session if session_id is provided
            if session_id and db:
                self.create_or_update_session(
                    session_id=session_id,
                    user_id=user_id,
                    db=db,
                )

            yield execution_id

            # Update workflow step as completed if it was created
            if workflow_step_id and parent_workflow_execution_id:
                self.update_workflow_step(
                    parent_workflow_execution_id,
                    workflow_step_id,
                    status="completed",
                    output_data={"status": "success"},
                )

            self.end_agent_execution(
                execution_id=execution_id,
                status="success",
                db=db,
            )

        except Exception as e:
            # Update workflow step as failed if it was created
            if workflow_step_id and parent_workflow_execution_id:
                self.update_workflow_step(
                    parent_workflow_execution_id,
                    workflow_step_id,
                    status="failed",
                    error=str(e),
                )

            self.end_agent_execution(
                execution_id=execution_id,
                status="error",
                response=str(e),
                db=db,
            )
            raise

    @contextmanager
    def track_tool_usage(
        self,
        tool_name: str,
        execution_id: str,
        input_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None,
    ):
        usage_id = str(uuid.uuid4())
        workflow_step_id = None
        skip_db_tracking = False  # Flag to control database persistence

        # Check if this is happening during workflow execution
        # We need to check both the current execution_id and see if there's a parent workflow
        is_workflow_execution = False
        workflow_execution_id = None

        with self._lock:
            # First check if this execution_id is directly a workflow
            if execution_id in self._live_executions:
                execution = self._live_executions[execution_id]
                if (
                    execution.type == "workflow"
                    and execution.workflow_trace is not None
                ):
                    is_workflow_execution = True
                    workflow_execution_id = execution_id
                    self.logger.info(
                        f"Tool tracking for {tool_name}: Direct workflow execution {execution_id}"
                    )
                else:
                    self.logger.info(
                        f"Tool tracking for {tool_name}: Agent execution {execution_id}, checking for active workflows"
                    )
            else:
                self.logger.info(
                    f"Tool tracking for {tool_name}: execution_id={execution_id} not found in live executions, checking for active workflows"
                )

            # If not a direct workflow execution, check for any active workflow executions
            # Tool calls during workflow execution should be added as workflow steps
            if not is_workflow_execution:
                for live_exec_id, live_exec in self._live_executions.items():
                    if (
                        live_exec.type == "workflow"
                        and live_exec.workflow_trace is not None
                    ):
                        # Found an active workflow - associate this tool call with it
                        is_workflow_execution = True
                        workflow_execution_id = live_exec_id
                        self.logger.info(
                            f"Tool tracking for {tool_name}: Found active workflow {live_exec_id} for tool call from execution {execution_id}"
                        )
                        break

        # If this is a workflow execution, create a workflow step for the tool call
        if is_workflow_execution and workflow_execution_id:
            workflow_step_id = str(uuid.uuid4())  # Use proper UUID format
            tool_step = WorkflowStep(
                step_id=workflow_step_id,
                step_type="tool_call",
                tool_name=tool_name,
                status="running",
                input_data=input_data,
                started_at=datetime.now(),
                step_metadata={
                    "tool_usage_id": usage_id,
                    "auto_created": True,
                    "agent_execution_id": execution_id,  # Track which agent execution this came from
                },
            )
            self.add_workflow_step(workflow_execution_id, tool_step)
            self.logger.info(
                f"Auto-created workflow step for tool: {tool_name} in workflow {workflow_execution_id}"
            )

        try:
            # For tool usage database persistence, we need to use an agent execution_id
            # If this is a workflow execution, we need to find the actual agent execution_id
            tool_tracking_execution_id = execution_id

            if is_workflow_execution and workflow_execution_id:
                # This tool call is part of a workflow - we need to find the agent execution_id
                # The execution_id passed to us should already be the agent execution_id if this is called from agent context
                agent_execution_found = False

                # First, check if the current execution_id is already an agent execution_id
                # (This happens when the tool is called directly from an agent)
                if execution_id != workflow_execution_id:
                    # The execution_id is different from workflow_execution_id, so it's likely an agent execution_id
                    tool_tracking_execution_id = execution_id
                    agent_execution_found = True
                    self.logger.info(
                        f"Using current execution_id {execution_id} as agent execution_id for tool tracking"
                    )
                else:
                    # Look for the most recent agent execution step in the workflow
                    with self._lock:
                        if workflow_execution_id in self._live_executions:
                            workflow_exec = self._live_executions[workflow_execution_id]
                            if workflow_exec.workflow_trace:
                                # Find the most recent agent execution step
                                for step in reversed(
                                    workflow_exec.workflow_trace.steps
                                ):
                                    if (
                                        step.step_type == "agent_execution"
                                        and step.step_metadata
                                        and step.step_metadata.get("agent_execution_id")
                                    ):
                                        # Use the agent execution_id from the workflow step
                                        tool_tracking_execution_id = step.step_metadata[
                                            "agent_execution_id"
                                        ]
                                        agent_execution_found = True
                                        self.logger.info(
                                            f"Using agent execution {tool_tracking_execution_id} from workflow trace for tool tracking"
                                        )
                                        break

                # Fallback: Look for any agent execution that's currently active
                if not agent_execution_found:
                    with self._lock:
                        for live_exec_id, live_exec in self._live_executions.items():
                            if (
                                live_exec.type == "agent"
                                and live_exec_id != workflow_execution_id
                            ):
                                # Found an agent execution - use it for tool tracking
                                tool_tracking_execution_id = live_exec_id
                                agent_execution_found = True
                                self.logger.info(
                                    f"Using agent execution {live_exec_id} for tool tracking instead of workflow {workflow_execution_id}"
                                )
                                break

                # If no agent execution found, we cannot track tool usage safely
                # Skip tool usage tracking to avoid foreign key violation
                if not agent_execution_found:
                    self.logger.warning(
                        f"No agent execution found for workflow {workflow_execution_id} - skipping tool usage tracking to avoid foreign key violation"
                    )
                    # Set flag to skip database tracking
                    skip_db_tracking = True

            # Only track tool usage in database if we have a valid agent execution_id
            if not skip_db_tracking:
                # Ensure we have a database session - create one if needed
                db_session = db
                if db_session is None:
                    try:
                        from db.database import SessionLocal

                        db_session = SessionLocal()
                    except Exception as db_create_error:
                        self.logger.error(
                            f"Failed to create database session: {db_create_error}"
                        )
                        skip_db_tracking = True
                        db_session = None

                # Double-check that the agent execution record exists in the database
                if db_session:
                    try:
                        agent_execution_exists = (
                            db_session.query(models.AgentExecutionMetrics)
                            .filter(
                                models.AgentExecutionMetrics.execution_id
                                == tool_tracking_execution_id
                            )
                            .first()
                        )

                        if agent_execution_exists:
                            self.logger.info(
                                f"Agent execution {tool_tracking_execution_id} found in database - proceeding with tool usage tracking"
                            )
                            self.start_tool_usage(
                                usage_id=usage_id,
                                tool_name=tool_name,
                                execution_id=tool_tracking_execution_id,  # Use agent execution_id for database persistence
                                parameters=input_data,
                            )
                        else:
                            self.logger.warning(
                                f"Agent execution {tool_tracking_execution_id} not found in database - skipping tool usage tracking"
                            )
                            skip_db_tracking = True
                    except Exception as db_check_error:
                        self.logger.error(
                            f"Error checking agent execution existence: {db_check_error}"
                        )
                        skip_db_tracking = True
                else:
                    # No database session available - skip tracking
                    self.logger.warning(
                        "No database session available for tool usage tracking"
                    )
                    skip_db_tracking = True

            yield usage_id

            # Update workflow step as completed if it was created
            if workflow_step_id and workflow_execution_id:
                self.update_workflow_step(
                    workflow_execution_id,
                    workflow_step_id,
                    status="completed",
                    output_data={
                        "status": "success",
                        "skipped_db_tracking": skip_db_tracking,
                    },
                )

            # Only end tool usage tracking if we started it
            if not skip_db_tracking:
                # Use the database session we created or received
                final_db_session = db_session if "db_session" in locals() else db
                self.end_tool_usage(
                    usage_id=usage_id,
                    status="success",
                    db=final_db_session,
                )

        except Exception as e:
            # Update workflow step as failed if it was created
            if workflow_step_id and workflow_execution_id:
                self.update_workflow_step(
                    workflow_execution_id,
                    workflow_step_id,
                    status="failed",
                    error=str(e),
                )

            # Only end tool usage tracking if we started it
            if not skip_db_tracking:
                # Use the database session we created or received
                final_db_session = db_session if "db_session" in locals() else db
                self.end_tool_usage(
                    usage_id=usage_id,
                    status="error",
                    result=str(e),
                    db=final_db_session,
                )
            raise

    # === EXECUTION MANAGER CAPABILITIES ===

    def create_execution(
        self,
        execution_type: Literal["agent", "workflow", "deterministic"],
        agent_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        query: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        estimated_duration: Optional[int] = None,  # seconds
    ) -> str:
        """Create a new execution record and return the execution_id."""
        execution_id = str(uuid.uuid4())

        estimated_completion = None
        if estimated_duration:
            estimated_completion = datetime.now() + timedelta(
                seconds=estimated_duration
            )

        status = ExecutionStatus(
            execution_id=execution_id,
            type=execution_type,
            status="queued",
            agent_id=agent_id,
            workflow_id=workflow_id,
            session_id=session_id,
            user_id=user_id,
            query=query,
            input_data=input_data,
            created_at=datetime.now(),
            estimated_completion=estimated_completion,
        )

        with self._lock:
            self._live_executions[execution_id] = status

        self.logger.info(f"Created execution {execution_id} of type {execution_type}")
        return execution_id

    def get_execution(self, execution_id: str) -> Optional[ExecutionStatus]:
        """Get execution status by ID."""
        with self._lock:
            return self._live_executions.get(execution_id)

    def update_execution(
        self,
        execution_id: str,
        status: Optional[
            Literal["queued", "running", "completed", "failed", "cancelled"]
        ] = None,
        progress: Optional[float] = None,
        current_step: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        tools_called: Optional[List[str]] = None,
        db: Optional[Session] = None,
    ) -> bool:
        """Update execution status. Returns True if execution exists."""
        with self._lock:
            if execution_id not in self._live_executions:
                return False

            execution = self._live_executions[execution_id]

            if status:
                execution.status = status
                if status == "running" and not execution.started_at:
                    execution.started_at = datetime.now()
                elif (
                    status in ["completed", "failed", "cancelled"]
                    and not execution.completed_at
                ):
                    execution.completed_at = datetime.now()
                    # Persist to database when completed
                    if db:
                        self._persist_execution_to_db(execution, db)

            if progress is not None:
                execution.progress = progress

            if current_step is not None:
                execution.current_step = current_step

            if input_data is not None:
                execution.input_data = input_data

            if result is not None:
                execution.result = result

            if error is not None:
                execution.error = error

            if tools_called is not None:
                execution.tools_called = tools_called

            return True

    def add_tool_call(self, execution_id: str, tool_name: str) -> bool:
        """Add a tool call to the execution's tools_called list."""
        with self._lock:
            if execution_id not in self._live_executions:
                return False

            execution = self._live_executions[execution_id]
            if tool_name not in execution.tools_called:
                execution.tools_called.append(tool_name)

            return True

    def init_workflow_trace(
        self, execution_id: str, workflow_id: str, total_steps: int = 0
    ) -> bool:
        """Initialize workflow tracing for an execution."""
        with self._lock:
            if execution_id not in self._live_executions:
                return False

            execution = self._live_executions[execution_id]
            execution.workflow_trace = WorkflowTrace(
                execution_id=execution_id,
                workflow_id=workflow_id,
                total_steps=total_steps,
            )
            return True

    def add_workflow_step(self, execution_id: str, step: WorkflowStep) -> bool:
        """Add a workflow step to the trace."""
        with self._lock:
            if execution_id not in self._live_executions:
                return False

            execution = self._live_executions[execution_id]
            if not execution.workflow_trace:
                return False

            execution.workflow_trace.steps.append(step)
            return True

    def update_workflow_step(
        self,
        execution_id: str,
        step_id: str,
        status: Optional[
            Literal["pending", "running", "completed", "failed", "skipped"]
        ] = None,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update a specific workflow step."""
        with self._lock:
            if execution_id not in self._live_executions:
                return False

            execution = self._live_executions[execution_id]
            if not execution.workflow_trace:
                return False

            for step in execution.workflow_trace.steps:
                if step.step_id == step_id:
                    if status:
                        step.status = status
                        if status == "running" and not step.started_at:
                            step.started_at = datetime.now()
                        elif (
                            status in ["completed", "failed"] and not step.completed_at
                        ):
                            step.completed_at = datetime.now()
                            if step.started_at:
                                step.duration_ms = int(
                                    (
                                        step.completed_at - step.started_at
                                    ).total_seconds()
                                    * 1000
                                )

                    if input_data is not None:
                        step.input_data = input_data

                    if output_data is not None:
                        step.output_data = output_data

                    if error is not None:
                        step.error = error

                    return True

            return False

    def advance_workflow_step(self, execution_id: str) -> bool:
        """Advance to the next workflow step."""
        with self._lock:
            if execution_id not in self._live_executions:
                return False

            execution = self._live_executions[execution_id]
            if not execution.workflow_trace:
                return False

            execution.workflow_trace.current_step_index += 1

            # Update overall progress
            if execution.workflow_trace.total_steps > 0:
                progress = min(
                    execution.workflow_trace.current_step_index
                    / execution.workflow_trace.total_steps,
                    1.0,
                )
                execution.progress = progress

            return True

    def add_execution_path(self, execution_id: str, agent_name: str) -> bool:
        """Add an agent to the execution path."""
        with self._lock:
            if execution_id not in self._live_executions:
                return False

            execution = self._live_executions[execution_id]
            if not execution.workflow_trace:
                return False

            execution.workflow_trace.execution_path.append(agent_name)
            return True

    def add_branch_decision(
        self, execution_id: str, decision_point: str, outcome: Any
    ) -> bool:
        """Record a branching decision in the workflow."""
        with self._lock:
            if execution_id not in self._live_executions:
                return False

            execution = self._live_executions[execution_id]
            if not execution.workflow_trace:
                return False

            execution.workflow_trace.branch_decisions[decision_point] = {
                "outcome": outcome,
                "timestamp": datetime.now().isoformat(),
            }
            return True

    def list_executions(
        self,
        status: Optional[
            Literal["queued", "running", "completed", "failed", "cancelled"]
        ] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[ExecutionStatus]:
        """List executions with optional filtering."""
        with self._lock:
            executions = list(self._live_executions.values())

        # Apply filters
        if status:
            executions = [e for e in executions if e.status == status]

        if user_id:
            executions = [e for e in executions if e.user_id == user_id]

        # Sort by creation time (newest first) and limit
        executions.sort(key=lambda x: x.created_at, reverse=True)
        return executions[:limit]

    def cleanup_completed(self) -> int:
        """Remove completed executions older than cleanup_interval. Returns count removed."""
        cutoff_time = datetime.now() - self._cleanup_interval
        removed_count = 0

        with self._lock:
            to_remove = []
            for execution_id, execution in self._live_executions.items():
                if (
                    execution.status in ["completed", "failed", "cancelled"]
                    and execution.completed_at
                    and execution.completed_at < cutoff_time
                ):
                    to_remove.append(execution_id)

            for execution_id in to_remove:
                del self._live_executions[execution_id]
                removed_count += 1

        return removed_count

    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution manager statistics."""
        with self._lock:
            executions = list(self._live_executions.values())

        total = len(executions)
        by_status = {}
        by_type = {}

        for execution in executions:
            # Count by status
            status = execution.status
            by_status[status] = by_status.get(status, 0) + 1

            # Count by type
            exec_type = execution.type
            by_type[exec_type] = by_type.get(exec_type, 0) + 1

        # Count workflow executions with tracing
        workflow_with_trace = sum(
            1 for e in executions if e.type == "workflow" and e.workflow_trace
        )

        return {
            "total_executions": total,
            "by_status": by_status,
            "by_type": by_type,
            "workflow_with_trace": workflow_with_trace,
            "oldest_execution": min((e.created_at for e in executions), default=None),
            "newest_execution": max((e.created_at for e in executions), default=None),
        }

    def _persist_execution_to_db(self, execution: ExecutionStatus, db: Session) -> None:
        """Persist execution data to database when execution completes."""
        try:
            if execution.type == "workflow":
                # Create workflow metrics record with execution_id as primary key
                workflow_metrics = models.WorkflowMetrics(
                    execution_id=execution.execution_id,  # Use execution_id as primary key
                    workflow_id=execution.workflow_id,
                    workflow_type="dynamic",  # Could be enhanced to get actual type
                    start_time=execution.started_at or execution.created_at,
                    end_time=execution.completed_at,
                    duration_ms=(
                        int(
                            (
                                execution.completed_at
                                - (execution.started_at or execution.created_at)
                            ).total_seconds()
                            * 1000
                        )
                        if execution.completed_at
                        else None
                    ),
                    status="success" if execution.status == "completed" else "error",
                    agents_involved=(
                        execution.workflow_trace.execution_path
                        if execution.workflow_trace
                        else []
                    ),
                    agent_count=(
                        len(execution.workflow_trace.execution_path)
                        if execution.workflow_trace
                        else 0
                    ),
                    session_id=execution.session_id,
                    user_id=execution.user_id,
                )
                db.add(workflow_metrics)

                # Create detailed step records if workflow trace exists
                if execution.workflow_trace:
                    for step in execution.workflow_trace.steps:
                        if step.step_type == "tool_call":
                            # Check if this tool call was marked to skip database tracking
                            skip_db_tracking = (
                                step.output_data
                                and isinstance(step.output_data, dict)
                                and step.output_data.get("skipped_db_tracking", False)
                            )

                            if skip_db_tracking:
                                self.logger.info(
                                    f"Skipping database persistence for tool call {step.step_id} due to skipped_db_tracking flag"
                                )
                                continue

                            tool_metrics = models.ToolUsageMetrics(
                                usage_id=step.step_id,
                                tool_name=step.tool_name,
                                execution_id=execution.execution_id,
                                start_time=step.started_at,
                                end_time=step.completed_at,
                                duration_ms=step.duration_ms,
                                status=(
                                    "success" if step.status == "completed" else "error"
                                ),
                                input_data=step.input_data,
                                output_data=step.output_data,
                            )
                            db.add(tool_metrics)
                        elif step.step_type == "agent_execution" and step.agent_id:
                            agent_metrics = models.AgentExecutionMetrics(
                                execution_id=step.step_id,
                                agent_name=step.agent_name,
                                agent_id=step.agent_id,
                                start_time=step.started_at,
                                end_time=step.completed_at,
                                duration_ms=step.duration_ms,
                                status=(
                                    "success" if step.status == "completed" else "error"
                                ),
                                query=(
                                    step.input_data.get("query")
                                    if step.input_data
                                    else None
                                ),
                                response=(
                                    str(step.output_data) if step.output_data else None
                                ),
                                session_id=execution.session_id,
                                user_id=execution.user_id,
                            )
                            db.add(agent_metrics)

            elif execution.type == "agent":
                # Create agent execution metrics record
                agent_metrics = models.AgentExecutionMetrics(
                    execution_id=execution.execution_id,
                    agent_name="Unknown",  # Could be enhanced to get actual agent name
                    agent_id=execution.agent_id,
                    start_time=execution.started_at or execution.created_at,
                    end_time=execution.completed_at,
                    duration_ms=(
                        int(
                            (
                                execution.completed_at
                                - (execution.started_at or execution.created_at)
                            ).total_seconds()
                            * 1000
                        )
                        if execution.completed_at
                        else None
                    ),
                    status="success" if execution.status == "completed" else "error",
                    query=execution.query,
                    response=str(execution.result) if execution.result else None,
                    tool_count=len(execution.tools_called),
                    session_id=execution.session_id,
                    user_id=execution.user_id,
                )
                db.add(agent_metrics)

            db.commit()
            self.logger.info(
                f"Persisted execution {execution.execution_id} to database"
            )

        except Exception as e:
            db.rollback()
            self.logger.error(
                f"Failed to persist execution {execution.execution_id} to database: {e}"
            )


analytics_service = AnalyticsService()
