# Shared observability constants for consistent labeling across spans and metrics

# Component identifiers
COMPONENT_AGENT_STUDIO = "agent_studio"
COMPONENT_WORKFLOW_ENGINE = "workflow_engine"
COMPONENT_STEP_REGISTRY = "step_registry"

# Status values
STATUS_STARTED = "started"
STATUS_COMPLETED = "completed"
STATUS_SUCCESS = "success"
STATUS_FAILED = "failed"
STATUS_ERROR = "error"

# Attribute/label keys
ATTR_COMPONENT = "component"
ATTR_STATUS = "status"
ATTR_WORKFLOW_TYPE = "workflow.type"
ATTR_WORKFLOW_ID = "workflow.id"
ATTR_EXECUTION_ID = "execution.id"
ATTR_AGENT_NAME = "agent.name"
ATTR_AGENT_ID = "agent.id"
ATTR_TOOL_NAME = "tool.name"
ATTR_STEP_ID = "step.id"
ATTR_STEP_TYPE = "step.type"
ATTR_SESSION_ID = "session.id"
ATTR_USER_ID = "user.id"

# Metric names
METRIC_WORKFLOW_EXECUTIONS_TOTAL = "workflow_executions_total"
METRIC_WORKFLOW_EXECUTION_DURATION = "workflow_execution_duration_seconds"
METRIC_AGENT_EXECUTIONS_TOTAL = "agent_executions_total"
METRIC_AGENT_EXECUTION_DURATION = "agent_execution_duration_seconds"
METRIC_TOOL_CALLS_TOTAL = "tool_calls_total"
METRIC_TOOL_CALL_DURATION = "tool_call_duration_seconds"

# Span names
SPAN_WORKFLOW_EXECUTION = "workflow_execution"
SPAN_AGENT_EXECUTION = "agent_execution"
SPAN_TOOL_CALL = "tool_call"
SPAN_STEP_EXECUTION = "step_execution"


# Helper functions for consistent attribute building
def build_workflow_attributes(
    workflow_type: str,
    workflow_id: str,
    component: str,
    session_id: str = "",
    user_id: str = "",
) -> dict:
    """Build consistent workflow span/metric attributes"""
    return {
        ATTR_WORKFLOW_TYPE: workflow_type,
        ATTR_WORKFLOW_ID: workflow_id,
        ATTR_COMPONENT: component,
        ATTR_SESSION_ID: session_id,
        ATTR_USER_ID: user_id,
    }


def build_agent_attributes(
    agent_name: str,
    agent_id: str,
    execution_id: str,
    component: str,
    session_id: str = "",
    user_id: str = "",
) -> dict:
    """Build consistent agent span/metric attributes"""
    return {
        ATTR_AGENT_NAME: agent_name,
        ATTR_AGENT_ID: agent_id,
        ATTR_EXECUTION_ID: execution_id,
        ATTR_COMPONENT: component,
        ATTR_SESSION_ID: session_id,
        ATTR_USER_ID: user_id,
    }


def build_tool_attributes(tool_name: str, execution_id: str, component: str) -> dict:
    """Build consistent tool span/metric attributes"""
    return {
        ATTR_TOOL_NAME: tool_name,
        ATTR_EXECUTION_ID: execution_id,
        ATTR_COMPONENT: component,
    }


def build_step_attributes(
    step_id: str, step_type: str, execution_id: str, component: str
) -> dict:
    """Build consistent step span/metric attributes"""
    return {
        ATTR_STEP_ID: step_id,
        ATTR_STEP_TYPE: step_type,
        ATTR_EXECUTION_ID: execution_id,
        ATTR_COMPONENT: component,
    }


def build_metric_labels(base_attrs: dict, status: str = "") -> dict:
    """Build metric labels from span attributes, optionally adding status"""
    labels = base_attrs.copy()
    if status:
        labels[ATTR_STATUS] = status
    return labels
