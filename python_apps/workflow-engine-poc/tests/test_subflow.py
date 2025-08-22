"""
Test subflow functionality for nested workflow execution
"""

import pytest
import asyncio
from datetime import datetime

from workflow_engine_poc.workflow_engine import WorkflowEngine
from workflow_engine_poc.step_registry import StepRegistry
from workflow_engine_poc.execution_context import ExecutionContext, UserContext
from workflow_engine_poc.database import get_database
from workflow_engine_poc.models import (
    EXAMPLE_SUBFLOW_CHILD,
    EXAMPLE_SUBFLOW_PARENT,
    WorkflowConfig,
)


@pytest.fixture
async def setup_subflow_test():
    """Setup test environment with subflow workflows"""
    # Initialize database
    database = await get_database()

    # Initialize step registry
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()

    # Initialize workflow engine
    workflow_engine = WorkflowEngine(step_registry)

    # Save the child subflow workflow to database
    child_workflow_id = await database.save_workflow(
        EXAMPLE_SUBFLOW_CHILD["workflow_id"], EXAMPLE_SUBFLOW_CHILD
    )

    # Save the parent workflow to database
    parent_workflow_id = await database.save_workflow(
        EXAMPLE_SUBFLOW_PARENT["workflow_id"], EXAMPLE_SUBFLOW_PARENT
    )

    return {
        "database": database,
        "step_registry": step_registry,
        "workflow_engine": workflow_engine,
        "child_workflow_id": child_workflow_id,
        "parent_workflow_id": parent_workflow_id,
    }


@pytest.mark.asyncio
async def test_subflow_basic_execution(setup_subflow_test):
    """Test basic subflow execution"""
    setup = await setup_subflow_test
    workflow_engine = setup["workflow_engine"]

    # Create user context
    user_context = UserContext(
        user_id="test_user",
        session_id="test_session",
        organization_id="test_org",
    )

    # Create execution context for parent workflow
    execution_context = ExecutionContext(
        workflow_config=EXAMPLE_SUBFLOW_PARENT,
        user_context=user_context,
        workflow_engine=workflow_engine,
    )

    # Execute the workflow
    completed_context = await workflow_engine.execute_workflow(execution_context)

    # Verify execution completed successfully
    assert completed_context.status.value == "completed"
    assert len(completed_context.completed_steps) > 0

    # Verify subflow steps were executed
    assert "process_title" in completed_context.completed_steps
    assert "process_content" in completed_context.completed_steps
    assert "combine_results" in completed_context.completed_steps

    # Verify subflow results are available
    assert "process_title" in completed_context.step_io_data
    assert "process_content" in completed_context.step_io_data

    # Check that subflow execution data is present
    title_result = completed_context.step_io_data.get("process_title", {})
    assert "subflow_id" in title_result
    assert "subflow_execution_id" in title_result
    assert "subflow_status" in title_result
    assert title_result.get("success") is True


@pytest.mark.asyncio
async def test_subflow_input_output_mapping(setup_subflow_test):
    """Test subflow input and output mapping"""
    setup = await setup_subflow_test
    workflow_engine = setup["workflow_engine"]

    # Create a simple test workflow that uses subflow with specific mappings
    test_workflow = {
        "workflow_id": "test-subflow-mapping",
        "name": "Test Subflow Mapping",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "setup_data",
                "step_name": "Setup Test Data",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "input_type": "static",
                    "data": {"test_text": "hello world"},
                },
            },
            {
                "step_id": "call_subflow",
                "step_name": "Call Text Processing Subflow",
                "step_type": "subflow",
                "step_order": 2,
                "dependencies": ["setup_data"],
                "config": {
                    "workflow_id": "text-processing-subflow",
                    "input_mapping": {"text": "setup_data.data.test_text"},
                    "output_mapping": {"final_result": "add_metadata.result"},
                    "inherit_context": True,
                },
            },
        ],
    }

    # Create user context
    user_context = UserContext(
        user_id="test_user",
        session_id="test_session",
        organization_id="test_org",
    )

    # Create execution context
    execution_context = ExecutionContext(
        workflow_config=test_workflow,
        user_context=user_context,
        workflow_engine=workflow_engine,
    )

    # Execute the workflow
    completed_context = await workflow_engine.execute_workflow(execution_context)

    # Verify execution completed successfully
    assert completed_context.status.value == "completed"

    # Verify input mapping worked - subflow should have received the mapped input
    subflow_result = completed_context.step_io_data.get("call_subflow", {})
    assert subflow_result.get("success") is True

    # Verify output mapping worked - should have the mapped output
    assert "subflow_output" in subflow_result
    subflow_output = subflow_result["subflow_output"]
    assert "final_result" in subflow_output


@pytest.mark.asyncio
async def test_subflow_isolation(setup_subflow_test):
    """Test subflow execution isolation"""
    setup = await setup_subflow_test
    workflow_engine = setup["workflow_engine"]

    # Create a test workflow with isolated subflow
    test_workflow = {
        "workflow_id": "test-subflow-isolation",
        "name": "Test Subflow Isolation",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "setup_data",
                "step_name": "Setup Test Data",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "input_type": "static",
                    "data": {"test_text": "isolation test"},
                },
            },
            {
                "step_id": "isolated_subflow",
                "step_name": "Isolated Subflow",
                "step_type": "subflow",
                "step_order": 2,
                "dependencies": ["setup_data"],
                "config": {
                    "workflow_id": "text-processing-subflow",
                    "input_mapping": {"text": "setup_data.data.test_text"},
                    "inherit_context": False,  # Test isolation
                },
            },
        ],
    }

    # Create user context
    user_context = UserContext(
        user_id="test_user",
        session_id="test_session",
        organization_id="test_org",
    )

    # Create execution context
    execution_context = ExecutionContext(
        workflow_config=test_workflow,
        user_context=user_context,
        workflow_engine=workflow_engine,
    )

    # Execute the workflow
    completed_context = await workflow_engine.execute_workflow(execution_context)

    # Verify execution completed successfully
    assert completed_context.status.value == "completed"

    # Verify subflow executed with isolation
    subflow_result = completed_context.step_io_data.get("isolated_subflow", {})
    assert subflow_result.get("success") is True

    # The subflow should have a different execution ID
    parent_execution_id = completed_context.execution_id
    subflow_execution_id = subflow_result.get("subflow_execution_id")
    assert subflow_execution_id != parent_execution_id


@pytest.mark.asyncio
async def test_subflow_error_handling(setup_subflow_test):
    """Test subflow error handling"""
    setup = await setup_subflow_test
    workflow_engine = setup["workflow_engine"]

    # Create a test workflow that references a non-existent subflow
    test_workflow = {
        "workflow_id": "test-subflow-error",
        "name": "Test Subflow Error Handling",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "setup_data",
                "step_name": "Setup Test Data",
                "step_type": "data_input",
                "step_order": 1,
                "config": {"input_type": "static", "data": {"test": "data"}},
            },
            {
                "step_id": "bad_subflow",
                "step_name": "Non-existent Subflow",
                "step_type": "subflow",
                "step_order": 2,
                "dependencies": ["setup_data"],
                "config": {"workflow_id": "non-existent-workflow"},
            },
        ],
    }

    # Create user context
    user_context = UserContext(
        user_id="test_user",
        session_id="test_session",
        organization_id="test_org",
    )

    # Create execution context
    execution_context = ExecutionContext(
        workflow_config=test_workflow,
        user_context=user_context,
        workflow_engine=workflow_engine,
    )

    # Execute the workflow - should handle the error gracefully
    completed_context = await workflow_engine.execute_workflow(execution_context)

    # Verify execution completed (the step executed successfully but subflow failed)
    assert completed_context.status.value == "completed"

    # Verify error information is captured in the subflow result
    subflow_result = completed_context.step_io_data.get("bad_subflow", {})
    assert subflow_result.get("success") is False
    assert "error" in subflow_result
    assert "non-existent-workflow" in subflow_result.get("error", "")
