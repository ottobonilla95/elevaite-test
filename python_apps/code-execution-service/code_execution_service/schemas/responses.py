"""Response schemas for the Code Execution Service."""

from pydantic import BaseModel, ConfigDict, Field


class ExecuteResponse(BaseModel):
    """Response model for code execution results."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "stdout": "Hello, World!\n",
                "stderr": "",
                "exit_code": 0,
                "execution_time_ms": 45,
                "error": None,
                "validation_errors": None,
            }
        }
    )

    success: bool = Field(
        ...,
        description="Whether the code executed successfully without errors.",
    )
    stdout: str = Field(
        default="",
        description="Standard output from the code execution.",
    )
    stderr: str = Field(
        default="",
        description="Standard error output from the code execution.",
    )
    exit_code: int = Field(
        default=0,
        description="Exit code from the execution (0 = success).",
    )
    execution_time_ms: int = Field(
        default=0,
        description="Execution time in milliseconds.",
    )
    error: str | None = Field(
        default=None,
        description="Error message if execution failed.",
    )
    validation_errors: list[str] | None = Field(
        default=None,
        description="List of validation errors if code failed pre-execution checks.",
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(
        default="healthy",
        description="Service health status.",
    )
    nsjail_available: bool = Field(
        default=False,
        description="Whether Nsjail binary is available.",
    )
