"""
Workflow Execution Context for Deterministic Workflows

Extends the existing analytics service to provide specialized support for
deterministic, multi-step workflows while maintaining compatibility with
the existing AI agent workflow system.

This service adds:
- Step dependency management and execution ordering
- Data flow tracking between steps
- Batch operation progress reporting
- Enhanced error handling and rollback capabilities
- Support for different execution patterns (sequential, parallel, conditional)
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Literal, Union, Callable
from contextlib import contextmanager
from enum import Enum
import uuid
import asyncio
from sqlalchemy.orm import Session
from pydantic import BaseModel

from services.analytics_service import analytics_service, WorkflowStep, ExecutionStatus
from fastapi_logger import ElevaiteLogger


class DeterministicStepType(str, Enum):
    """Extended step types for deterministic workflows"""

    # Existing types from analytics service
    AGENT_EXECUTION = "agent_execution"
    TOOL_CALL = "tool_call"
    DECISION_POINT = "decision_point"
    DATA_PROCESSING = "data_processing"

    # New deterministic workflow types
    DATA_INPUT = "data_input"
    DATA_OUTPUT = "data_output"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    BATCH_PROCESSING = "batch_processing"
    CONDITIONAL_BRANCH = "conditional_branch"
    PARALLEL_EXECUTION = "parallel_execution"
    AGGREGATION = "aggregation"
    NOTIFICATION = "notification"


class ExecutionPattern(str, Enum):
    """Workflow execution patterns"""

    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    DAG = "dag"  # Directed Acyclic Graph with dependencies


class StepDependency(BaseModel):
    """Define dependencies between workflow steps"""

    step_id: str
    depends_on: List[str] = []  # List of step_ids this step depends on
    condition: Optional[str] = None  # Optional condition for execution
    timeout_seconds: Optional[int] = None


class BatchProgress(BaseModel):
    """Progress tracking for batch operations"""

    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    current_batch: int = 0
    total_batches: int = 0
    estimated_completion: Optional[datetime] = None


class DeterministicWorkflowStep(WorkflowStep):
    """Extended WorkflowStep with deterministic workflow features"""

    step_type: DeterministicStepType
    dependencies: List[str] = []
    execution_pattern: ExecutionPattern = ExecutionPattern.SEQUENTIAL
    batch_progress: Optional[BatchProgress] = None
    data_input: Optional[Dict[str, Any]] = None
    data_output: Optional[Dict[str, Any]] = None
    rollback_data: Optional[Dict[str, Any]] = None


class WorkflowExecutionContext:
    """
    Extended execution context for deterministic workflows.

    Built on top of the existing analytics service to provide:
    - Step dependency management
    - Data flow tracking
    - Enhanced progress reporting
    - Rollback capabilities
    """

    def __init__(self):
        self.logger = ElevaiteLogger()
        self.analytics = analytics_service
        self._step_registry: Dict[str, Callable] = {}
        self._active_workflows: Dict[str, Dict[str, Any]] = {}

        # Register default step implementations
        self._register_default_steps()

    def _register_default_steps(self):
        """Register default step implementations."""
        try:
            from services.deterministic_steps import step_implementations

            # Register basic step implementations (bind methods to instance)
            self._step_registry["data_input"] = step_implementations.data_input_step
            self._step_registry["transformation"] = (
                step_implementations.transformation_step
            )
            self._step_registry["data_output"] = step_implementations.data_output_step
            self._step_registry["validation"] = step_implementations.validation_step
            self._step_registry["data_processing"] = (
                step_implementations.data_processing_step
            )

            self.logger.info("Registered default deterministic step implementations")
            
            # Register agent execution step
            try:
                from steps.agent_execution_step import create_agent_execution_step_direct
                self._step_registry["agent_execution"] = create_agent_execution_step_direct
                self.logger.info("Registered agent execution step")
            except ImportError as e:
                self.logger.warning(f"Could not import agent execution step: {e}")
            
            # Register tokenizer steps
            try:
                from services.tokenizer_steps_registry import tokenizer_steps_registry
                
                for step_type in tokenizer_steps_registry.list_available_steps():
                    implementation = tokenizer_steps_registry.get_step_implementation(step_type)
                    if implementation:
                        self._step_registry[step_type] = implementation
                
                self.logger.info(f"Registered tokenizer steps: {tokenizer_steps_registry.list_available_steps()}")
                
            except ImportError as e:
                self.logger.warning(f"Could not import tokenizer steps registry: {e}")

        except ImportError as e:
            self.logger.warning(f"Could not import default step implementations: {e}")

    def register_step_implementation(
        self, step_type: DeterministicStepType, implementation: Callable
    ) -> None:
        """Register a step implementation function"""
        self._step_registry[step_type.value] = implementation
        self.logger.info(f"Registered step implementation: {step_type}")

    def get_step_implementation(self, step_type: str) -> Optional[Callable]:
        """Get registered step implementation"""
        return self._step_registry.get(step_type)
    
    def get_step_implementation_with_config(self, step_type: str, step_config: Dict[str, Any]) -> Optional[Callable]:
        """Get step implementation, checking for tokenizer step configurations"""
        # Check if this step uses a tokenizer implementation
        step_config_dict = step_config.get("config", {})
        tokenizer_step = step_config_dict.get("tokenizer_step")
        
        if tokenizer_step:
            # Try to get tokenizer implementation
            try:
                from services.tokenizer_steps_registry import tokenizer_steps_registry
                tokenizer_impl = tokenizer_steps_registry.get_step_implementation(tokenizer_step)
                if tokenizer_impl:
                    self.logger.info(f"Using tokenizer implementation for step {step_config.get('step_id', 'unknown')}: {tokenizer_step}")
                    return tokenizer_impl
            except ImportError:
                self.logger.warning("Tokenizer steps registry not available")
        
        # Fall back to standard implementation
        return self._step_registry.get(step_type)

    @contextmanager
    def deterministic_workflow_execution(
        self,
        workflow_name: str,
        workflow_config: Dict[str, Any],
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        db: Optional[Session] = None,
    ):
        """
        Context manager for deterministic workflow execution.

        Extends the analytics service workflow tracking with:
        - Step dependency resolution
        - Data flow management
        - Enhanced error handling
        """
        workflow_id = workflow_config.get("workflow_id", str(uuid.uuid4()))

        # Initialize with analytics service - use deterministic execution type
        execution_id = self.analytics.create_execution(
            execution_type="deterministic",
            workflow_id=workflow_id,
            session_id=session_id,
            user_id=user_id,
            input_data={
                "workflow_type": "deterministic",
                "workflow_name": workflow_name,
                "config": workflow_config,
            },
        )

        # Initialize workflow trace for step tracking
        steps_config = workflow_config.get("steps", [])
        self.analytics.init_workflow_trace(
            execution_id=execution_id,
            workflow_id=workflow_id,
            total_steps=len(steps_config),
        )

        # Store workflow context
        self._active_workflows[execution_id] = {
            "workflow_name": workflow_name,
            "config": workflow_config,
            "step_dependencies": self._build_dependency_graph(steps_config),
            "step_data": {},  # Store data passed between steps
            "completed_steps": set(),
            "failed_steps": set(),
        }

        try:
            self.analytics.update_execution(
                execution_id=execution_id, status="running", db=db
            )

            yield execution_id

            # Mark as completed
            self.analytics.update_execution(
                execution_id=execution_id,
                status="completed",
                result=self._active_workflows[execution_id].get("step_data"),
                db=db,
            )

        except Exception as e:
            self.logger.error(f"Deterministic workflow {execution_id} failed: {e}")

            # Attempt rollback if configured
            try:
                asyncio.create_task(self._attempt_rollback(execution_id))
            except Exception as rollback_error:
                self.logger.error(f"Rollback failed: {rollback_error}")

            self.analytics.update_execution(
                execution_id=execution_id, status="failed", error=str(e), db=db
            )
            raise

        finally:
            # Cleanup
            if execution_id in self._active_workflows:
                del self._active_workflows[execution_id]

    async def execute_step(
        self,
        execution_id: str,
        step_config: Dict[str, Any],
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Execute a single deterministic workflow step.

        Handles:
        - Dependency checking
        - Data flow from previous steps
        - Progress tracking
        - Error handling with rollback support
        """
        if execution_id not in self._active_workflows:
            raise ValueError(f"Workflow execution {execution_id} not found")

        workflow_context = self._active_workflows[execution_id]
        step_id = step_config.get("step_id", str(uuid.uuid4()))
        step_type = step_config.get("step_type")
        step_name = step_config.get("step_name", step_id)

        # Check dependencies
        dependencies = step_config.get("dependencies", [])
        if not self._dependencies_satisfied(workflow_context, dependencies):
            raise ValueError(f"Dependencies not satisfied for step {step_id}")

        # Get input data from previous steps
        input_data = self._collect_step_input_data(workflow_context, step_config)

        # Start step tracking with analytics service
        workflow_step_id = self.analytics.track_workflow_step(
            execution_id=execution_id,
            step_type=step_type,
            step_name=step_name,
            input_data=input_data,
            step_metadata={
                "step_id": step_id,
                "dependencies": dependencies,
                "deterministic": True,
            },
        )

        try:
            # Get and execute step implementation
            implementation = self.get_step_implementation_with_config(step_type, step_config)
            if not implementation:
                raise ValueError(f"No implementation found for step type: {step_type}")

            # Execute the step
            result = await self._execute_step_with_progress(
                implementation=implementation,
                step_config=step_config,
                input_data=input_data,
                execution_id=execution_id,
                step_id=step_id,
            )

            # Store result for future steps
            workflow_context["step_data"][step_id] = result
            workflow_context["completed_steps"].add(step_id)

            # Complete step tracking
            self.analytics.complete_workflow_step(
                execution_id=execution_id,
                step_id=workflow_step_id,
                output_data=result,
                status="completed",
            )

            return result

        except Exception as e:
            workflow_context["failed_steps"].add(step_id)

            # Complete step tracking with error
            self.analytics.complete_workflow_step(
                execution_id=execution_id,
                step_id=workflow_step_id,
                error=str(e),
                status="failed",
            )

            # Store rollback information if available
            rollback_data = step_config.get("rollback")
            if rollback_data:
                workflow_context["rollback_data"] = workflow_context.get(
                    "rollback_data", {}
                )
                workflow_context["rollback_data"][step_id] = rollback_data

            raise

    async def execute_workflow(
        self,
        execution_id: str,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Execute all steps in a deterministic workflow according to their dependencies.

        Supports different execution patterns:
        - Sequential: Steps executed one after another
        - Parallel: Independent steps executed concurrently
        - DAG: Steps executed based on dependency graph
        """
        if execution_id not in self._active_workflows:
            raise ValueError(f"Workflow execution {execution_id} not found")

        workflow_context = self._active_workflows[execution_id]
        config = workflow_context["config"]
        steps = config.get("steps", [])
        execution_pattern = ExecutionPattern(
            config.get("execution_pattern", "sequential")
        )

        if execution_pattern == ExecutionPattern.SEQUENTIAL:
            return await self._execute_sequential(execution_id, steps, db)
        elif execution_pattern == ExecutionPattern.PARALLEL:
            return await self._execute_parallel(execution_id, steps, db)
        elif execution_pattern == ExecutionPattern.DAG:
            return await self._execute_dag(execution_id, steps, db)
        else:
            raise ValueError(f"Unsupported execution pattern: {execution_pattern}")

    async def _execute_sequential(
        self,
        execution_id: str,
        steps: List[Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Execute steps sequentially"""
        results = {}

        for step_config in steps:
            step_id = step_config.get("step_id")
            result = await self.execute_step(execution_id, step_config, db)
            results[step_id] = result

            # Update overall progress
            progress = len(results) / len(steps)
            self.analytics.update_execution(
                execution_id=execution_id,
                progress=progress,
                current_step=step_config.get("step_name", step_id),
            )

        return results

    async def _execute_parallel(
        self,
        execution_id: str,
        steps: List[Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Execute independent steps in parallel"""
        # Group steps by dependencies
        independent_steps = [s for s in steps if not s.get("dependencies")]
        dependent_steps = [s for s in steps if s.get("dependencies")]

        # Execute independent steps in parallel
        tasks = []
        for step_config in independent_steps:
            task = asyncio.create_task(self.execute_step(execution_id, step_config, db))
            tasks.append((step_config.get("step_id"), task))

        results = {}
        for step_id, task in tasks:
            results[step_id] = await task

        # Execute dependent steps sequentially
        for step_config in dependent_steps:
            step_id = step_config.get("step_id")
            results[step_id] = await self.execute_step(execution_id, step_config, db)

        return results

    async def _attempt_rollback(self, execution_id: str) -> None:
        """Attempt to rollback failed workflow steps"""
        if execution_id not in self._active_workflows:
            return

        workflow_context = self._active_workflows[execution_id]
        completed_steps = workflow_context.get("completed_steps", set())

        # Simple rollback - just log for now
        self.logger.info(
            f"Attempting rollback for {len(completed_steps)} completed steps"
        )

        # In a full implementation, this would call step-specific rollback methods
        for step_id in completed_steps:
            self.logger.info(f"Rolling back step: {step_id}")

    async def _execute_dag(
        self,
        execution_id: str,
        steps: List[Dict[str, Any]],
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Execute steps based on dependency graph (DAG)"""
        workflow_context = self._active_workflows[execution_id]
        dependency_graph = workflow_context["step_dependencies"]

        results = {}
        executed = set()

        while len(executed) < len(steps):
            # Find steps ready to execute (dependencies satisfied)
            ready_steps = []
            for step_config in steps:
                step_id = step_config.get("step_id")
                if step_id not in executed:
                    dependencies = dependency_graph.get(step_id, [])
                    if all(dep in executed for dep in dependencies):
                        ready_steps.append(step_config)

            if not ready_steps:
                remaining_steps = [
                    s.get("step_id") for s in steps if s.get("step_id") not in executed
                ]
                raise ValueError(
                    f"Circular dependency detected. Remaining steps: {remaining_steps}"
                )

            # Execute ready steps
            for step_config in ready_steps:
                step_id = step_config.get("step_id")
                results[step_id] = await self.execute_step(
                    execution_id, step_config, db
                )
                executed.add(step_id)

                # Update progress
                progress = len(executed) / len(steps)
                self.analytics.update_execution(
                    execution_id=execution_id,
                    progress=progress,
                    current_step=step_config.get("step_name", step_id),
                )

        return results

    async def _execute_step_with_progress(
        self,
        implementation: Callable,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_id: str,
        step_id: str,
    ) -> Dict[str, Any]:
        """Execute step implementation with progress tracking"""

        # Check if step supports batch processing
        batch_size = step_config.get("batch_size")
        if batch_size and isinstance(input_data.get("items"), list):
            return await self._execute_batch_step(
                implementation, step_config, input_data, execution_id, step_id
            )
        else:
            # Simple single execution
            execution_context = {
                "execution_id": execution_id,
                "step_id": step_id,
                "workflow_context": self._active_workflows.get(execution_id, {}),
            }
            return await implementation(step_config, input_data, execution_context)

    async def _execute_batch_step(
        self,
        implementation: Callable,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_id: str,
        step_id: str,
    ) -> Dict[str, Any]:
        """Execute step with batch processing and progress tracking"""
        items = input_data.get("items", [])
        batch_size = step_config.get("batch_size", 100)

        total_items = len(items)
        total_batches = (total_items + batch_size - 1) // batch_size

        results = []
        processed_items = 0
        successful_items = 0
        failed_items = 0

        for batch_index in range(total_batches):
            start_idx = batch_index * batch_size
            end_idx = min(start_idx + batch_size, total_items)
            batch_items = items[start_idx:end_idx]

            batch_input = input_data.copy()
            batch_input["items"] = batch_items
            batch_input["batch_index"] = batch_index
            batch_input["total_batches"] = total_batches

            try:
                batch_result = await implementation(step_config, batch_input)
                results.extend(batch_result.get("results", []))

                # Update counters
                batch_processed = len(batch_items)
                batch_successful = batch_result.get("successful_count", batch_processed)
                processed_items += batch_processed
                successful_items += batch_successful
                failed_items += batch_processed - batch_successful

            except Exception as e:
                self.logger.error(f"Batch {batch_index} failed: {e}")
                failed_items += len(batch_items)
                processed_items += len(batch_items)

            # Update progress in workflow step metadata
            progress_data = {
                "total_items": total_items,
                "processed_items": processed_items,
                "successful_items": successful_items,
                "failed_items": failed_items,
                "current_batch": batch_index + 1,
                "total_batches": total_batches,
                "progress_percentage": (processed_items / total_items) * 100,
            }

            # This would need to be added to analytics service to update step metadata
            # For now, log the progress
            self.logger.info(f"Step {step_id} progress: {progress_data}")

        return {
            "results": results,
            "total_items": total_items,
            "successful_items": successful_items,
            "failed_items": failed_items,
            "progress": progress_data,
        }

    def _build_dependency_graph(
        self, steps: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Build dependency graph from step configurations"""
        graph = {}
        for step in steps:
            step_id = step.get("step_id")
            dependencies = step.get("dependencies", [])
            graph[step_id] = dependencies
        return graph

    def _dependencies_satisfied(
        self, workflow_context: Dict[str, Any], dependencies: List[str]
    ) -> bool:
        """Check if all dependencies are satisfied"""
        completed_steps = workflow_context.get("completed_steps", set())
        return all(dep in completed_steps for dep in dependencies)

    def _collect_step_input_data(
        self, workflow_context: Dict[str, Any], step_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Collect input data from previous steps and step configuration"""
        step_data = workflow_context.get("step_data", {})
        input_mapping = step_config.get("input_mapping", {})

        # Start with step config input data or empty dict
        input_data = step_config.get("input_data", {}).copy()

        # If this is the first step and no previous step data exists, include initial workflow input
        if not step_data or step_config.get("step_order", 0) == 1:
            initial_input = step_data.get("input", {})
            if initial_input:
                input_data.update(initial_input)

        # Map data from previous steps
        for input_key, source_spec in input_mapping.items():
            if isinstance(source_spec, str) and "." in source_spec:
                # Format: "step_id.field_name"
                source_step, field_name = source_spec.split(".", 1)
                if source_step in step_data:
                    source_data = step_data[source_step]
                    if isinstance(source_data, dict) and field_name in source_data:
                        input_data[input_key] = source_data[field_name]
                    else:
                        input_data[input_key] = source_data
                else:
                    # Debug: Log missing source step
                    print(
                        f"🔍 Source step '{source_step}' not found in step_data. Available: {list(step_data.keys())}"
                    )
            elif isinstance(source_spec, str) and source_spec in step_data:
                # Direct step reference
                input_data[input_key] = step_data[source_spec]
            else:
                # Debug: Log mapping issue
                print(
                    f"🔍 Failed to map '{input_key}' from '{source_spec}'. Step data keys: {list(step_data.keys())}"
                )

        return input_data

    async def _attempt_rollback(self, execution_id: str) -> None:
        """Attempt to rollback failed workflow steps"""
        if execution_id not in self._active_workflows:
            return

        workflow_context = self._active_workflows[execution_id]
        rollback_data = workflow_context.get("rollback_data", {})
        completed_steps = workflow_context.get("completed_steps", set())

        # Rollback completed steps in reverse order
        for step_id in reversed(list(completed_steps)):
            if step_id in rollback_data:
                try:
                    rollback_config = rollback_data[step_id]
                    rollback_impl = self.get_step_implementation(
                        rollback_config.get("rollback_type")
                    )

                    if rollback_impl:
                        await rollback_impl(
                            rollback_config, workflow_context["step_data"].get(step_id)
                        )
                        self.logger.info(f"Successfully rolled back step: {step_id}")

                except Exception as e:
                    self.logger.error(f"Failed to rollback step {step_id}: {e}")


# Global instance
workflow_execution_context = WorkflowExecutionContext()
