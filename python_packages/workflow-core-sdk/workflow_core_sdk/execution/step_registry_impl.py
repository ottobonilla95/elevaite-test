"""
Step Registry Implementation

Manages registration and execution of workflow steps.
Supports local functions, RPC endpoints, API calls, and gRPC.
"""

import uuid
import importlib
import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import logging

from .context import ExecutionContext, StepResult
from ..models import StepStatus
from ..monitoring import monitoring


logger = logging.getLogger(__name__)


class StepExecutionError(Exception):
    """Exception raised during step execution"""

    pass


class StepRegistry:
    """
    Registry for workflow step functions.

    Supports:
    - Local Python functions
    - RPC endpoints
    - REST API calls
    - gRPC calls
    - Dynamic registration
    """

    def __init__(self):
        self.registered_steps: Dict[str, Dict[str, Any]] = {}
        self.step_functions: Dict[str, Callable] = {}

    async def register_step(self, step_config: Dict[str, Any]) -> str:
        """Register a new step type"""
        step_type = step_config["step_type"]
        step_id = str(uuid.uuid4())

        # Validate step configuration
        required_fields = ["step_type", "name", "function_reference", "execution_type"]
        for field in required_fields:
            if field not in step_config:
                raise ValueError(f"Missing required field: {field}")

        # Store step configuration
        self.registered_steps[step_type] = {
            "step_id": step_id,
            "step_type": step_type,
            "name": step_config["name"],
            "description": step_config.get("description", ""),
            "function_reference": step_config["function_reference"],
            "execution_type": step_config["execution_type"],
            "parameters_schema": step_config.get("parameters_schema", {}),
            "output_schema": step_config.get("output_schema", {}),
            "endpoint_config": step_config.get("endpoint_config", {}),
            "tags": step_config.get("tags", []),
            "registered_at": datetime.now().isoformat(),
        }

        # Load function if it's a local execution type
        if step_config["execution_type"] == "local":
            await self._load_local_function(
                step_type, step_config["function_reference"]
            )

        logger.info(
            f"Registered step type: {step_type} ({step_config['execution_type']})"
        )
        return step_id

    async def _load_local_function(self, step_type: str, function_reference: str):
        """Load a local Python function"""
        try:
            # Parse module.function format
            if "." not in function_reference:
                raise ValueError(f"Invalid function reference: {function_reference}")

            module_path, function_name = function_reference.rsplit(".", 1)

            # Import module and get function
            module = importlib.import_module(module_path)
            function = getattr(module, function_name)

            # Store function
            self.step_functions[step_type] = function

        except Exception as e:
            logger.error(f"Failed to load function {function_reference}: {e}")
            raise StepExecutionError(f"Failed to load function: {e}")

    async def execute_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> StepResult:
        """Execute a step based on its type"""

        if step_type not in self.registered_steps:
            raise StepExecutionError(f"Unknown step type: {step_type}")

        step_info = self.registered_steps[step_type]
        execution_type = step_info["execution_type"]

        start_time = datetime.now()
        step_id = step_config.get("step_id", "unknown")

        # Start step tracing
        with monitoring.trace_step_execution(
            step_id=step_id,
            step_type=step_type,
            execution_id=execution_context.execution_id,
        ):
            try:
                # Execute based on execution type
                if execution_type == "local":
                    result = await self._execute_local_step(
                        step_type, step_config, input_data, execution_context
                    )
                elif execution_type == "rpc":
                    result = await self._execute_rpc_step(
                        step_type, step_config, input_data, execution_context
                    )
                elif execution_type == "api":
                    result = await self._execute_api_step(
                        step_type, step_config, input_data, execution_context
                    )
                elif execution_type == "grpc":
                    result = await self._execute_grpc_step(
                        step_type, step_config, input_data, execution_context
                    )
                else:
                    raise Exception(f"Unknown execution type: {execution_type}")

                # Calculate execution time
                end_time = datetime.now()
                execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

                # If the step returned a StepResult, propagate it (supports WAITING/FAILED/etc.)
                if isinstance(result, StepResult):
                    if result.execution_time_ms is None:
                        result.execution_time_ms = execution_time_ms
                    return result

                # If the step returned a dict indicating WAITING, map to a WAITING StepResult
                if (
                    isinstance(result, dict)
                    and str(result.get("status", "")).lower() == "waiting"
                ):
                    return StepResult(
                        step_id=step_id,
                        status=StepStatus.WAITING,
                        output_data=result,
                        execution_time_ms=execution_time_ms,
                    )

                # Otherwise, wrap raw output as a completed step
                return StepResult(
                    step_id=step_id,
                    status=StepStatus.COMPLETED,
                    output_data=result,
                    execution_time_ms=execution_time_ms,
                )

            except Exception as e:
                # Calculate execution time even for failed steps
                end_time = datetime.now()
                execution_time_ms = int((end_time - start_time).total_seconds() * 1000)

                # Return failed step result
                return StepResult(
                    step_id=step_id,
                    status=StepStatus.FAILED,
                    error_message=str(e),
                    execution_time_ms=execution_time_ms,
                )

    async def _execute_local_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute a local Python function"""

        if step_type not in self.step_functions:
            raise StepExecutionError(f"Function not loaded for step type: {step_type}")

        function = self.step_functions[step_type]

        # Prepare function arguments
        kwargs = {
            "step_config": step_config,
            "input_data": input_data,
            "execution_context": execution_context,
        }

        # Execute function (handle both sync and async)
        if asyncio.iscoroutinefunction(function):
            result = await function(**kwargs)
        else:
            result = function(**kwargs)

        return result

    async def _execute_rpc_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute an RPC step"""
        step_info = self.registered_steps[step_type]
        endpoint_config = step_info["endpoint_config"]

        # Prepare RPC call
        rpc_url = endpoint_config.get("url")
        if not rpc_url:
            raise StepExecutionError("RPC URL not configured")

        payload = {
            "step_config": step_config,
            "input_data": input_data,
            "execution_context": {
                "execution_id": execution_context.execution_id,
                "workflow_id": execution_context.workflow_id,
                "user_context": {
                    "user_id": execution_context.user_context.user_id
                    if execution_context.user_context
                    else None,
                    "session_id": execution_context.user_context.session_id
                    if execution_context.user_context
                    else None,
                },
            },
        }

        # Make RPC call
        timeout = endpoint_config.get("timeout", 30)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                rpc_url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status != 200:
                    raise StepExecutionError(f"RPC call failed: {response.status}")

                result = await response.json()
                return result

    async def _execute_api_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute an API step"""
        step_info = self.registered_steps[step_type]
        endpoint_config = step_info["endpoint_config"]

        # Prepare API call
        api_url = endpoint_config.get("url")
        method = endpoint_config.get("method", "POST").upper()
        headers = endpoint_config.get("headers", {})

        if not api_url:
            raise StepExecutionError("API URL not configured")

        # Prepare request data
        request_data = {"step_config": step_config, "input_data": input_data}

        # Make API call
        timeout = endpoint_config.get("timeout", 30)
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                api_url,
                json=request_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                if response.status not in [200, 201]:
                    raise StepExecutionError(f"API call failed: {response.status}")
                result = await response.json()
                return result

    async def _execute_grpc_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute a gRPC step via a user-provided invoker.

        Design:
        - Keep this registry light by delegating heavy gRPC client code to an external package/app.
        - endpoint_config.invoker should be a dotted path to a callable that performs the gRPC call.
          Example: "elevaite_ingestion.client.vectorize_invoker"
        - The callable can be sync or async and must accept kwargs: step_config, input_data, execution_context, endpoint_config.
        - It should return a JSON-serializable dict or a StepResult.
        """
        step_info = self.registered_steps[step_type]
        endpoint_config = step_info.get("endpoint_config", {}) or {}
        invoker_ref = endpoint_config.get("invoker")
        if not invoker_ref:
            raise StepExecutionError(
                "gRPC invoker not configured; set endpoint_config.invoker to '<module>:<callable>' or '<module>.<callable>'"
            )

        # Support both module:function and module.function formats
        if ":" in invoker_ref:
            module_path, func_name = invoker_ref.split(":", 1)
        else:
            module_path, func_name = invoker_ref.rsplit(".", 1)

        try:
            mod = importlib.import_module(module_path)
            invoker = getattr(mod, func_name)
        except Exception as e:
            raise StepExecutionError(
                f"Failed to import gRPC invoker '{invoker_ref}': {e}"
            )

        kwargs = {
            "step_config": step_config,
            "input_data": input_data,
            "execution_context": execution_context,
            "endpoint_config": endpoint_config,
        }

        try:
            if asyncio.iscoroutinefunction(invoker):
                return await invoker(**kwargs)
            else:
                return invoker(**kwargs)
        except Exception as e:
            # Surface underlying gRPC/client errors as step failures
            raise StepExecutionError(f"gRPC invoker execution failed: {e}")

    async def get_registered_steps(self) -> List[Dict[str, Any]]:
        """Get list of all registered steps"""
        return list(self.registered_steps.values())

    async def get_step_info(self, step_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific step type"""
        return self.registered_steps.get(step_type)

    async def unregister_step(self, step_type: str) -> bool:
        """Unregister a step type"""
        if step_type in self.registered_steps:
            del self.registered_steps[step_type]
            if step_type in self.step_functions:
                del self.step_functions[step_type]
            logger.info(f"Unregistered step type: {step_type}")
            return True
        return False

    async def register_builtin_steps(self):
        """
        Register built-in step types.

        Note: This method will be implemented by importing step definitions
        from the steps module once they are moved to the SDK.
        For now, this is a placeholder that applications can override.
        """
        logger.info(
            "Built-in steps registration - to be implemented with step migrations"
        )
        pass
