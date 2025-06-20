
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import AgentExecutionMetrics, ToolUsageMetrics, WorkflowMetrics, SessionMetrics
from ..schemas import (
    AgentExecutionMetricsCreate,
    AgentExecutionMetricsUpdate,
    ToolUsageMetricsCreate,
    ToolUsageMetricsUpdate,
    WorkflowMetricsCreate,
    WorkflowMetricsUpdate,
    SessionMetricsCreate,
    SessionMetricsUpdate,
)

def create_agent_execution_metrics(db: Session, metrics: AgentExecutionMetricsCreate) -> AgentExecutionMetrics:
    db_metrics = AgentExecutionMetrics(
        execution_id=uuid.uuid4(),
        agent_id=metrics.agent_id,
        agent_name=metrics.agent_name,
        start_time=datetime.now(),
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

def get_agent_execution_metrics(db: Session, execution_id: uuid.UUID) -> Optional[AgentExecutionMetrics]:
    return db.query(AgentExecutionMetrics).filter(AgentExecutionMetrics.execution_id == execution_id).first()

def get_agent_execution_metrics_by_agent(db: Session, agent_id: uuid.UUID, limit: int = 100) -> List[AgentExecutionMetrics]:
    return (
        db.query(AgentExecutionMetrics)
        .filter(AgentExecutionMetrics.agent_id == agent_id)
        .order_by(AgentExecutionMetrics.start_time.desc())
        .limit(limit)
        .all()
    )

def get_agent_execution_metrics_by_session(db: Session, session_id: str) -> List[AgentExecutionMetrics]:
    return (
        db.query(AgentExecutionMetrics)
        .filter(AgentExecutionMetrics.session_id == session_id)
        .order_by(AgentExecutionMetrics.start_time.desc())
        .all()
    )

def update_agent_execution_metrics(db: Session, execution_id: uuid.UUID, metrics_update: AgentExecutionMetricsUpdate) -> Optional[AgentExecutionMetrics]:
    db_metrics = get_agent_execution_metrics(db, execution_id)
    if not db_metrics:
        return None

    update_data = metrics_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metrics, key, value)

    db.commit()
    db.refresh(db_metrics)
    return db_metrics

def create_tool_usage_metrics(db: Session, metrics: ToolUsageMetricsCreate) -> ToolUsageMetrics:
    db_metrics = ToolUsageMetrics(
        usage_id=uuid.uuid4(),
        tool_name=metrics.tool_name,
        execution_id=metrics.execution_id,
        start_time=datetime.now(),
        status="in_progress",
        input_data=metrics.input_data,
        external_api_called=metrics.external_api_called,
    )
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics

def get_tool_usage_metrics(db: Session, usage_id: uuid.UUID) -> Optional[ToolUsageMetrics]:
    return db.query(ToolUsageMetrics).filter(ToolUsageMetrics.usage_id == usage_id).first()

def get_tool_usage_metrics_by_execution(db: Session, execution_id: uuid.UUID) -> List[ToolUsageMetrics]:
    return db.query(ToolUsageMetrics).filter(ToolUsageMetrics.execution_id == execution_id).all()

def get_tool_usage_metrics_by_tool(db: Session, tool_name: str, limit: int = 100) -> List[ToolUsageMetrics]:
    return (
        db.query(ToolUsageMetrics)
        .filter(ToolUsageMetrics.tool_name == tool_name)
        .order_by(ToolUsageMetrics.start_time.desc())
        .limit(limit)
        .all()
    )

def update_tool_usage_metrics(db: Session, usage_id: uuid.UUID, metrics_update: ToolUsageMetricsUpdate) -> Optional[ToolUsageMetrics]:
    db_metrics = get_tool_usage_metrics(db, usage_id)
    if not db_metrics:
        return None

    update_data = metrics_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metrics, key, value)

    db.commit()
    db.refresh(db_metrics)
    return db_metrics

def create_workflow_metrics(db: Session, metrics: WorkflowMetricsCreate) -> WorkflowMetrics:
    db_metrics = WorkflowMetrics(
        workflow_id=uuid.uuid4(),
        workflow_type=metrics.workflow_type,
        start_time=datetime.now(),
        status="in_progress",
        agents_involved=metrics.agents_involved,
        session_id=metrics.session_id,
        user_id=metrics.user_id,
    )
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics

def get_workflow_metrics(db: Session, workflow_id: uuid.UUID) -> Optional[WorkflowMetrics]:
    return db.query(WorkflowMetrics).filter(WorkflowMetrics.workflow_id == workflow_id).first()

def get_workflow_metrics_by_type(db: Session, workflow_type: str, limit: int = 100) -> List[WorkflowMetrics]:
    return (
        db.query(WorkflowMetrics)
        .filter(WorkflowMetrics.workflow_type == workflow_type)
        .order_by(WorkflowMetrics.start_time.desc())
        .limit(limit)
        .all()
    )

def update_workflow_metrics(db: Session, workflow_id: uuid.UUID, metrics_update: WorkflowMetricsUpdate) -> Optional[WorkflowMetrics]:
    db_metrics = get_workflow_metrics(db, workflow_id)
    if not db_metrics:
        return None

    update_data = metrics_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metrics, key, value)

    db.commit()
    db.refresh(db_metrics)
    return db_metrics

def create_session_metrics(db: Session, metrics: SessionMetricsCreate) -> SessionMetrics:
    db_metrics = SessionMetrics(
        session_id=metrics.session_id,
        start_time=datetime.now(),
        user_id=metrics.user_id,
        user_agent=metrics.user_agent,
        ip_address=metrics.ip_address,
    )
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics

def get_session_metrics(db: Session, session_id: str) -> Optional[SessionMetrics]:
    return db.query(SessionMetrics).filter(SessionMetrics.session_id == session_id).first()

def get_active_sessions(db: Session) -> List[SessionMetrics]:
    return db.query(SessionMetrics).filter(SessionMetrics.is_active == True).all()

def update_session_metrics(db: Session, session_id: str, metrics_update: SessionMetricsUpdate) -> Optional[SessionMetrics]:
    db_metrics = get_session_metrics(db, session_id)
    if not db_metrics:
        return None

    update_data = metrics_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_metrics, key, value)

    db.commit()
    db.refresh(db_metrics)
    return db_metrics

def get_analytics_summary(db: Session, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> dict:
    query_filter = []
    if start_date:
        query_filter.append(AgentExecutionMetrics.start_time >= start_date)
    if end_date:
        query_filter.append(AgentExecutionMetrics.start_time <= end_date)

    agent_stats = (
        db.query(
            AgentExecutionMetrics.agent_name,
            func.count(AgentExecutionMetrics.id).label("total_executions"),
            func.count(func.nullif(AgentExecutionMetrics.status == "success", False)).label("successful_executions"),
            func.avg(AgentExecutionMetrics.duration_ms).label("avg_duration_ms"),
        )
        .filter(*query_filter)
        .group_by(AgentExecutionMetrics.agent_name)
        .all()
    )

    tool_stats = (
        db.query(
            ToolUsageMetrics.tool_name,
            func.count(ToolUsageMetrics.id).label("total_calls"),
            func.count(func.nullif(ToolUsageMetrics.status == "success", False)).label("successful_calls"),
            func.avg(ToolUsageMetrics.duration_ms).label("avg_duration_ms"),
        )
        .join(AgentExecutionMetrics, ToolUsageMetrics.execution_id == AgentExecutionMetrics.execution_id)
        .filter(*query_filter)
        .group_by(ToolUsageMetrics.tool_name)
        .all()
    )

    session_stats = (
        db.query(
            func.count(SessionMetrics.id).label("total_sessions"),
            func.count(func.nullif(SessionMetrics.is_active, False)).label("active_sessions"),
            func.avg(SessionMetrics.duration_ms).label("avg_session_duration_ms"),
            func.avg(SessionMetrics.total_queries).label("avg_queries_per_session"),
        )
        .first()
    )

    return {
        "agent_stats": [dict(row._mapping) for row in agent_stats],
        "tool_stats": [dict(row._mapping) for row in tool_stats],
        "session_stats": dict(session_stats._mapping) if session_stats else {},
    }
