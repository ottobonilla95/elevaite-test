"""Health check router."""

from fastapi import APIRouter

from ..schemas.responses import HealthResponse
from ..services.sandbox import SandboxExecutor

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns service health status and Nsjail availability.
    """
    sandbox = SandboxExecutor()

    return HealthResponse(
        status="healthy",
        nsjail_available=sandbox.is_available(),
    )

