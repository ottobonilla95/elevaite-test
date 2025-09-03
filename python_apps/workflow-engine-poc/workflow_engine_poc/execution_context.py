"""
Unified Workflow Execution Context

The execution context is the heart of the workflow engine. It:
- Holds the complete workflow configuration
- Manages step input/output data flow
- Tracks all analytics and logging IDs
- Provides a clean interface for step execution
- Supports conditional, sequential, and parallel execution patterns
"""

import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

if TYPE_CHECKING:
    from .workflow_engine import WorkflowEngine


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepResult:
    """Result of a step execution"""

    step_id: str
    status: StepStatus
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    retry_count: int = 0


@dataclass
class AnalyticsIds:
    """Container for all analytics and logging IDs"""

    execution_id: str
    workflow_execution_id: Optional[str] = None
    agent_execution_id: Optional[str] = None
    step_execution_ids: Dict[str, str] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None


@dataclass
class UserContext:
    """User and session context"""

    user_id: Optional[str] = None
    session_id: Optional[str] = None
    organization_id: Optional[str] = None
    permissions: List[str] = field(default_factory=list)


class ExecutionContext:
    """
    Unified execution context for workflow execution.

    This class manages the complete state of a workflow execution,
    providing a clean interface for step execution and data flow.
    """

    def __init__(
        self,
        workflow_config: Dict[str, Any],
        user_context: Optional[UserContext] = None,
        execution_id: Optional[str] = None,
        workflow_engine: Optional["WorkflowEngine"] = None,
    ):
        # Core identifiers
        self.execution_id = execution_id or str(uuid.uuid4())
        self.workflow_id = workflow_config.get("workflow_id", str(uuid.uuid4()))

        # Workflow configuration (immutable snapshot)
        self.workflow_config = workflow_config.copy()
        self.workflow_name = workflow_config.get("name", "Unnamed Workflow")

        # Normalize steps to ensure each has a unique step_id
        raw_steps = list(self.workflow_config.get("steps", []) or [])
        self.workflow_config["steps"] = self._normalize_steps(raw_steps)

        # Execution state
        self.status = ExecutionStatus.PENDING
        self.current_step: Optional[str] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None

        # Step management
        self.steps_config = self.workflow_config.get("steps", [])
        self.step_results: Dict[str, StepResult] = {}
        self.completed_steps: Set[str] = set()
        self.failed_steps: Set[str] = set()
        self.pending_steps: Set[str] = {step["step_id"] for step in self.steps_config}

        # Data flow between steps
        self.step_io_data: Dict[str, Any] = {}
        self.global_variables: Dict[str, Any] = {}

        # Analytics and logging
        self.analytics_ids = AnalyticsIds(execution_id=self.execution_id)
        self.user_context = user_context or UserContext()

        # Execution metadata
        self.metadata: Dict[str, Any] = {
            "created_at": datetime.now().isoformat(),
            "engine_version": "1.0.0-poc",
        }

        # Reference to workflow engine for subflow execution
        self.workflow_engine = workflow_engine

        # Build dependency graph
        self.dependency_graph = self._build_dependency_graph()

    def _normalize_steps(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Ensure each step has a unique step_id. If missing, infer a reasonable default.
        - Trigger step: defaults to 'trigger'
        - Else: slugified name or fall back to step_type_{idx}
        - Ensure uniqueness by appending numeric suffixes if needed
        """

        def slugify(txt: str) -> str:
            s = (txt or "").strip().lower()
            import re

            s = re.sub(r"[^a-z0-9]+", "_", s)
            s = re.sub(r"_+", "_", s).strip("_")
            return s or "step"

        used: Set[str] = set()
        normalized: List[Dict[str, Any]] = []
        for idx, step in enumerate(steps):
            stype = step.get("step_type") or "step"
            sid = step.get("step_id")
            if not sid:
                if stype == "trigger":
                    candidate = "trigger"
                else:
                    candidate = slugify(step.get("name") or f"{stype}_{idx + 1}")
                # Ensure unique
                base = candidate
                n = 2
                while candidate in used:
                    candidate = f"{base}_{n}"
                    n += 1
                sid = candidate
                step = {**step, "step_id": sid}
            used.add(sid)
            normalized.append(step)
        return normalized

    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph from step configurations"""
        graph = {}
        for step in self.steps_config:
            step_id = step["step_id"]
            dependencies = step.get("dependencies", [])
            graph[step_id] = dependencies
        return graph

    def start_execution(self) -> None:
        """Mark execution as started"""
        self.status = ExecutionStatus.RUNNING
        self.started_at = datetime.now()
        self.metadata["started_at"] = self.started_at.isoformat()

    def complete_execution(self) -> None:
        """Mark execution as completed"""
        self.status = ExecutionStatus.COMPLETED
        self.completed_at = datetime.now()
        self.metadata["completed_at"] = self.completed_at.isoformat()
        if self.started_at:
            self.metadata["duration_ms"] = int((self.completed_at - self.started_at).total_seconds() * 1000)

    def fail_execution(self, error_message: str) -> None:
        """Mark execution as failed"""
        self.status = ExecutionStatus.FAILED
        self.completed_at = datetime.now()
        self.metadata["failed_at"] = self.completed_at.isoformat()
        self.metadata["error_message"] = error_message
        if self.started_at:
            if self.started_at:
                self.metadata["duration_ms"] = int((self.completed_at - self.started_at).total_seconds() * 1000)

    def get_step_config(self, step_id: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific step"""
        for step in self.steps_config:
            if step["step_id"] == step_id:
                return step
        return None

    def get_step_input_data(self, step_id: str) -> Dict[str, Any]:
        """
        Collect input data for a step based on its input_mapping configuration.

        This handles the data flow between steps by mapping outputs from
        previous steps to inputs for the current step.
        """
        step_config = self.get_step_config(step_id)
        if not step_config:
            return {}

        input_mapping = step_config.get("input_mapping", {})
        input_data = {}

        # Process input mappings
        for input_key, source_spec in input_mapping.items():
            if isinstance(source_spec, str) and "." in source_spec:
                # Format: "step_id.field_name"
                source_step_id, field_name = source_spec.split(".", 1)
                if source_step_id in self.step_io_data:
                    source_data = self.step_io_data[source_step_id]
                    if isinstance(source_data, dict) and field_name in source_data:
                        input_data[input_key] = source_data[field_name]
                    else:
                        # If field doesn't exist, use the whole source data
                        input_data[input_key] = source_data
            elif isinstance(source_spec, str) and source_spec in self.step_io_data:
                # Direct step reference
                input_data[input_key] = self.step_io_data[source_spec]
            elif isinstance(source_spec, str) and source_spec in self.global_variables:
                # Global variable reference
                input_data[input_key] = self.global_variables[source_spec]

        # Add any direct input_data from step config
        if "input_data" in step_config:
            input_data.update(step_config["input_data"])

        return input_data

    def store_step_result(self, step_result: StepResult) -> None:
        """Store the result of a step execution"""
        step_id = step_result.step_id

        # Store the result
        self.step_results[step_id] = step_result

        # Update step tracking
        if step_result.status == StepStatus.COMPLETED:
            self.completed_steps.add(step_id)
            self.pending_steps.discard(step_id)
            # Store output data for future steps
            if step_result.output_data:
                self.step_io_data[step_id] = step_result.output_data
        elif step_result.status == StepStatus.FAILED:
            self.failed_steps.add(step_id)
            self.pending_steps.discard(step_id)
            # Store output data for failed steps as well (for error analysis and subflow results)
            if step_result.output_data:
                self.step_io_data[step_id] = step_result.output_data

        # Update current step tracking
        if self.current_step == step_id:
            self.current_step = None

    def can_execute_step(self, step_id: str) -> bool:
        """Check if a step can be executed (all dependencies satisfied)"""
        if step_id in self.completed_steps or step_id in self.failed_steps:
            return False

        dependencies = self.dependency_graph.get(step_id, [])
        return all(dep in self.completed_steps for dep in dependencies)

    def get_ready_steps(self) -> List[str]:
        """Get list of steps that are ready to execute"""
        return [step_id for step_id in self.pending_steps if self.can_execute_step(step_id)]

    def is_execution_complete(self) -> bool:
        """Check if the workflow execution is complete"""
        return len(self.pending_steps) == 0 or self.status in [
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
            ExecutionStatus.CANCELLED,
        ]

    def skip_step(self, step_id: str, reason: str = "Conditions not met"):
        """Mark a step as skipped"""
        self.step_results[step_id] = StepResult(
            step_id=step_id,
            status=StepStatus.SKIPPED,
            error_message=reason,
        )

        # Update step tracking
        self.pending_steps.discard(step_id)
        # Note: skipped steps are not added to completed_steps or failed_steps

        # Update current step tracking
        if self.current_step == step_id:
            self.current_step = None

    def get_execution_summary(self) -> Dict[str, Any]:
        """Get a summary of the execution state"""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "current_step": self.current_step,
            "completed_steps": len(self.completed_steps),
            "failed_steps": len(self.failed_steps),
            "pending_steps": len(self.pending_steps),
            "total_steps": len(self.steps_config),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (self.completed_at.isoformat() if self.completed_at else None),
            "analytics_ids": {
                "execution_id": self.analytics_ids.execution_id,
                "correlation_id": self.analytics_ids.correlation_id,
                "trace_id": self.analytics_ids.trace_id,
            },
            "user_context": {
                "user_id": self.user_context.user_id,
                "session_id": self.user_context.session_id,
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize execution context to dictionary for storage"""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workflow_config": self.workflow_config,
            "status": self.status.value,
            "current_step": self.current_step,
            "step_io_data": self.step_io_data,
            "global_variables": self.global_variables,
            "completed_steps": list(self.completed_steps),
            "failed_steps": list(self.failed_steps),
            "pending_steps": list(self.pending_steps),
            "analytics_ids": {
                "execution_id": self.analytics_ids.execution_id,
                "workflow_execution_id": self.analytics_ids.workflow_execution_id,
                "agent_execution_id": self.analytics_ids.agent_execution_id,
                "step_execution_ids": self.analytics_ids.step_execution_ids,
                "correlation_id": self.analytics_ids.correlation_id,
                "trace_id": self.analytics_ids.trace_id,
            },
            "user_context": {
                "user_id": self.user_context.user_id,
                "session_id": self.user_context.session_id,
                "organization_id": self.user_context.organization_id,
                "permissions": self.user_context.permissions,
            },
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionContext":
        """Deserialize execution context from dictionary"""
        # Reconstruct user context
        user_context_data = data.get("user_context", {})
        user_context = UserContext(
            user_id=user_context_data.get("user_id"),
            session_id=user_context_data.get("session_id"),
            organization_id=user_context_data.get("organization_id"),
            permissions=user_context_data.get("permissions", []),
        )

        # Create execution context
        context = cls(
            workflow_config=data["workflow_config"],
            user_context=user_context,
            execution_id=data["execution_id"],
        )

        # Restore state
        context.status = ExecutionStatus(data["status"])
        context.current_step = data.get("current_step")
        context.step_io_data = data.get("step_io_data", {})
        context.global_variables = data.get("global_variables", {})
        context.completed_steps = set(data.get("completed_steps", []))
        context.failed_steps = set(data.get("failed_steps", []))
        context.pending_steps = set(data.get("pending_steps", []))
        context.metadata = data.get("metadata", {})

        # Restore analytics IDs
        analytics_data = data.get("analytics_ids", {})
        context.analytics_ids = AnalyticsIds(
            execution_id=analytics_data.get("execution_id", context.execution_id),
            workflow_execution_id=analytics_data.get("workflow_execution_id"),
            agent_execution_id=analytics_data.get("agent_execution_id"),
            step_execution_ids=analytics_data.get("step_execution_ids", {}),
            correlation_id=analytics_data.get("correlation_id"),
            trace_id=analytics_data.get("trace_id"),
        )

        return context
