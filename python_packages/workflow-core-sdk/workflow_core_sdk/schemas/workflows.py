from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


# -------- Enums --------


class ScheduleMode(str, Enum):
    cron = "cron"
    interval = "interval"


class BackendEnum(str, Enum):
    dbos = "dbos"
    local = "local"


class TriggerKindEnum(str, Enum):
    webhook = "webhook"
    chat = "chat"
    file = "file"


# -------- Workflow Configuration Schemas (for creation/edit) --------


class CronSchedule(BaseModel):
    """Schedule configuration for trigger step.

    Notes about seconds field:
    - If using a 6-field cron with seconds at the end (default croniter): "* * * * * */10" for every 10 seconds
    - If using seconds at the beginning (Quartz style): set seconds_at_beginning=True and use "*/10 * * * * *"
    """

    enabled: bool = True
    mode: ScheduleMode = ScheduleMode.cron

    # Cron expression. For interval mode, leave cron None and set interval_seconds.
    cron: Optional[str] = None

    # When True, interpret 6-field crons with seconds as the FIRST field (Quartz-style)
    seconds_at_beginning: Optional[bool] = False

    # For interval mode
    interval_seconds: Optional[int] = None

    # Common options
    timezone: str = "UTC"
    backend: BackendEnum = BackendEnum.dbos
    jitter_seconds: int = 0


class TriggerParameters(BaseModel):
    """Parameters for the required trigger step.

    - kind: webhook | chat | file
    - schedule: optional schedule config
    - For chat, you can further constrain attachments by type/size
    """

    kind: TriggerKindEnum = TriggerKindEnum.webhook
    schedule: Optional[CronSchedule] = None

    # Chat/file constraints and options
    need_history: bool = True
    allowed_modalities: Optional[List[str]] = None  # e.g., ["text", "image", "audio"]
    allowed_mime_types: Optional[List[str]] = None
    max_files: int = 10
    per_file_size_mb: int = 20
    total_size_mb: int = 60


class UIPosition(BaseModel):
    """UI canvas position for visual workflow editor"""

    x: float
    y: float


class StepConnection(BaseModel):
    """Connection/edge between steps for UI visualization"""

    source_step_id: str
    target_step_id: str
    source_handle: Optional[str] = None  # For multi-output steps
    target_handle: Optional[str] = None  # For multi-input steps
    connection_type: Optional[str] = "default"  # default, conditional, error, etc.
    label: Optional[str] = None
    animated: bool = False


class ToolOverride(BaseModel):
    """Workflow-specific overrides for tool configuration"""

    title: Optional[str] = None  # Override tool title for this workflow
    description: Optional[str] = None  # Override tool description for this workflow
    parameter_overrides: Dict[str, Any] = Field(default_factory=dict)  # Override specific parameter titles/descriptions


class StepBase(BaseModel):
    # Preserve caller-provided IDs and graph structure; do not drop these
    step_id: Optional[str] = None
    step_type: str
    name: Optional[str] = None
    dependencies: List[str] = Field(default_factory=list)
    # Allow mapping of prior step outputs into this step's inputs
    input_mapping: Dict[str, Any] = Field(default_factory=dict)
    # Support both 'parameters' (trigger) and 'config' (execution steps)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)

    # UI metadata for visual workflow editor
    position: Optional[UIPosition] = None

    # Tool-specific overrides (for tool steps)
    tool_override: Optional[ToolOverride] = None


class TriggerStepConfig(StepBase):
    step_type: Literal["trigger"] = "trigger"
    parameters: TriggerParameters


StepConfig = Union[TriggerStepConfig, StepBase]


class WorkflowConfig(BaseModel):
    name: str
    description: Optional[str] = None
    version: Optional[str] = "1.0.0"
    steps: List[StepConfig]
    global_config: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    timeout_seconds: Optional[int] = None
    created_by: Optional[str] = None

    # UI metadata for visual workflow editor
    connections: List[StepConnection] = Field(
        default_factory=list, description="Visual connections between steps for UI rendering"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Time Agent (Every 10 Seconds)",
                    "description": "Demo workflow that prints time on a schedule",
                    "steps": [
                        {
                            "step_type": "trigger",
                            "parameters": {
                                "kind": "webhook",
                                "schedule": {
                                    "enabled": True,
                                    "mode": "cron",
                                    "cron": "* * * * * */10",
                                    "timezone": "UTC",
                                    "backend": "dbos",
                                    "jitter_seconds": 0,
                                },
                            },
                        },
                        {"step_type": "agent", "name": "TimeAgent", "parameters": {"agent_name": "Time Agent"}},
                    ],
                    "tags": ["demo"],
                }
            ]
        }
    }


# -------- Execution Request Schemas (for /execute) --------


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class Attachment(BaseModel):
    name: Optional[str] = None
    mime: str
    size_bytes: Optional[int] = None
    path: Optional[str] = None
    data_url: Optional[str] = None


class ChatTriggerPayload(BaseModel):
    kind: Literal["chat"] = "chat"
    current_message: Optional[str] = None
    history: List[ChatMessage] = Field(default_factory=list)
    messages: Optional[List[ChatMessage]] = None
    attachments: List[Attachment] = Field(default_factory=list)
    need_history: Optional[bool] = True


class FileTriggerPayload(BaseModel):
    kind: Literal["file"] = "file"
    attachments: List[Attachment] = Field(default_factory=list)


class WebhookTriggerPayload(BaseModel):
    kind: Literal["webhook"] = "webhook"
    data: Dict[str, Any] = Field(default_factory=dict)


TriggerPayload = Union[ChatTriggerPayload, FileTriggerPayload, WebhookTriggerPayload]


class ExecutionRequest(BaseModel):
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    organization_id: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    trigger: Optional[TriggerPayload] = None
    execution_backend: Optional[BackendEnum] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Webhook execution",
                    "value": {
                        "user_id": "user-123",
                        "session_id": "sess-1",
                        "input_data": {"foo": "bar"},
                        "metadata": {"source": "test"},
                        "trigger": {"kind": "webhook", "data": {"event": "ping"}},
                    },
                },
                {
                    "summary": "Chat execution",
                    "value": {
                        "user_id": "user-123",
                        "trigger": {
                            "kind": "chat",
                            "current_message": "Hello!",
                            "history": [{"role": "user", "content": "Hi"}],
                            "attachments": [],
                        },
                    },
                },
            ]
        }
    }
