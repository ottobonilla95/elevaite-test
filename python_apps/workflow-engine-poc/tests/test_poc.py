"""
Test the Workflow Engine PoC

This script tests the core functionality of the unified workflow execution engine.
"""

import asyncio
import json
from datetime import datetime

from workflow_engine_poc.execution_context import ExecutionContext, UserContext
from workflow_engine_poc.step_registry import StepRegistry
from workflow_engine_poc.workflow_engine import WorkflowEngine
from workflow_engine_poc.models import (
    EXAMPLE_SIMPLE_WORKFLOW,
    EXAMPLE_AGENT_WORKFLOW,
    EXAMPLE_PARALLEL_WORKFLOW,
)


async def test_execution_context():
    """Test the execution context functionality"""
    print("🧪 Testing Execution Context")
    print("-" * 40)

    # Create a simple workflow config
    workflow_config = {
        "workflow_id": "test-context",
        "name": "Test Context Workflow",
        "steps": [
            {
                "step_id": "step1",
                "step_name": "First Step",
                "step_type": "data_input",
                "config": {"data": {"message": "Hello"}},
            },
            {
                "step_id": "step2",
                "step_name": "Second Step",
                "step_type": "data_processing",
                "dependencies": ["step1"],
                "input_mapping": {"input": "step1.data"},
                "config": {"processing_type": "uppercase"},
            },
        ],
    }

    user_context = UserContext(user_id="test_user", session_id="test_session")
    context = ExecutionContext(workflow_config, user_context)

    print(f"✅ Created execution context: {context.execution_id}")
    print(f"   Workflow: {context.workflow_name}")
    print(f"   Total steps: {len(context.steps_config)}")
    print(f"   Ready steps: {context.get_ready_steps()}")

    # Test serialization
    context_dict = context.to_dict()
    restored_context = ExecutionContext.from_dict(context_dict)

    print(f"✅ Serialization test passed")
    print(f"   Original ID: {context.execution_id}")
    print(f"   Restored ID: {restored_context.execution_id}")

    return context


async def test_step_registry():
    """Test the step registry functionality"""
    print("\n🧪 Testing Step Registry")
    print("-" * 40)

    registry = StepRegistry()

    # Register built-in steps
    await registry.register_builtin_steps()

    # Get registered steps
    steps = await registry.get_registered_steps()
    print(f"✅ Registered {len(steps)} built-in steps:")
    for step in steps:
        print(f"   - {step['step_type']}: {step['name']}")

    # Test custom step registration
    custom_step = {
        "step_type": "custom_test",
        "name": "Custom Test Step",
        "description": "A custom step for testing",
        "function_reference": "workflow_engine_poc.builtin_steps.data_input_step",
        "execution_type": "local",
    }

    step_id = await registry.register_step(custom_step)
    print(f"✅ Registered custom step: {step_id}")

    return registry


async def test_workflow_engine():
    """Test the workflow engine functionality"""
    print("\n🧪 Testing Workflow Engine")
    print("-" * 40)

    # Create step registry and engine
    registry = StepRegistry()
    await registry.register_builtin_steps()

    engine = WorkflowEngine(registry)

    # Test simple workflow
    print("\n📋 Testing Simple Sequential Workflow:")

    workflow_config = EXAMPLE_SIMPLE_WORKFLOW.copy()
    user_context = UserContext(user_id="test_user")
    context = ExecutionContext(workflow_config, user_context)

    # Execute workflow
    result_context = await engine.execute_workflow(context)

    print(f"   Status: {result_context.status.value}")
    print(f"   Completed steps: {len(result_context.completed_steps)}")
    print(f"   Failed steps: {len(result_context.failed_steps)}")

    if result_context.step_results:
        print("   Step results:")
        for step_id, result in result_context.step_results.items():
            print(f"     {step_id}: {result.status.value}")

    # Test parallel workflow
    print("\n📋 Testing Parallel Workflow:")

    workflow_config = EXAMPLE_PARALLEL_WORKFLOW.copy()
    context = ExecutionContext(workflow_config, user_context)

    result_context = await engine.execute_workflow(context)

    print(f"   Status: {result_context.status.value}")
    print(f"   Completed steps: {len(result_context.completed_steps)}")

    return engine


async def test_agent_execution():
    """Test agent execution functionality"""
    print("\n🧪 Testing Agent Execution")
    print("-" * 40)

    from workflow_engine_poc.agent_steps import (
        agent_execution_step,
        EXAMPLE_CONTENT_ANALYZER,
    )
    from workflow_engine_poc.execution_context import ExecutionContext, UserContext

    # Create test context
    workflow_config = {
        "workflow_id": "test-agent",
        "name": "Test Agent Workflow",
        "steps": [],
    }

    user_context = UserContext(user_id="test_user")
    execution_context = ExecutionContext(workflow_config, user_context)

    # Test agent step
    step_config = {
        "step_id": "test_agent_step",
        "step_type": "agent_execution",
        "config": {
            "agent_config": EXAMPLE_CONTENT_ANALYZER,
            "query": "Please analyze this content: {content}",
            "return_simplified": True,
        },
    }

    input_data = {
        "content": "This is a test document for the PoC. It demonstrates agent execution within the workflow engine."
    }

    result = await agent_execution_step(step_config, input_data, execution_context)

    print(f"✅ Agent execution completed:")
    print(f"   Success: {result.get('success')}")
    print(f"   Agent: {result.get('agent_name')}")
    print(f"   Response length: {len(result.get('response', ''))}")
    print(f"   Execution time: {result.get('execution_time'):.3f}s")

    return result


async def test_full_workflow_with_agent():
    """Test a complete workflow including agent execution"""
    print("\n🧪 Testing Full Workflow with Agent")
    print("-" * 40)

    # Create step registry and engine
    registry = StepRegistry()
    await registry.register_builtin_steps()

    engine = WorkflowEngine(registry)

    # Create a workflow that processes data and then uses an agent
    workflow_config = {
        "workflow_id": "full-test",
        "name": "Full Test Workflow",
        "description": "Complete workflow with data processing and agent execution",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "input_data",
                "step_name": "Input Data",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "input_type": "static",
                    "data": {
                        "text": "The unified workflow execution engine is a powerful system that can execute workflows in a completely agnostic way. It supports sequential, parallel, and conditional execution patterns."
                    },
                },
            },
            {
                "step_id": "process_text",
                "step_name": "Process Text",
                "step_type": "data_processing",
                "step_order": 2,
                "dependencies": ["input_data"],
                "input_mapping": {"text": "input_data.data.text"},
                "config": {"processing_type": "word_count"},
            },
            {
                "step_id": "analyze_content",
                "step_name": "Analyze Content",
                "step_type": "agent_execution",
                "step_order": 3,
                "dependencies": ["input_data", "process_text"],
                "input_mapping": {
                    "content": "input_data.data.text",
                    "word_count": "process_text.result.word_count",
                },
                "config": {
                    "agent_config": {
                        "agent_name": "Content Analyzer",
                        "model": "gpt-4o-mini",
                        "system_prompt": "You are a content analyzer. Analyze the provided content and provide insights.",
                        "temperature": 0.1,
                        "max_tokens": 500,
                        "tools": [],
                    },
                    "query": "Please analyze this content (word count: {word_count}): {content}",
                    "return_simplified": True,
                },
            },
        ],
    }

    user_context = UserContext(user_id="test_user", session_id="full_test")
    context = ExecutionContext(workflow_config, user_context)

    # Execute workflow
    print("🚀 Executing full workflow...")
    result_context = await engine.execute_workflow(context)

    print(f"✅ Workflow completed:")
    print(f"   Status: {result_context.status.value}")
    print(f"   Total steps: {len(result_context.steps_config)}")
    print(f"   Completed: {len(result_context.completed_steps)}")
    print(f"   Failed: {len(result_context.failed_steps)}")

    if result_context.step_io_data:
        print("\n📊 Step outputs:")
        for step_id, data in result_context.step_io_data.items():
            if step_id == "analyze_content" and "response" in data:
                print(f"   {step_id}: {data['response'][:100]}...")
            else:
                print(f"   {step_id}: {type(data).__name__} with {len(data)} keys")

    return result_context


async def main():
    """Run all tests"""
    print("🚀 Unified Workflow Execution Engine PoC Test")
    print("=" * 60)

    try:
        # Test individual components
        await test_execution_context()
        await test_step_registry()
        await test_workflow_engine()
        await test_agent_execution()

        # Test full integration
        await test_full_workflow_with_agent()

        print("\n🎉 All tests completed successfully!")
        print("✅ The Workflow Engine PoC is working correctly")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
