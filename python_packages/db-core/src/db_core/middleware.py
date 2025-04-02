"""
FastAPI middleware for tenant identification and context setting.
"""

import logging
import re
from contextvars import ContextVar
from typing import Any, Callable, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from starlette.types import ASGIApp

from db_core.config import MultitenancySettings
from db_core.exceptions import InvalidTenantIdError, MissingTenantIdError, TenantNotFoundError
from db_core.utils import validate_tenant_id

logger = logging.getLogger(__name__)

# Context variable to store the current tenant ID
current_tenant_id: ContextVar[Optional[str]] = ContextVar("current_tenant_id", default=None)


def get_current_tenant_id() -> Optional[str]:
    """
    Get the current tenant ID from the context variable.

    Returns:
        The current tenant ID, or None if no tenant ID is set
    """
    return current_tenant_id.get()


def set_current_tenant_id(tenant_id: Optional[str]) -> None:
    """
    Set the current tenant ID in the context variable.

    Args:
        tenant_id: The tenant ID to set
    """
    current_tenant_id.set(tenant_id)


class TenantMiddleware(BaseHTTPMiddleware):
    """Middleware for extracting and validating tenant ID from request headers."""

    def __init__(
        self,
        app: ASGIApp,
        settings: MultitenancySettings,
        tenant_callback: Optional[Callable[[str], bool]] = None,
        excluded_paths: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the tenant middleware.

        Args:
            app: The ASGI application
            settings: The multitenancy settings
            tenant_callback: Optional callback function to validate tenant ID
            excluded_paths: Optional dictionary of path patterns to exclude from tenant validation
        """
        super().__init__(app)
        self.settings = settings
        self.tenant_callback = tenant_callback
        self.excluded_paths = excluded_paths or {}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Process the request and extract tenant ID.

        Args:
            request: The incoming request
            call_next: The next request handler

        Returns:
            The response from the next handler
        """
        # Check if the path is excluded from tenant validation
        path = request.url.path
        for pattern, options in self.excluded_paths.items():
            if re.match(pattern, path):
                tenant_id = options.get("default_tenant", self.settings.default_tenant_id)
                set_current_tenant_id(tenant_id)
                return await call_next(request)

        # Extract tenant ID from the header
        tenant_id = request.headers.get(self.settings.tenant_id_header)

        # If no tenant ID is provided, use the default tenant ID if configured
        if not tenant_id:
            if self.settings.default_tenant_id:
                tenant_id = self.settings.default_tenant_id
            else:
                error = MissingTenantIdError()
                return JSONResponse(
                    status_code=400,
                    content={"detail": str(error)},
                )

        # Normalize tenant ID if case sensitivity is not required
        if not self.settings.case_sensitive_tenant_id:
            tenant_id = tenant_id.lower()

        try:
            # Validate tenant ID
            if not validate_tenant_id(tenant_id, self.settings):
                error = InvalidTenantIdError(tenant_id, self.settings.tenant_id_validation_pattern)
                return JSONResponse(
                    status_code=400,
                    content={"detail": str(error)},
                )

            # Custom tenant validation callback
            if self.tenant_callback and not self.tenant_callback(tenant_id):
                error = TenantNotFoundError(tenant_id)
                return JSONResponse(
                    status_code=404,
                    content={"detail": str(error)},
                )

            # Set the current tenant ID in the context
            set_current_tenant_id(tenant_id)

            # Process the request
            response = await call_next(request)

            return response
        except Exception as e:
            logger.exception(f"Error processing request for tenant {tenant_id}: {e}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
        finally:
            # Reset the tenant ID
            set_current_tenant_id(None)


def add_tenant_middleware(
    app: FastAPI,
    settings: MultitenancySettings,
    tenant_callback: Optional[Callable[[str], bool]] = None,
    excluded_paths: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Add the tenant middleware to a FastAPI application.

    Args:
        app: The FastAPI application
        settings: The multitenancy settings
        tenant_callback: Optional callback function to validate tenant ID
        excluded_paths: Optional dictionary of path patterns to exclude from tenant validation
    """
    app.add_middleware(
        TenantMiddleware,
        settings=settings,
        tenant_callback=tenant_callback,
        excluded_paths=excluded_paths,
    )
