from datetime import datetime
from typing import Dict, Optional, Any, List
from contextlib import contextmanager
import uuid
from sqlalchemy.orm import Session

from fastapi_logger import ElevaiteLogger
from db import models


class AnalyticsService:
    def __init__(self):
        self.logger = ElevaiteLogger()
        self.current_executions: Dict[str, Dict[str, Any]] = {}
        self.current_tools: Dict[str, Dict[str, Any]] = {}
        self.current_workflows: Dict[str, Dict[str, Any]] = {}

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
                except Exception as db_error:
                    self.logger.error(
                        f"Failed to create initial execution record: {db_error}"
                    )
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
                    else:
                        # Create new record (fallback for cases where start didn't create one)
                        metrics = models.AgentExecutionMetrics(
                            execution_id=execution_id,
                            agent_name=execution_data["agent_name"],
                            agent_id=execution_data.get("agent_id"),
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
                except Exception as db_error:
                    self.logger.error(
                        f"Failed to update/create execution record: {db_error}"
                    )

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
        db: Optional[Session] = None,
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
        db: Optional[Session] = None,
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
        correlation_id: Optional[str] = None,
        db: Optional[Session] = None,
    ):
        execution_id = str(uuid.uuid4())

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

            yield execution_id

            self.end_agent_execution(
                execution_id=execution_id,
                status="success",
                db=db,
            )

        except Exception as e:
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
        external_api_called: Optional[str] = None,
        db: Optional[Session] = None,
    ):
        usage_id = str(uuid.uuid4())

        try:
            self.start_tool_usage(
                usage_id=usage_id,
                tool_name=tool_name,
                execution_id=execution_id,
                parameters=input_data,
            )

            yield usage_id

            self.end_tool_usage(
                usage_id=usage_id,
                status="success",
                db=db,
            )

        except Exception as e:
            self.end_tool_usage(
                usage_id=usage_id,
                status="error",
                result=str(e),
                db=db,
            )
            raise


analytics_service = AnalyticsService()
