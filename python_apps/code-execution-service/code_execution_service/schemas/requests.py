"""Request schemas for the Code Execution Service."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecuteRequest(BaseModel):
    """Request model for code execution."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "language": "python",
                "code": "print('Hello, World!')",
                "timeout_seconds": 30,
                "memory_mb": 256,
                "input_data": {"key": "value"},
            }
        }
    )

    language: str = Field(
        default="python",
        description="Programming language to execute. Only 'python' is supported in Phase 1.",
    )
    code: str = Field(
        ...,
        description="The code to execute.",
        min_length=1,
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=60,
        description="Maximum execution time in seconds (1-60).",
    )
    memory_mb: int = Field(
        default=256,
        ge=64,
        le=512,
        description="Maximum memory allocation in MB (64-512).",
    )
    input_data: dict[str, Any] | None = Field(
        default=None,
        description="Optional input data available as 'input_data' variable in the code.",
    )
