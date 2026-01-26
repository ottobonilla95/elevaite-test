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
from db_core.exceptions import (
    InvalidTenantIdError,
    MissingTenantIdError,
    TenantNotFoundError,
)
from db_core.utils import validate_tenant_id

logger = logging.getLogger(__name__)

# Context variable to store the current tenant ID
current_tenant_id: ContextVar[Optional[str]] = ContextVar("current_tenant_id", default=None)

# Dictionary to store original openapi functions for each app (using weak references)
_original_openapi_functions: Dict[int, Callable[..., Dict[str, Any]]] = {}


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

    @classmethod
    def add_tenant_header_to_openapi(cls, app: FastAPI, settings: MultitenancySettings) -> None:
        """
        Add the tenant header to the OpenAPI documentation.

        Args:
            app: The FastAPI application
            settings: The multitenancy settings
        """
        # Check if already patched by looking for this app's id in our dictionary
        app_id = id(app)
        if app_id in _original_openapi_functions:
            # Already patched
            return

        # Store the original openapi function
        _original_openapi_functions[app_id] = app.openapi

        def custom_openapi():
            if app.openapi_schema:
                return app.openapi_schema

            original_openapi = _original_openapi_functions[app_id]
            openapi_schema: Dict[str, Any] = original_openapi()

            if "components" not in openapi_schema:
                openapi_schema["components"] = {}
            if "parameters" not in openapi_schema["components"]:
                openapi_schema["components"]["parameters"] = {}

            # Define the tenant header parameter
            openapi_schema["components"]["parameters"]["tenant_header"] = {
                "name": settings.tenant_id_header,
                "in": "header",
                "required": True,
                "schema": {
                    "title": "Tenant ID",
                    "type": "string",
                    "default": settings.default_tenant_id or "tenant1",
                    "example": settings.default_tenant_id or "tenant1",
                },
                "description": "The tenant identifier used for schema-based multitenancy",
            }

            # Add the tenant header parameter to all paths except docs and openapi
            for path_name, path_item in openapi_schema["paths"].items():
                # Skip documentation paths
                if path_name.startswith("/docs") or path_name.startswith("/redoc") or path_name == "/openapi.json":
                    continue

                for operation in path_item.values():
                    if "parameters" not in operation:
                        operation["parameters"] = []
                    operation["parameters"].append({"$ref": "#/components/parameters/tenant_header"})

            app.openapi_schema = openapi_schema
            return app.openapi_schema

        app.openapi = custom_openapi


def add_tenant_middleware(
    app: FastAPI,
    settings: MultitenancySettings,
    tenant_callback: Optional[Callable[[str], bool]] = None,
    excluded_paths: Optional[Dict[str, Any]] = None,
    add_openapi_header: bool = True,
) -> None:
    """
    Add the tenant middleware to a FastAPI application.

    Args:
        app: The FastAPI application
        settings: The multitenancy settings
        tenant_callback: Optional callback function to validate tenant ID
        excluded_paths: Optional dictionary of path patterns to exclude from tenant validation
        add_openapi_header: Whether to add the tenant header to OpenAPI documentation
    """
    app.add_middleware(
        TenantMiddleware,
        settings=settings,
        tenant_callback=tenant_callback,
        excluded_paths=excluded_paths,
    )

    if add_openapi_header:
        TenantMiddleware.add_tenant_header_to_openapi(app, settings)


def add_tenant_header_to_openapi(cls, app: FastAPI, settings: MultitenancySettings) -> None:
    """
    Add the tenant header to the OpenAPI documentation.

    Args:
        app: The FastAPI application
        settings: The multitenancy settings
    """
    # Check if already patched by looking for this app's id in our dictionary
    app_id = id(app)
    if app_id in _original_openapi_functions:
        # Already patched
        return

    # Store the original openapi function
    _original_openapi_functions[app_id] = app.openapi

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        original_openapi = _original_openapi_functions[app_id]
        openapi_schema: Dict[str, Any] = original_openapi()

        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        if "parameters" not in openapi_schema["components"]:
            openapi_schema["components"]["parameters"] = {}

        # Define the tenant header parameter
        openapi_schema["components"]["parameters"]["tenant_header"] = {
            "name": settings.tenant_id_header,
            "in": "header",
            "required": True,
            "schema": {
                "title": "Tenant ID",
                "type": "string",
                "default": settings.default_tenant_id or "tenant1",
                "example": settings.default_tenant_id or "tenant1",
            },
            "description": "The tenant identifier used for schema-based multitenancy",
        }

        # Add the tenant header parameter to all paths except docs and openapi
        for path_name, path_item in openapi_schema["paths"].items():
            # Skip documentation paths
            if path_name.startswith("/docs") or path_name.startswith("/redoc") or path_name == "/openapi.json":
                continue

            for operation in path_item.values():
                if "parameters" not in operation:
                    operation["parameters"] = []
                operation["parameters"].append({"$ref": "#/components/parameters/tenant_header"})

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
