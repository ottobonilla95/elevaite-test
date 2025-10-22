"""
Workflow Adapter - High-level adapter for workflow operations

This adapter provides high-level methods for workflow-related operations,
combining request and response adapters.
"""

from typing import Dict, Any, List, Optional
from .request_adapter import RequestAdapter
from .response_adapter import ResponseAdapter


class WorkflowAdapter:
    """High-level adapter for workflow operations"""

    @staticmethod
    def adapt_create_request(as_request: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt workflow creation request from AS to SDK format"""
        return RequestAdapter.adapt_workflow_create_request(as_request)

    @staticmethod
    def adapt_update_request(as_request: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt workflow update request from AS to SDK format"""
        return RequestAdapter.adapt_workflow_update_request(as_request)

    @staticmethod
    def adapt_workflow_response(sdk_workflow: Any) -> Dict[str, Any]:
        """Adapt workflow response from SDK to AS format"""
        return ResponseAdapter.adapt_workflow_response(sdk_workflow)

    @staticmethod
    def adapt_list_response(sdk_workflows: List[Any]) -> List[Dict[str, Any]]:
        """Adapt workflow list response from SDK to AS format"""
        return ResponseAdapter.adapt_workflow_list_response(sdk_workflows)

