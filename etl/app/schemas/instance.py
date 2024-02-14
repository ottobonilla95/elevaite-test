from enum import Enum


class InstanceStatus(str, Enum):
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"
