"""
Execution Adapter - High-level adapter for execution operations

This adapter provides high-level methods for execution-related operations,
combining request and response adapters.
"""

from typing import Dict, Any, List, Optional
from .request_adapter import RequestAdapter
from .response_adapter import ResponseAdapter


class ExecutionAdapter:
    """High-level adapter for execution operations"""

    @staticmethod
    def adapt_execute_request(as_request: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt workflow execution request from AS to SDK format"""
        return RequestAdapter.adapt_workflow_execute_request(as_request)

    @staticmethod
    def adapt_execute_response(sdk_execution: Any) -> Dict[str, Any]:
        """Adapt workflow execution response from SDK to AS format"""
        return ResponseAdapter.adapt_execution_response(sdk_execution)

    @staticmethod
    def adapt_status_response(sdk_execution: Any) -> Dict[str, Any]:
        """Adapt execution status response from SDK to AS format"""
        return ResponseAdapter.adapt_execution_status_response(sdk_execution)

    @staticmethod
    def adapt_list_params(
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Adapt execution list parameters from AS to SDK format"""
        return RequestAdapter.adapt_execution_list_params(
            status=status,
            user_id=user_id,
            limit=limit,
            offset=offset,
        )

    @staticmethod
    def adapt_list_response(sdk_executions: List[Any]) -> List[Dict[str, Any]]:
        """Adapt execution list response from SDK to AS format"""
        return ResponseAdapter.adapt_execution_list_response(sdk_executions)

    @staticmethod
    def adapt_result_response(sdk_execution: Any) -> Any:
        """Extract result from SDK execution"""
        return ResponseAdapter.adapt_execution_result_response(sdk_execution)

