from enum import Enum


class PipelineStepStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"
