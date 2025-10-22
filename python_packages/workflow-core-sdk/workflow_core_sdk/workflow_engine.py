"""
Unified Workflow Execution Engine

The core engine that executes workflows in a completely agnostic way.
Supports conditional, sequential, and parallel execution patterns.
"""

import asyncio
import os

import logging
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime

from .execution.context_impl import ExecutionContext, StepResult

# Prefer SDK status enums; fallback to local if SDK unavailable
from .models import ExecutionStatus, StepStatus
from .execution.registry_impl import StepRegistry
from .execution.error_handling import (
    error_handler,
    RetryConfig,
    RetryStrategy,
    ErrorSeverity,
    StepExecutionError,
    ValidationError,
    RetryableError,
    NonRetryableError,
)
from .utils.condition_evaluator import (
    condition_evaluator,
    Condition,
    ConditionalExpression,
    ConditionOperator,
    LogicalOperator,
)
from .monitoring import monitoring

from .services.analytics_service import analytics_service
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # type-only import to avoid runtime dependency
    from .execution import StepRegistryProtocol


logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Unified workflow execution engine.

    This engine is completely agnostic to workflow structure and simply
    executes the appropriate function at the appropriate step based on
    dependencies and execution patterns.
    """

    def __init__(self, step_registry: "StepRegistryProtocol"):
        self.step_registry = step_registry
        self.active_executions: Dict[str, ExecutionContext] = {}
        self.execution_history: List[ExecutionContext] = []

    async def execute_workflow(self, execution_context: ExecutionContext) -> ExecutionContext:
        """
        Execute a workflow using the provided execution context.

        This is the main entry point for workflow execution.
        The engine determines the execution pattern and manages step execution accordingly.
        """
        execution_id = execution_context.execution_id

        try:
            # Store execution context
            self.active_executions[execution_id] = execution_context

            # Update active executions metric
            monitoring.update_active_executions(len(self.active_executions))

            # Start execution
            execution_context.start_execution()
            logger.info(f"Starting workflow execution: {execution_id}")

            # Start workflow tracing
            with monitoring.trace_workflow_execution(workflow_id=execution_context.workflow_id, execution_id=execution_id):
                # Determine execution pattern
                execution_pattern = execution_context.workflow_config.get("execution_pattern", "sequential")

                if execution_pattern == "sequential":
                    await self._execute_sequential(execution_context)
                elif execution_pattern == "parallel":
                    await self._execute_parallel(execution_context)
                elif execution_pattern == "conditional":
                    await self._execute_conditional(execution_context)
                else:
                    # Default to dependency-based execution
                    await self._execute_dependency_based(execution_context)

            # Complete execution
            if execution_context.status == ExecutionStatus.RUNNING:
                execution_context.complete_execution()
                logger.info(f"Workflow execution completed: {execution_id}")
                # Persist final status and step I/O snapshot to DB for API reads
                try:
                    from sqlmodel import Session as _SQLSession
                    from workflow_core_sdk.db.database import engine as _engine
                    from workflow_core_sdk.db.service import DatabaseService as _DBS

                    seconds = None
                    try:
                        if execution_context.started_at and execution_context.completed_at:
                            seconds = (execution_context.completed_at - execution_context.started_at).total_seconds()
                    except Exception:
                        pass

                    with _SQLSession(_engine) as _s:
                        _DBS().update_execution(
                            _s,
                            execution_context.execution_id,
                            {
                                "status": execution_context.status,
                                "step_io_data": execution_context.step_io_data,
                                "output_data": {},
                                "completed_at": execution_context.completed_at,
                                "execution_time_seconds": seconds,
                            },
                        )
                except Exception as _persist_e:
                    logger.warning(f"Failed to persist final execution state: {_persist_e}")

                # Persist workflow-level analytics rollup (tokens-only)
                try:
                    # Sum tokens across agent steps
                    totals = {"tokens_in": 0, "tokens_out": 0, "total_tokens": 0, "llm_calls": 0}
                    for sid, step in execution_context.step_results.items():
                        od = step.output_data or {}
                        if isinstance(od, dict) and od.get("usage"):
                            u = od["usage"]
                            try:
                                totals["tokens_in"] += int(u.get("tokens_in", 0) or 0)
                                totals["tokens_out"] += int(u.get("tokens_out", 0) or 0)
                                totals["total_tokens"] += int(u.get("total_tokens", 0) or 0)
                                totals["llm_calls"] += int(u.get("llm_calls", 0) or 0)
                            except Exception:
                                pass
                    summary = execution_context.get_execution_summary()
                    # Use a real Session context manager (get_session is a generator)
                    from sqlmodel import Session as _SQLSession
                    from workflow_core_sdk.db.database import engine as _engine

                    with _SQLSession(_engine) as _s:
                        analytics_service.record_workflow_metrics(
                            _s,
                            execution_id=execution_context.execution_id,
                            workflow_id=execution_context.workflow_id,
                            workflow_name=execution_context.workflow_name,
                            summary=summary,
                            totals=totals,
                            status=summary.get("status", "completed"),
                            started_at=execution_context.started_at,
                            completed_at=execution_context.completed_at,
                        )
                except Exception as we:
                    logger.warning(f"Workflow analytics rollup failed: {we}")

        except Exception as e:
            logger.error(f"Workflow execution failed: {execution_id} - {e}")
            execution_context.fail_execution(str(e))
            monitoring.record_error("workflow_engine", "execution_error", str(e))

        finally:
            # Move to history and clean up
            # Keep WAITING executions active so they can be resumed
            if execution_context.status in (ExecutionStatus.COMPLETED, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
                if execution_id in self.active_executions:
                    del self.active_executions[execution_id]
                self.execution_history.append(execution_context)

            # Update active executions metric
            monitoring.update_active_executions(len(self.active_executions))

            # Keep only recent history (last 1000 executions)
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]

        return execution_context

    async def _execute_sequential(self, execution_context: ExecutionContext):
        """Execute steps sequentially based on step_order"""

        # Sort steps by step_order (handle None values)
        steps = sorted(
            execution_context.steps_config,
            key=lambda s: s.get("step_order") if s.get("step_order") is not None else 0,
        )

        for step_config in steps:
            if execution_context.status != ExecutionStatus.RUNNING:
                break

            step_id = step_config["step_id"]

            # Check if dependencies are satisfied
            if not execution_context.can_execute_step(step_id):
                logger.warning(f"Skipping step {step_id} - dependencies not satisfied")
                continue

            # Execute step
            await self._execute_single_step(execution_context, step_config)

    async def _execute_parallel(self, execution_context: ExecutionContext):
        """Execute steps in parallel where possible, respecting dependencies"""

        while not execution_context.is_execution_complete():
            if execution_context.status != ExecutionStatus.RUNNING:
                break

            # Get all ready steps
            ready_steps = execution_context.get_ready_steps()

            if not ready_steps:
                # No steps ready - check if we're stuck
                if execution_context.pending_steps:
                    logger.error("Workflow stuck - no steps ready but steps pending")
                    execution_context.fail_execution("Workflow stuck - circular dependencies or missing steps")
                break

            # Execute all ready steps in parallel
            tasks = []
            for step_id in ready_steps:
                step_config = execution_context.get_step_config(step_id)
                if step_config:
                    task = asyncio.create_task(self._execute_single_step(execution_context, step_config))
                    tasks.append(task)

            # Wait for all parallel steps to complete
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_conditional(self, execution_context: ExecutionContext):
        """Execute steps based on conditional logic"""

        # For now, implement as dependency-based execution
        # TODO: Add support for conditional expressions in step configs
        await self._execute_dependency_based(execution_context)

    async def _execute_dependency_based(self, execution_context: ExecutionContext):
        """Execute steps based purely on dependency satisfaction"""

        while not execution_context.is_execution_complete():
            if execution_context.status != ExecutionStatus.RUNNING:
                break

            # Get ready steps
            ready_steps = execution_context.get_ready_steps()

            if not ready_steps:
                if execution_context.pending_steps:
                    logger.error("Workflow stuck - no steps ready but steps pending")
                    execution_context.fail_execution("Workflow stuck - circular dependencies")
                break

            # Execute one step at a time (can be made parallel if needed)
            step_id = ready_steps[0]
            step_config = execution_context.get_step_config(step_id)

            if step_config:
                await self._execute_single_step(execution_context, step_config)

    async def _execute_single_step(self, execution_context: ExecutionContext, step_config: Dict[str, Any]):
        """Execute a single step with enhanced error handling and retry logic"""

        step_id = step_config["step_id"]
        step_type = step_config["step_type"]

        logger.info(f"Executing step: {step_id} ({step_type})")

        # Update current step
        execution_context.current_step = step_id

        # Check if step should be executed based on conditions
        if not self._should_execute_step(execution_context, step_config):
            logger.info(f"Step {step_id} skipped due to conditions not being met")
            # Mark step as skipped
            execution_context.skip_step(step_id, "Conditions not met")
            return

        # Create retry configuration from step config
        retry_config = self._create_retry_config(step_config)

        # Context for error handling
        error_context = {
            "component": "workflow_engine",
            "operation": f"execute_step_{step_id}",
            "step_id": step_id,
            "step_type": step_type,
            "execution_id": execution_context.execution_id,
        }

        try:
            # Execute step with retry logic
            step_result = await error_handler.execute_with_retry(
                self._execute_step_once,
                execution_context,
                step_config,
                retry_config=retry_config,
                context=error_context,
            )

            # Store result
            execution_context.store_step_result(step_result)
            # Persist step I/O snapshot to DB so the API response reflects latest data
            try:
                from sqlmodel import Session as _SQLSession
                from workflow_core_sdk.db.database import engine as _engine
                from workflow_core_sdk.db.service import DatabaseService as _DBS

                with _SQLSession(_engine) as _s:
                    _DBS().update_execution(
                        _s,
                        execution_context.execution_id,
                        {
                            "status": execution_context.status,
                            "step_io_data": execution_context.step_io_data,
                        },
                    )
            except Exception as _persist_step_e:
                logger.warning(f"Failed to persist step I/O for {execution_context.execution_id}: {_persist_step_e}")

            if step_result.status == StepStatus.WAITING:
                # Early exit; engine will pause
                return

            if step_result.status == StepStatus.COMPLETED:
                logger.info(f"Step completed: {step_id} ({step_result.execution_time_ms}ms)")

                # Persist agent analytics if applicable (tokens-only)
                try:
                    if step_type == "agent_execution" and isinstance(step_result.output_data, dict):
                        agent_out = step_result.output_data
                        # Insert analytics row
                        # Use a real Session context manager (get_session is a generator)
                        from sqlmodel import Session as _SQLSession
                        from workflow_core_sdk.db.database import engine as _engine

                        with _SQLSession(_engine) as _s:
                            analytics_service.record_agent_execution(
                                _s,
                                execution_id=execution_context.execution_id,
                                step_execution_id=None,  # optional: wire actual StepExecution.id if available
                                agent_output=agent_out,
                                status="completed",
                                started_at=execution_context.started_at,
                                completed_at=execution_context.completed_at,
                                error_message=None,
                                redact_response_in_analytics=bool(
                                    os.getenv("REDACT_ANALYTICS_RESPONSE", "false").lower() == "true"
                                ),
                            )
                except Exception as ae:
                    logger.warning(f"Analytics record for agent step failed: {ae}")
            elif step_result.status == StepStatus.WAITING:
                logger.info(f"Step waiting: {step_id} - human interaction required")
                # Persist as needed (DB write happens in router/service)
                # Leave execution_context.status as WAITING (set by step) and stop further processing
                return
            else:
                logger.error(f"Step failed: {step_id} - {step_result.error_message}")

                # Check if this should fail the entire workflow
                if step_config.get("critical", True):  # Steps are critical by default
                    execution_context.fail_execution(f"Critical step {step_id} failed: {step_result.error_message}")

        except Exception as e:
            # Final failure after all retries
            logger.error(f"Step {step_id} failed after all retries: {e}")
            execution_context.fail_execution(f"Step {step_id} failed: {e}")

    async def _execute_step_once(self, execution_context: ExecutionContext, step_config: Dict[str, Any]):
        """Execute a single step once (used by retry mechanism)"""

        step_id = step_config["step_id"]
        step_type = step_config["step_type"]

        # Get input data for this step
        input_data = execution_context.get_step_input_data(step_id)

        # Execute step through registry with timeout if configured
        timeout = step_config.get("timeout_seconds")

        try:
            if timeout:
                step_result = await asyncio.wait_for(
                    self.step_registry.execute_step(
                        step_type=step_type,
                        step_config=step_config,
                        input_data=input_data,
                        execution_context=execution_context,
                    ),
                    timeout=timeout,
                )
            else:
                step_result = await self.step_registry.execute_step(
                    step_type=step_type,
                    step_config=step_config,
                    input_data=input_data,
                    execution_context=execution_context,
                )

        except asyncio.TimeoutError:
            raise RetryableError(
                f"Step {step_id} timed out after {timeout} seconds",
                severity=ErrorSeverity.HIGH,
                component="step_execution",
                operation="execute_step",
            )
        except Exception as e:
            # Classify error for retry logic
            if self._is_retryable_step_error(e):
                raise RetryableError(
                    f"Retryable error in step {step_id}: {e}",
                    severity=ErrorSeverity.MEDIUM,
                    component="step_execution",
                    operation="execute_step",
                )
            else:
                raise NonRetryableError(
                    f"Non-retryable error in step {step_id}: {e}",
                    severity=ErrorSeverity.HIGH,
                    component="step_execution",
                    operation="execute_step",
                )

        return step_result

    def _create_retry_config(self, step_config: Dict[str, Any]) -> RetryConfig:
        """Create retry configuration from step configuration"""

        # Get retry settings from step config
        max_retries = step_config.get("max_retries", 3)
        retry_strategy = step_config.get("retry_strategy", "exponential_backoff")
        retry_delay = step_config.get("retry_delay_seconds", 1.0)
        max_retry_delay = step_config.get("max_retry_delay_seconds", 60.0)

        # Map string strategy to enum
        strategy_map = {
            "none": RetryStrategy.NONE,
            "fixed_delay": RetryStrategy.FIXED_DELAY,
            "exponential_backoff": RetryStrategy.EXPONENTIAL_BACKOFF,
            "linear_backoff": RetryStrategy.LINEAR_BACKOFF,
        }

        strategy = strategy_map.get(retry_strategy, RetryStrategy.EXPONENTIAL_BACKOFF)

        return RetryConfig(
            max_attempts=max_retries + 1,  # +1 for initial attempt
            strategy=strategy,
            base_delay=retry_delay,
            max_delay=max_retry_delay,
            backoff_multiplier=2.0,
            jitter=True,
        )

    def _is_retryable_step_error(self, error: Exception) -> bool:
        """Determine if a step error is retryable"""

        # Network and connection errors are usually retryable
        retryable_types = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
            OSError,  # Network-related OS errors
        )

        # Logic and configuration errors are not retryable
        non_retryable_types = (
            ValueError,
            TypeError,
            AttributeError,
            KeyError,
            ValidationError,
        )

        if isinstance(error, non_retryable_types):
            return False

        if isinstance(error, retryable_types):
            return True

        # Check error message for common retryable patterns
        error_msg = str(error).lower()
        retryable_patterns = [
            "connection",
            "timeout",
            "network",
            "temporary",
            "rate limit",
            "throttle",
            "busy",
            "unavailable",
        ]

        for pattern in retryable_patterns:
            if pattern in error_msg:
                return True

        # Default to non-retryable for unknown errors
        return False

    def _should_execute_step(self, execution_context: ExecutionContext, step_config: Dict[str, Any]) -> bool:
        """
        Check if a step should be executed based on its conditions.

        Args:
            execution_context: Current execution context
            step_config: Step configuration

        Returns:
            True if step should be executed, False otherwise
        """
        # Check if step has conditions
        conditions = step_config.get("conditions")
        if not conditions:
            return True  # No conditions means always execute

        try:
            # Prepare context for condition evaluation
            condition_context = self._prepare_condition_context(execution_context)

            # Handle different condition formats
            if isinstance(conditions, str):
                # Simple string condition
                condition = condition_evaluator.parse_condition_string(conditions)
                if condition:
                    return condition_evaluator.evaluate_condition(condition, condition_context)
                else:
                    logger.warning(f"Could not parse condition string: {conditions}")
                    return True

            elif isinstance(conditions, dict):
                # Complex condition object
                if "logical_operator" in conditions or "conditions" in conditions:
                    # Parse as conditional expression
                    expression = self._parse_conditional_expression(conditions)
                    if expression:
                        return condition_evaluator.evaluate_expression(expression, condition_context)
                else:
                    # Parse as single condition
                    condition = self._parse_condition_dict(conditions)
                    if condition:
                        return condition_evaluator.evaluate_condition(condition, condition_context)

            elif isinstance(conditions, list):
                # List of conditions (default AND logic)
                expression = ConditionalExpression(
                    conditions=[self._parse_condition_item(cond) for cond in conditions],
                    logical_operator=LogicalOperator.AND,
                )
                return condition_evaluator.evaluate_expression(expression, condition_context)

            logger.warning(f"Unknown condition format: {type(conditions)}")
            return True

        except Exception as e:
            logger.error(f"Error evaluating step conditions: {e}")
            return True  # Default to executing on error

    def _prepare_condition_context(self, execution_context: ExecutionContext) -> Dict[str, Any]:
        """Prepare context data for condition evaluation"""
        context = {
            "workflow": {
                "id": execution_context.workflow_config.get("workflow_id"),
                "status": execution_context.status.value,
                "current_step": execution_context.current_step,
            },
            "global": execution_context.step_io_data.get("global", {}),
            "input": execution_context.step_io_data.get("input", {}),
        }

        # Add step results
        for step_id, step_result in execution_context.step_results.items():
            context[step_id] = {
                "status": step_result.status.value,
                "output": step_result.output_data,
                "error": step_result.error_message,
                "execution_time_ms": step_result.execution_time_ms,
            }

        # Add step I/O data
        for step_id, step_data in execution_context.step_io_data.items():
            if step_id not in context:
                context[step_id] = {}
            context[step_id].update(step_data)

        return context

    def _parse_conditional_expression(self, expr_dict: Dict[str, Any]) -> Optional[ConditionalExpression]:
        """Parse a conditional expression from dictionary"""
        try:
            conditions = []

            if "conditions" in expr_dict:
                for cond_item in expr_dict["conditions"]:
                    parsed_cond = self._parse_condition_item(cond_item)
                    if parsed_cond:
                        conditions.append(parsed_cond)

            logical_op = LogicalOperator(expr_dict.get("logical_operator", "and"))

            return ConditionalExpression(
                conditions=conditions,
                logical_operator=logical_op,
                description=expr_dict.get("description"),
            )

        except Exception as e:
            logger.error(f"Error parsing conditional expression: {e}")
            return None

    def _parse_condition_dict(self, cond_dict: Dict[str, Any]) -> Optional[Condition]:
        """Parse a single condition from dictionary"""
        try:
            return Condition(
                left_operand=cond_dict["left_operand"],
                operator=ConditionOperator(cond_dict["operator"]),
                right_operand=cond_dict.get("right_operand"),
                description=cond_dict.get("description"),
            )
        except Exception as e:
            logger.error(f"Error parsing condition dict: {e}")
            return None

    def _parse_condition_item(self, item: Any) -> Optional[Union[Condition, ConditionalExpression]]:
        """Parse a condition item (string, dict, or nested expression)"""
        if isinstance(item, str):
            return condition_evaluator.parse_condition_string(item)
        elif isinstance(item, dict):
            if "expression" in item or "logical_operator" in item:
                return self._parse_conditional_expression(item)
            else:
                return self._parse_condition_dict(item)
        else:
            logger.warning(f"Unknown condition item type: {type(item)}")
            return None

    async def get_execution_context(self, execution_id: str) -> Optional[ExecutionContext]:
        """Get execution context by ID"""

        # Check active executions
        if execution_id in self.active_executions:
            return self.active_executions[execution_id]

        # Check history
        for context in self.execution_history:
            if context.execution_id == execution_id:
                return context

        return None

    async def resume_execution(self, execution_id: str, step_id: str, decision_output: Dict[str, Any]) -> bool:
        """Resume a paused local execution by injecting decision output and continuing."""
        ctx = await self.get_execution_context(execution_id)
        if not ctx:
            logger.error(f"Execution context not found for {execution_id}")
            return False
        # Inject decision output for the waiting step without marking it completed yet
        # Store decision data so the step can pick it up on next execution
        ctx.step_io_data[step_id] = decision_output

        # Mark the current execution as running again
        ctx.status = ExecutionStatus.RUNNING

        # Re-run dependency-based execution; the waiting step will execute again and can complete
        await self._execute_dependency_based(ctx)

        # If all steps done, mark complete
        if ctx.is_execution_complete() and ctx.status == ExecutionStatus.RUNNING:
            ctx.complete_execution()
        return True

    async def validate_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a workflow configuration"""

        errors = []
        warnings = []
        step_validation = {}

        # Basic validation
        if "steps" not in workflow_config:
            errors.append("Workflow must have 'steps' field")
            return {
                "is_valid": False,
                "errors": errors,
                "warnings": warnings,
                "step_validation": step_validation,
            }

        steps = workflow_config["steps"]
        step_ids = set()

        # Validate each step
        for step in steps:
            step_id = step.get("step_id")
            step_type = step.get("step_type")

            if not step_id:
                errors.append("Step missing 'step_id'")
                continue

            if step_id in step_ids:
                errors.append(f"Duplicate step_id: {step_id}")
            step_ids.add(step_id)

            if not step_type:
                errors.append(f"Step {step_id} missing 'step_type'")
                continue

            # Check if step type is registered
            step_info = await self.step_registry.get_step_info(step_type)
            if not step_info:
                errors.append(f"Unknown step type: {step_type}")
                step_validation[step_id] = {"error": f"Unknown step type: {step_type}"}
                continue

            # Validate dependencies
            dependencies = step.get("dependencies", [])
            for dep in dependencies:
                if dep not in step_ids and dep not in [s.get("step_id") for s in steps]:
                    errors.append(f"Step {step_id} depends on unknown step: {dep}")

            step_validation[step_id] = {"status": "valid", "step_type": step_type}

        # Enforce trigger rules: exactly one trigger, first step, no dependencies
        trigger_steps = [s for s in steps if s.get("step_type") == "trigger"]
        if len(trigger_steps) != 1:
            errors.append("Workflow must include exactly one 'trigger' step")
        else:
            trigger = trigger_steps[0]
            if trigger.get("dependencies"):
                errors.append("Trigger step must not have dependencies")
            # If steps have explicit ordering, enforce trigger first
            orders = [s.get("step_order") for s in steps if s.get("step_order") is not None]
            if orders:
                min_order = min(orders)
                if trigger.get("step_order") != min_order:
                    errors.append("Trigger step must be first in execution order")

        # Check for circular dependencies
        if not self._has_circular_dependencies(steps):
            warnings.append("Potential circular dependencies detected")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "step_validation": step_validation,
        }

    def _has_circular_dependencies(self, steps: List[Dict[str, Any]]) -> bool:
        """Check for circular dependencies using DFS"""

        # Build adjacency list
        graph = {}
        for step in steps:
            step_id = step.get("step_id")
            dependencies = step.get("dependencies", [])
            graph[step_id] = dependencies

        # DFS to detect cycles
        visited = set()
        rec_stack = set()

        def dfs(node):
            if node in rec_stack:
                return True  # Cycle detected
            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if dfs(neighbor):
                    return True

            rec_stack.remove(node)
            return False

        for step_id in graph:
            if step_id not in visited:
                if dfs(step_id):
                    return True

        return False

    async def get_execution_analytics(self, limit: int = 100, offset: int = 0, status: Optional[str] = None) -> Dict[str, Any]:
        """Get execution analytics and history"""

        # Combine active and historical executions
        all_executions = list(self.active_executions.values()) + self.execution_history

        # Filter by status if provided
        if status:
            all_executions = [exec_ctx for exec_ctx in all_executions if exec_ctx.status.value == status]

        # Sort by creation time (most recent first)
        all_executions.sort(key=lambda x: x.metadata.get("created_at", ""), reverse=True)

        # Paginate
        total = len(all_executions)
        paginated = all_executions[offset : offset + limit]

        # Generate statistics
        status_counts = {}
        for exec_ctx in all_executions:
            status = exec_ctx.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "total_executions": total,
            "executions": [exec_ctx.get_execution_summary() for exec_ctx in paginated],
            "statistics": {
                "status_distribution": status_counts,
                "active_executions": len(self.active_executions),
                "completed_executions": status_counts.get("completed", 0),
                "failed_executions": status_counts.get("failed", 0),
            },
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
                "has_more": offset + limit < total,
            },
        }
