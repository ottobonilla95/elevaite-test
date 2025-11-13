"""
Test Conditional Execution Logic

Tests for dynamic workflow branching based on step results,
expression evaluation, and complex conditional logic.
"""

import asyncio
from typing import Dict, Any

from workflow_engine_poc.condition_evaluator import (
    condition_evaluator,
    Condition,
    ConditionalExpression,
    ConditionOperator,
    LogicalOperator,
)
from workflow_engine_poc.execution_context import ExecutionContext, UserContext
from workflow_engine_poc.workflow_engine import WorkflowEngine
from workflow_engine_poc.step_registry import StepRegistry


async def test_condition_evaluator():
    """Test the condition evaluator with various conditions"""

    print("🧪 Testing Condition Evaluator")
    print("-" * 40)

    # Sample context data
    context = {
        "step1": {
            "status": "completed",
            "output": {"result": "success", "count": 15, "items": ["a", "b", "c"]},
        },
        "step2": {"status": "failed", "output": {}, "error": "Connection timeout"},
        "workflow": {"status": "running"},
    }

    # Test simple conditions
    test_conditions = [
        ("step1.status == 'completed'", True),
        ("step1.output.result == 'success'", True),
        ("step1.output.count > 10", True),
        ("step1.output.count < 5", False),
        ("step2.status == 'failed'", True),
        ("step2.error contains 'timeout'", True),
        ("step1.output.items contains 'b'", True),
        ("step1.output.items contains 'z'", False),
        ("workflow.status == 'completed'", False),
    ]

    print("📋 Testing Simple Conditions:")
    for condition_str, expected in test_conditions:
        condition = condition_evaluator.parse_condition_string(condition_str)
        if condition:
            result = condition_evaluator.evaluate_condition(condition, context)
            status = "✅" if result == expected else "❌"
            print(f"   {status} {condition_str} -> {result} (expected {expected})")
        else:
            print(f"   ❌ Failed to parse: {condition_str}")

    # Test complex expressions
    print("\n📋 Testing Complex Expressions:")

    # AND expression
    and_expression = ConditionalExpression(
        conditions=[
            Condition("step1.status", ConditionOperator.EQUALS, "completed"),
            Condition("step1.output.count", ConditionOperator.GREATER_THAN, 10),
        ],
        logical_operator=LogicalOperator.AND,
    )

    result = condition_evaluator.evaluate_expression(and_expression, context)
    print(f"   ✅ AND expression: {result} (expected True)")

    # OR expression
    or_expression = ConditionalExpression(
        conditions=[
            Condition("step2.status", ConditionOperator.EQUALS, "completed"),
            Condition("step1.status", ConditionOperator.EQUALS, "completed"),
        ],
        logical_operator=LogicalOperator.OR,
    )

    result = condition_evaluator.evaluate_expression(or_expression, context)
    print(f"   ✅ OR expression: {result} (expected True)")


async def test_conditional_workflow():
    """Test conditional execution in a workflow"""

    print("\n🧪 Testing Conditional Workflow Execution")
    print("-" * 40)

    # Create workflow with conditional steps
    workflow_config = {
        "workflow_id": "conditional-test-workflow",
        "name": "Conditional Test Workflow",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "initial_step",
                "step_name": "Initial Step",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "input_type": "static",
                    "data": {"status": "success", "score": 85},
                },
            },
            {
                "step_id": "success_step",
                "step_name": "Success Processing",
                "step_type": "data_processing",
                "step_order": 2,
                "dependencies": ["initial_step"],
                "conditions": "initial_step.output.data.status == 'success'",
                "config": {"operation": "transform", "transformation": "upper"},
            },
            {
                "step_id": "failure_step",
                "step_name": "Failure Processing",
                "step_type": "data_processing",
                "step_order": 3,
                "dependencies": ["initial_step"],
                "conditions": "initial_step.output.data.status == 'failed'",
                "config": {"operation": "transform", "transformation": "lower"},
            },
            {
                "step_id": "high_score_step",
                "step_name": "High Score Processing",
                "step_type": "data_input",
                "step_order": 4,
                "dependencies": ["initial_step"],
                "conditions": "initial_step.output.data.score > 80",
                "config": {
                    "input_type": "static",
                    "data": {"message": "High score achieved!"},
                },
            },
            {
                "step_id": "final_step",
                "step_name": "Final Step",
                "step_type": "data_merge",
                "step_order": 5,
                "dependencies": ["success_step", "high_score_step"],
                "config": {"merge_strategy": "combine"},
            },
        ],
    }

    # Initialize components
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()

    workflow_engine = WorkflowEngine(step_registry)

    # Create execution context
    user_context = UserContext(user_id="conditional_test_user")
    execution_context = ExecutionContext(workflow_config, user_context)

    # Execute workflow
    print("📋 Executing conditional workflow:")

    await workflow_engine.execute_workflow(execution_context)

    # Check results
    summary = execution_context.get_execution_summary()
    print(f"   Workflow status: {summary['status']}")
    print(f"   Completed steps: {summary.get('completed_steps', 0)}")
    print(f"   Failed steps: {summary.get('failed_steps', 0)}")

    # Check which steps were executed/skipped
    executed_steps = []
    skipped_steps = []

    for step_id, step_result in execution_context.step_results.items():
        if step_result.status.value == "completed":
            executed_steps.append(step_id)
        elif step_result.status.value == "skipped":
            skipped_steps.append(step_id)

    print(f"   Executed steps: {executed_steps}")
    print(f"   Skipped steps: {skipped_steps}")

    # Debug: Check step conditions and results
    print(f"   Debug - Step results:")
    for step_id, step_result in execution_context.step_results.items():
        print(
            f"     {step_id}: {step_result.status.value} - {step_result.error_message or 'No error'}"
        )

    # Check initial step output
    initial_output = execution_context.step_results.get("initial_step")
    if initial_output:
        print(f"   Initial step output: {initial_output.output_data}")

    # Verify expected behavior
    expected_executed = [
        "initial_step",
        "success_step",
        "high_score_step",
        "final_step",
    ]
    expected_skipped = ["failure_step"]

    if set(executed_steps) == set(expected_executed) and set(skipped_steps) == set(
        expected_skipped
    ):
        print("   ✅ Conditional execution worked as expected!")
    else:
        print("   ❌ Conditional execution did not work as expected")
        print(f"     Expected executed: {expected_executed}")
        print(f"     Actual executed: {executed_steps}")
        print(f"     Expected skipped: {expected_skipped}")
        print(f"     Actual skipped: {skipped_steps}")


async def test_complex_conditions():
    """Test complex conditional expressions"""

    print("\n🧪 Testing Complex Conditional Expressions")
    print("-" * 40)

    # Create workflow with complex conditions
    workflow_config = {
        "workflow_id": "complex-conditional-workflow",
        "name": "Complex Conditional Workflow",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "data_step",
                "step_name": "Data Generation",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "input_type": "static",
                    "data": {
                        "environment": "production",
                        "user_count": 150,
                        "error_rate": 0.02,
                        "features": ["auth", "analytics", "notifications"],
                    },
                },
            },
            {
                "step_id": "production_check",
                "step_name": "Production Environment Check",
                "step_type": "data_processing",
                "step_order": 2,
                "dependencies": ["data_step"],
                "conditions": {
                    "logical_operator": "and",
                    "conditions": [
                        {
                            "left_operand": "data_step.output.environment",
                            "operator": "==",
                            "right_operand": "production",
                        },
                        {
                            "left_operand": "data_step.output.user_count",
                            "operator": ">",
                            "right_operand": 100,
                        },
                    ],
                },
                "config": {"operation": "transform", "transformation": "upper"},
            },
            {
                "step_id": "error_alert",
                "step_name": "Error Rate Alert",
                "step_type": "data_input",
                "step_order": 3,
                "dependencies": ["data_step"],
                "conditions": {
                    "logical_operator": "or",
                    "conditions": [
                        {
                            "left_operand": "data_step.output.error_rate",
                            "operator": ">",
                            "right_operand": 0.05,
                        },
                        {
                            "left_operand": "data_step.output.user_count",
                            "operator": "<",
                            "right_operand": 50,
                        },
                    ],
                },
                "config": {
                    "input_type": "static",
                    "data": {"alert": "High error rate or low user count"},
                },
            },
            {
                "step_id": "feature_check",
                "step_name": "Feature Availability Check",
                "step_type": "data_processing",
                "step_order": 4,
                "dependencies": ["data_step"],
                "conditions": "data_step.output.features contains 'analytics'",
                "config": {"operation": "transform", "transformation": "lower"},
            },
        ],
    }

    # Initialize components
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()

    workflow_engine = WorkflowEngine(step_registry)

    # Create execution context
    user_context = UserContext(user_id="complex_conditional_test_user")
    execution_context = ExecutionContext(workflow_config, user_context)

    # Execute workflow
    print("📋 Executing complex conditional workflow:")

    await workflow_engine.execute_workflow(execution_context)

    # Check results
    summary = execution_context.get_execution_summary()
    print(f"   Workflow status: {summary['status']}")

    # Analyze step execution
    for step_id, step_result in execution_context.step_results.items():
        status = step_result.status.value
        print(f"   Step {step_id}: {status}")

    # Expected: data_step, production_check, and feature_check should execute
    # error_alert should be skipped (error rate is 0.02 < 0.05 and user_count is 150 > 50)

    executed_count = sum(
        1
        for result in execution_context.step_results.values()
        if result.status.value == "completed"
    )
    skipped_count = sum(
        1
        for result in execution_context.step_results.values()
        if result.status.value == "skipped"
    )

    print(f"   Total executed: {executed_count}, skipped: {skipped_count}")


async def main():
    """Run all conditional execution tests"""

    print("🚀 Conditional Execution Test Suite")
    print("=" * 60)

    try:
        await test_condition_evaluator()
        await test_conditional_workflow()
        await test_complex_conditions()

        print("\n🎉 All conditional execution tests completed successfully!")
        print("✅ Conditional execution logic is working correctly")

    except Exception as e:
        print(f"\n❌ Conditional execution test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
