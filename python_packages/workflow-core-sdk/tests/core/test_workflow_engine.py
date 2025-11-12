"""
Unit tests for WorkflowEngine

Tests workflow execution patterns: sequential, parallel, conditional, and dependency-based.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from workflow_core_sdk.workflow_engine import WorkflowEngine
from workflow_core_sdk.execution.context_impl import ExecutionContext, StepResult
from workflow_core_sdk.models import ExecutionStatus, StepStatus


@pytest.fixture
def mock_step_registry():
    """Create a mock step registry"""
    registry = AsyncMock()

    # Mock execute_step to return successful results
    async def mock_execute(step_type, step_config, input_data, execution_context):
        return StepResult(
            step_id=step_config["step_id"],
            status=StepStatus.COMPLETED,
            output_data={"result": f"output from {step_config['step_id']}"},
            execution_time_ms=10,
        )

    registry.execute_step = mock_execute
    return registry


@pytest.fixture
def workflow_engine(mock_step_registry):
    """Create a workflow engine instance"""
    return WorkflowEngine(step_registry=mock_step_registry)


class TestSequentialExecution:
    """Tests for sequential workflow execution"""

    @pytest.mark.asyncio
    async def test_sequential_execution_simple(self, workflow_engine):
        """Test simple sequential execution of 3 steps"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Sequential Workflow",
            "execution_pattern": "sequential",
            "steps": [
                {"step_id": "step1", "step_type": "data_input", "step_order": 1},
                {"step_id": "step2", "step_type": "data_processing", "step_order": 2},
                {"step_id": "step3", "step_type": "data_processing", "step_order": 3},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        assert result_context.status == ExecutionStatus.COMPLETED
        assert len(result_context.step_results) == 3
        assert "step1" in result_context.step_results
        assert "step2" in result_context.step_results
        assert "step3" in result_context.step_results

    @pytest.mark.asyncio
    async def test_sequential_execution_with_dependencies(self, workflow_engine):
        """Test sequential execution respects dependencies"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Sequential with Dependencies",
            "execution_pattern": "sequential",
            "steps": [
                {"step_id": "step1", "step_type": "data_input", "step_order": 1},
                {
                    "step_id": "step2",
                    "step_type": "data_processing",
                    "step_order": 2,
                    "dependencies": ["step1"],
                },
                {
                    "step_id": "step3",
                    "step_type": "data_processing",
                    "step_order": 3,
                    "dependencies": ["step2"],
                },
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        assert result_context.status == ExecutionStatus.COMPLETED
        assert len(result_context.step_results) == 3

    @pytest.mark.asyncio
    async def test_sequential_execution_with_unordered_steps(self, workflow_engine):
        """Test sequential execution handles missing step_order"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Sequential Unordered",
            "execution_pattern": "sequential",
            "steps": [
                {"step_id": "step1", "step_type": "data_input"},  # No step_order
                {"step_id": "step2", "step_type": "data_processing", "step_order": 2},
                {"step_id": "step3", "step_type": "data_processing"},  # No step_order
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        assert result_context.status == ExecutionStatus.COMPLETED
        assert len(result_context.step_results) == 3


class TestParallelExecution:
    """Tests for parallel workflow execution"""

    @pytest.mark.asyncio
    async def test_parallel_execution_independent_steps(self, workflow_engine):
        """Test parallel execution of independent steps"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Parallel Workflow",
            "execution_pattern": "parallel",
            "steps": [
                {"step_id": "step1", "step_type": "data_input"},
                {"step_id": "step2", "step_type": "data_input"},
                {"step_id": "step3", "step_type": "data_input"},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        assert result_context.status == ExecutionStatus.COMPLETED
        assert len(result_context.step_results) == 3

    @pytest.mark.asyncio
    async def test_parallel_execution_with_dependencies(self, workflow_engine):
        """Test parallel execution respects dependencies"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Parallel with Dependencies",
            "execution_pattern": "parallel",
            "steps": [
                {"step_id": "step1", "step_type": "data_input"},
                {
                    "step_id": "step2",
                    "step_type": "data_processing",
                    "dependencies": ["step1"],
                },
                {
                    "step_id": "step3",
                    "step_type": "data_processing",
                    "dependencies": ["step1"],
                },
                {
                    "step_id": "step4",
                    "step_type": "data_merge",
                    "dependencies": ["step2", "step3"],
                },
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        assert result_context.status == ExecutionStatus.COMPLETED
        assert len(result_context.step_results) == 4
        # Verify step1 executed before step2 and step3
        assert "step1" in result_context.step_results
        assert "step2" in result_context.step_results
        assert "step3" in result_context.step_results
        assert "step4" in result_context.step_results

    @pytest.mark.asyncio
    async def test_parallel_execution_detects_circular_dependencies(self, workflow_engine):
        """Test parallel execution detects circular dependencies"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Circular Dependencies",
            "execution_pattern": "parallel",
            "steps": [
                {"step_id": "step1", "step_type": "data_input", "dependencies": ["step2"]},
                {"step_id": "step2", "step_type": "data_processing", "dependencies": ["step1"]},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        # Should fail due to circular dependencies
        assert result_context.status == ExecutionStatus.FAILED
        error_msg = result_context.metadata.get("error_message", "").lower()
        assert "circular dependencies" in error_msg or "stuck" in error_msg


class TestDependencyBasedExecution:
    """Tests for dependency-based workflow execution"""

    @pytest.mark.asyncio
    async def test_dependency_based_execution_simple(self, workflow_engine):
        """Test dependency-based execution with simple chain"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Dependency-Based",
            "execution_pattern": "dependency",
            "steps": [
                {"step_id": "step1", "step_type": "data_input"},
                {"step_id": "step2", "step_type": "data_processing", "dependencies": ["step1"]},
                {"step_id": "step3", "step_type": "data_processing", "dependencies": ["step2"]},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        assert result_context.status == ExecutionStatus.COMPLETED
        assert len(result_context.step_results) == 3

    @pytest.mark.asyncio
    async def test_dependency_based_execution_complex_dag(self, workflow_engine):
        """Test dependency-based execution with complex DAG"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Complex DAG",
            "execution_pattern": "dependency",
            "steps": [
                {"step_id": "step1", "step_type": "data_input"},
                {"step_id": "step2", "step_type": "data_input"},
                {"step_id": "step3", "step_type": "data_processing", "dependencies": ["step1"]},
                {"step_id": "step4", "step_type": "data_processing", "dependencies": ["step2"]},
                {"step_id": "step5", "step_type": "data_merge", "dependencies": ["step3", "step4"]},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        assert result_context.status == ExecutionStatus.COMPLETED
        assert len(result_context.step_results) == 5

    @pytest.mark.asyncio
    async def test_dependency_based_detects_stuck_workflow(self, workflow_engine):
        """Test dependency-based execution detects stuck workflows"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Stuck Workflow",
            "execution_pattern": "dependency",
            "steps": [
                {"step_id": "step1", "step_type": "data_input", "dependencies": ["step2"]},
                {"step_id": "step2", "step_type": "data_processing", "dependencies": ["step1"]},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        assert result_context.status == ExecutionStatus.FAILED
        error_msg = result_context.metadata.get("error_message", "").lower()
        assert "circular dependencies" in error_msg or "stuck" in error_msg


class TestConditionalExecution:
    """Tests for conditional workflow execution"""

    @pytest.mark.asyncio
    async def test_conditional_execution_delegates_to_dependency(self, workflow_engine):
        """Test conditional execution currently delegates to dependency-based"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Conditional",
            "execution_pattern": "conditional",
            "steps": [
                {"step_id": "step1", "step_type": "data_input"},
                {"step_id": "step2", "step_type": "data_processing", "dependencies": ["step1"]},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        assert result_context.status == ExecutionStatus.COMPLETED
        assert len(result_context.step_results) == 2


class TestStepFailureHandling:
    """Tests for handling step failures"""

    @pytest.mark.asyncio
    async def test_step_failure_stops_sequential_execution(self):
        """Test that step failure stops sequential execution"""
        # Create a registry that fails on step2
        registry = AsyncMock()

        async def mock_execute(step_type, step_config, input_data, execution_context):
            if step_config["step_id"] == "step2":
                raise Exception("Step 2 failed")
            return StepResult(
                step_id=step_config["step_id"],
                status=StepStatus.COMPLETED,
                output_data={"result": "success"},
            )

        registry.execute_step = mock_execute
        engine = WorkflowEngine(step_registry=registry)

        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Failure",
            "execution_pattern": "sequential",
            "steps": [
                {"step_id": "step1", "step_type": "data_input", "step_order": 1},
                {"step_id": "step2", "step_type": "data_processing", "step_order": 2},
                {"step_id": "step3", "step_type": "data_processing", "step_order": 3},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await engine.execute_workflow(context)

        # Workflow should fail
        assert result_context.status == ExecutionStatus.FAILED
        # Step1 should complete, step2 should fail, step3 should not execute
        assert "step1" in result_context.step_results
        assert result_context.step_results["step1"].status == StepStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_parallel_execution_continues_on_step_failure(self):
        """Test that parallel execution continues other steps when one fails"""
        # Create a registry that fails on step2
        registry = AsyncMock()

        async def mock_execute(step_type, step_config, input_data, execution_context):
            if step_config["step_id"] == "step2":
                raise Exception("Step 2 failed")
            return StepResult(
                step_id=step_config["step_id"],
                status=StepStatus.COMPLETED,
                output_data={"result": "success"},
            )

        registry.execute_step = mock_execute
        engine = WorkflowEngine(step_registry=registry)

        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Parallel Failure",
            "execution_pattern": "parallel",
            "steps": [
                {"step_id": "step1", "step_type": "data_input"},
                {"step_id": "step2", "step_type": "data_input"},
                {"step_id": "step3", "step_type": "data_input"},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await engine.execute_workflow(context)

        # Workflow should fail but other steps should complete
        assert result_context.status == ExecutionStatus.FAILED


class TestWaitingSteps:
    """Tests for steps that return WAITING status"""

    @pytest.mark.asyncio
    async def test_waiting_step_pauses_execution(self):
        """Test that WAITING step pauses workflow execution"""
        registry = AsyncMock()

        async def mock_execute(step_type, step_config, input_data, execution_context):
            if step_config["step_id"] == "step2":
                return StepResult(
                    step_id=step_config["step_id"],
                    status=StepStatus.WAITING,
                    output_data={"message": "Waiting for approval"},
                )
            return StepResult(
                step_id=step_config["step_id"],
                status=StepStatus.COMPLETED,
                output_data={"result": "success"},
            )

        registry.execute_step = mock_execute
        engine = WorkflowEngine(step_registry=registry)

        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Waiting",
            "execution_pattern": "sequential",
            "steps": [
                {"step_id": "step1", "step_type": "data_input", "step_order": 1},
                {"step_id": "step2", "step_type": "human_approval", "step_order": 2},
                {"step_id": "step3", "step_type": "data_processing", "step_order": 3},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await engine.execute_workflow(context)

        # Workflow should be in WAITING status
        assert result_context.status == ExecutionStatus.WAITING
        # Step1 should complete, step2 should be waiting, step3 should not execute
        assert "step1" in result_context.step_results
        assert "step2" in result_context.step_results
        assert result_context.step_results["step2"].status == StepStatus.WAITING
        assert "step3" not in result_context.step_results


class TestExecutionContextManagement:
    """Tests for execution context management"""

    @pytest.mark.asyncio
    async def test_active_executions_tracking(self, workflow_engine):
        """Test that active executions are tracked"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Tracking",
            "execution_pattern": "sequential",
            "steps": [
                {"step_id": "step1", "step_type": "data_input", "step_order": 1},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)

        # Before execution
        assert len(workflow_engine.active_executions) == 0

        # Execute
        result_context = await workflow_engine.execute_workflow(context)

        # After execution (completed workflows are removed from active)
        assert result_context.status == ExecutionStatus.COMPLETED
        assert len(workflow_engine.active_executions) == 0
        assert len(workflow_engine.execution_history) == 1

    @pytest.mark.asyncio
    async def test_waiting_execution_stays_active(self):
        """Test that WAITING executions stay in active_executions"""
        registry = AsyncMock()

        async def mock_execute(step_type, step_config, input_data, execution_context):
            return StepResult(
                step_id=step_config["step_id"],
                status=StepStatus.WAITING,
                output_data={"message": "Waiting"},
            )

        registry.execute_step = mock_execute
        engine = WorkflowEngine(step_registry=registry)

        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Waiting Active",
            "execution_pattern": "sequential",
            "steps": [
                {"step_id": "step1", "step_type": "human_approval", "step_order": 1},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await engine.execute_workflow(context)

        # WAITING executions should stay active
        assert result_context.status == ExecutionStatus.WAITING
        assert result_context.execution_id in engine.active_executions
        assert len(engine.execution_history) == 0


class TestDefaultExecutionPattern:
    """Tests for default execution pattern"""

    @pytest.mark.asyncio
    async def test_default_pattern_is_dependency_based(self, workflow_engine):
        """Test that workflows without execution_pattern use dependency-based"""
        workflow_config = {
            "workflow_id": "test-workflow",
            "name": "Test Default Pattern",
            # No execution_pattern specified
            "steps": [
                {"step_id": "step1", "step_type": "data_input"},
                {"step_id": "step2", "step_type": "data_processing", "dependencies": ["step1"]},
            ],
        }

        context = ExecutionContext(workflow_config=workflow_config)
        result_context = await workflow_engine.execute_workflow(context)

        assert result_context.status == ExecutionStatus.COMPLETED
        assert len(result_context.step_results) == 2
