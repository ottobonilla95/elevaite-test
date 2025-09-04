"""
Minimal analytics service (tokens-only) for PoC
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime
import uuid as uuid_module

from sqlmodel import Session

from ..db.models import AgentExecutionMetrics, WorkflowMetrics


class AnalyticsService:
    def record_agent_execution(
        self,
        session: Session,
        *,
        execution_id: str,
        step_execution_id: Optional[str],
        agent_output: Dict[str, Any],
        status: str,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        error_message: Optional[str] = None,
        redact_response_in_analytics: bool = False,
    ) -> uuid_module.UUID:
        """Persist per-agent step analytics with tokens-only usage.

        If redact_response_in_analytics=True, the response text will not be saved to analytics.
        """
        agent_name = str(agent_output.get("agent_name") or agent_output.get("agentId") or "Agent")
        agent_id = str(agent_output.get("agent_id") or "") or None
        query = agent_output.get("query")
        response = None if redact_response_in_analytics else agent_output.get("response")

        usage = agent_output.get("usage") or {}
        tokens_in = usage.get("tokens_in") if isinstance(usage, dict) else None
        tokens_out = usage.get("tokens_out") if isinstance(usage, dict) else None
        total_tokens = usage.get("total_tokens") if isinstance(usage, dict) else None
        llm_calls = usage.get("llm_calls") if isinstance(usage, dict) else None

        model = agent_output.get("model") or {}
        model_provider = model.get("provider") if isinstance(model, dict) else None
        model_name = model.get("name") if isinstance(model, dict) else None

        start_time = started_at or datetime.utcnow()
        end_time = completed_at or datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)

        row = AgentExecutionMetrics(
            execution_id=uuid_module.UUID(execution_id),
            step_execution_id=uuid_module.UUID(step_execution_id) if step_execution_id else None,
            agent_id=agent_id,
            agent_name=agent_name,
            start_time=start_time,
            end_time=end_time,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
            query=query,
            response=str(response) if response is not None else None,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            total_tokens=total_tokens,
            llm_calls=llm_calls,
            model_provider=model_provider,
            model_name=str(model_name) if model_name is not None else None,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id

    def record_workflow_metrics(
        self,
        session: Session,
        *,
        execution_id: str,
        workflow_id: str,
        workflow_name: Optional[str],
        summary: Dict[str, Any],
        totals: Dict[str, int],
        status: str,
        started_at: Optional[datetime],
        completed_at: Optional[datetime],
    ) -> uuid_module.UUID:
        start_time = started_at or datetime.utcnow()
        end_time = completed_at or datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000) if started_at and completed_at else None

        row = WorkflowMetrics(
            execution_id=uuid_module.UUID(execution_id),
            workflow_id=uuid_module.UUID(workflow_id),
            workflow_name=workflow_name,
            start_time=start_time if started_at else None,
            end_time=end_time if completed_at else None,
            duration_ms=duration_ms,
            status=status,
            total_steps=summary.get("total_steps"),
            completed_steps=summary.get("completed_steps"),
            failed_steps=summary.get("failed_steps"),
            total_tokens_in=totals.get("tokens_in"),
            total_tokens_out=totals.get("tokens_out"),
            total_tokens=totals.get("total_tokens"),
            total_llm_calls=totals.get("llm_calls"),
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id


analytics_service = AnalyticsService()
