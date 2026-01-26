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


class InputKindEnum(str, Enum):
    """Input node kinds - determines how the input is activated.

    Trigger kinds (external activation):
    - webhook: Activated by HTTP POST to registered path
    - schedule: Activated by cron/interval
    - gmail: Activated by Gmail event listener
    - slack: Activated by Slack event listener

    Manual kinds (user-provided):
    - chat: User provides via chat interface
    - manual: User provides via canvas UI or API
    - form: User provides via structured form
    """

    # Trigger kinds (external activation)
    webhook = "webhook"
    schedule = "schedule"
    gmail = "gmail"
    slack = "slack"

    # Manual kinds (user-provided)
    chat = "chat"
    manual = "manual"
    form = "form"


class MergeModeEnum(str, Enum):
    """Merge node modes - determines when the merge completes.

    - first_available: Completes when ANY dependency completes (OR logic)
    - wait_all: Waits for ALL dependencies to complete (AND logic, then combines)
    """

    first_available = "first_available"
    wait_all = "wait_all"


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
    parameter_overrides: Dict[str, Any] = Field(
        default_factory=dict
    )  # Override specific parameter titles/descriptions


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

    # Execution control fields
    critical: bool = Field(
        default=True, description="If True, step failure fails the entire workflow"
    )
    timeout_seconds: Optional[int] = Field(
        default=None, description="Maximum execution time for this step"
    )

    # Retry configuration
    max_retries: int = Field(default=3, description="Maximum number of retry attempts")
    retry_strategy: str = Field(
        default="exponential_backoff",
        description="Retry strategy: none, fixed_delay, exponential_backoff, linear_backoff",
    )
    retry_delay_seconds: float = Field(
        default=1.0, description="Initial delay between retries"
    )
    max_retry_delay_seconds: float = Field(
        default=60.0, description="Maximum delay between retries"
    )

    # Conditional execution
    conditions: Optional[Union[str, Dict[str, Any], List[Any]]] = Field(
        default=None, description="Conditions that must be met for this step to execute"
    )

    # UI metadata for visual workflow editor
    position: Optional[UIPosition] = None

    # Tool-specific overrides (for tool steps)
    tool_override: Optional[ToolOverride] = None


class TriggerStepConfig(StepBase):
    step_type: Literal["trigger"] = "trigger"
    parameters: TriggerParameters


class InputStepParameters(BaseModel):
    """Parameters for input node steps.

    Input nodes are entry points that receive data. They can be:
    - Externally triggered (webhook, schedule, gmail, slack)
    - Manually provided (chat, manual, form)
    """

    kind: InputKindEnum = InputKindEnum.manual

    # Schedule configuration (for schedule kind)
    schedule: Optional[CronSchedule] = None

    # Webhook configuration (for webhook kind)
    webhook_path: Optional[str] = None  # Custom webhook path

    # Schema for validating input data
    schema: Optional[Dict[str, Any]] = None

    # Chat/form constraints
    need_history: bool = True
    allowed_modalities: Optional[List[str]] = None
    allowed_mime_types: Optional[List[str]] = None
    max_files: int = 10
    per_file_size_mb: int = 20
    total_size_mb: int = 60


class InputStepConfig(StepBase):
    """Input node step configuration.

    Input nodes are data entry points with no execution logic.
    They complete when data is provided (via trigger event or manual input).
    Input nodes must have no dependencies.
    """

    step_type: Literal["input"] = "input"
    parameters: InputStepParameters = Field(default_factory=InputStepParameters)


class MergeStepParameters(BaseModel):
    """Parameters for merge node steps."""

    mode: MergeModeEnum = MergeModeEnum.first_available

    # For wait_all mode: how to combine outputs
    # - "object": Combine as {step_id: output, ...}
    # - "array": Combine as [output1, output2, ...]
    # - "first": Just use the first completed (same as first_available)
    combine_mode: Literal["object", "array", "first"] = "object"


class MergeStepConfig(StepBase):
    """Merge node step configuration.

    Merge nodes combine multiple inputs with OR or AND logic.
    - first_available: Completes when ANY dependency completes
    - wait_all: Waits for ALL dependencies to complete

    Merge nodes must have 2+ dependencies.
    """

    step_type: Literal["merge"] = "merge"
    parameters: MergeStepParameters = Field(default_factory=MergeStepParameters)


class PromptVariable(BaseModel):
    """Definition of a variable that can be used in prompts."""

    name: str = Field(..., description="Variable name (used as {{name}} in prompt)")
    description: Optional[str] = Field(None, description="Description of the variable")
    default_value: Optional[str] = Field(
        None, description="Default value if not provided"
    )
    required: bool = Field(
        default=False, description="Whether the variable is required"
    )
    source: Optional[str] = Field(
        None,
        description="Source for the variable value (e.g., 'step_id.field', 'input.message')",
    )


class PromptStepParameters(BaseModel):
    """Parameters for prompt node steps.

    Prompt nodes provide prompt configuration for connected Agent steps.
    They support variable injection using {{variable_name}} syntax.
    """

    # The prompt template with optional {{variable}} placeholders
    system_prompt: Optional[str] = Field(
        None,
        description="System prompt template for the agent. Supports {{variable}} syntax.",
    )

    # User query template
    query_template: Optional[str] = Field(
        None,
        description="Query template for the agent. Supports {{variable}} syntax.",
    )

    # Variable definitions for the prompt
    variables: List[PromptVariable] = Field(
        default_factory=list,
        description="Variable definitions for the prompt template",
    )

    # Whether to override the agent's existing prompt or merge with it
    override_agent_prompt: bool = Field(
        default=True,
        description="If True, replace agent's prompt. If False, append to it.",
    )

    # Model configuration overrides
    provider: Optional[str] = Field(
        None,
        description="Override provider type for the agent (e.g., openai_textgen, gemini, bedrock)",
    )
    model_name: Optional[str] = Field(
        None, description="Override model name for the agent"
    )
    temperature: Optional[float] = Field(
        None, description="Override temperature setting"
    )
    max_tokens: Optional[int] = Field(None, description="Override max tokens setting")


class PromptStepConfig(StepBase):
    """Prompt node step configuration.

    Prompt nodes provide prompt configuration for connected Agent steps.
    They act like input nodes but specifically for prompt configuration.

    Features:
    - Define system prompts and query templates
    - Support {{variable}} syntax for runtime value injection
    - Override or extend agent prompt configuration
    - Pass model configuration overrides

    The Prompt step outputs its configuration which is consumed by
    connected Agent steps to configure their prompts.
    """

    step_type: Literal["prompt"] = "prompt"
    parameters: PromptStepParameters = Field(default_factory=PromptStepParameters)


StepConfig = Union[
    TriggerStepConfig, InputStepConfig, MergeStepConfig, PromptStepConfig, StepBase
]


class WorkflowConfig(BaseModel):
    workflow_id: Optional[str] = None
    name: str = "Unnamed Workflow"
    description: Optional[str] = None
    version: Optional[str] = "1.0.0"
    steps: List[StepConfig] = Field(default_factory=list)
    global_config: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    timeout_seconds: Optional[int] = None
    created_by: Optional[str] = None

    # UI metadata for visual workflow editor
    connections: List[StepConnection] = Field(
        default_factory=list,
        description="Visual connections between steps for UI rendering",
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowConfig":
        """Create WorkflowConfig from a dictionary, handling both raw dicts and model instances."""
        if isinstance(data, cls):
            return data
        return cls.model_validate(data)

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
                        {
                            "step_type": "agent",
                            "name": "TimeAgent",
                            "parameters": {"agent_name": "Time Agent"},
                        },
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
