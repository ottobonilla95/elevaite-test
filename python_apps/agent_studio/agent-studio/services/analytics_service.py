from datetime import datetime
from typing import Dict, Optional, Any
from sqlalchemy.orm import Session

from fastapi_logger import ElevaiteLogger
from db import models


class AnalyticsService:
    def __init__(self):
        self.logger = ElevaiteLogger()
        self.current_executions: Dict[str, Dict[str, Any]] = {}
        self.current_tools: Dict[str, Dict[str, Any]] = {}

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
    ) -> None:
        try:
            execution_data = {
                "execution_id": execution_id,
                "agent_name": agent_name,
                "user_id": user_id,
                "session_id": session_id,
                "query": query,
                "start_time": datetime.now(),
                "tool_count": 0,
            }

            self.current_executions[execution_id] = execution_data
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
                metrics = models.AgentExecutionMetrics(
                    execution_id=execution_id,
                    agent_name=execution_data["agent_name"],
                    start_time=execution_data["start_time"],
                    end_time=end_time,
                    duration_ms=duration_ms,
                    status=status,
                    query=execution_data.get("query"),
                    response=response,
                    tool_count=tool_count or execution_data.get("tool_count", 0),
                    session_id=execution_data.get("session_id"),
                    user_id=execution_data.get("user_id"),
                )
                db.add(metrics)
                db.commit()

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

            del self.current_tools[usage_id]
            self.logger.info(f"Completed tracking tool usage: {usage_id}")

        except Exception as e:
            self.logger.error(f"Error ending tool usage tracking: {e}")


analytics_service = AnalyticsService()
