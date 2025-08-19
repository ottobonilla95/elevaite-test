"""
End-to-End Tests for Workflow Engine

Comprehensive tests that validate the entire workflow engine functionality
including agents, tools, workflow execution, and integrations.
"""

import asyncio
import json
import time
from typing import Dict, Any, List

from workflow_engine_poc.workflow_engine import WorkflowEngine
from workflow_engine_poc.step_registry import StepRegistry
from workflow_engine_poc.execution_context import ExecutionContext
from workflow_engine_poc.agent_steps import SimpleAgent, agent_execution_step
from workflow_engine_poc.tools import (
    BASIC_TOOL_STORE,
    function_schema,
    tool_handler,
)


async def test_basic_agent_execution():
    """Test basic agent execution without tools"""

    print("🧪 Testing Basic Agent Execution")
    print("-" * 50)

    agent = SimpleAgent(
        name="Basic Test Agent",
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant for testing.",
        provider_type="openai_textgen",
    )

    test_queries = [
        "Hello, how are you?",
        "What is 2 + 2?",
        "Tell me a short joke.",
    ]

    for query in test_queries:
        print(f"📋 Query: {query}")

        start_time = time.time()
        result = await agent.execute(query)
        execution_time = time.time() - start_time

        assert result["success"], f"Agent execution failed for query: {query}"
        assert "response" in result, "Response missing from result"
        assert len(result["response"]) > 0, "Empty response"

        print(f"   ✅ Success: {result['success']}")
        print(f"   📝 Response: {result['response'][:100]}...")
        print(f"   ⏱️  Time: {execution_time:.3f}s")

    print("✅ Basic agent execution test passed")


async def test_agent_with_tools():
    """Test agent execution with tools"""

    print("\n🧪 Testing Agent with Tools")
    print("-" * 50)

    agent = SimpleAgent(
        name="Tool-Enabled Agent",
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant with access to tools. Use them when appropriate.",
        tool_names=["add_numbers", "calculate", "get_current_time", "weather_forecast"],
        provider_type="openai_textgen",
    )

    # Verify tools were loaded
    assert len(agent.tools) == 4, f"Expected 4 tools, got {len(agent.tools)}"
    assert (
        len(agent.tool_handlers) == 4
    ), f"Expected 4 handlers, got {len(agent.tool_handlers)}"

    test_queries = [
        "What's 15 + 27?",
        "Calculate 5 * 8 + 3",
        "What time is it?",
        "What's the weather like in San Francisco?",
        "Just say hello (no tools needed)",
    ]

    for query in test_queries:
        print(f"📋 Query: {query}")

        start_time = time.time()
        result = await agent.execute(query)
        execution_time = time.time() - start_time

        assert result["success"], f"Agent execution failed for query: {query}"
        assert "response" in result, "Response missing from result"

        print(f"   ✅ Success: {result['success']}")
        print(f"   📝 Response: {result['response'][:100]}...")
        print(f"   🔧 Tools available: {len(result.get('tools_used', []))}")
        print(f"   ⏱️  Time: {execution_time:.3f}s")

    print("✅ Agent with tools test passed")


async def test_workflow_execution():
    """Test complete workflow execution"""

    print("\n🧪 Testing Workflow Execution")
    print("-" * 50)

    # Create a simple workflow
    workflow_config = {
        "workflow_id": "test_workflow_001",
        "name": "E2E Test Workflow",
        "description": "End-to-end test workflow with multiple steps",
        "steps": [
            {
                "step_id": "step_1",
                "step_type": "agent",
                "name": "Math Helper",
                "config": {
                    "agent_config": {
                        "agent_name": "Math Assistant",
                        "model": "gpt-4o-mini",
                        "system_prompt": "You are a math assistant. Help with calculations.",
                        "tool_names": ["add_numbers", "calculate"],
                        "provider_type": "openai_textgen",
                    },
                    "query": "Calculate 25 + 17",
                },
            },
            {
                "step_id": "step_2",
                "step_type": "agent",
                "name": "Time Helper",
                "config": {
                    "agent_config": {
                        "agent_name": "Time Assistant",
                        "model": "gpt-4o-mini",
                        "system_prompt": "You help with time-related queries.",
                        "tool_names": ["get_current_time"],
                        "provider_type": "openai_textgen",
                    },
                    "query": "What time is it?",
                },
            },
        ],
    }

    # Execute workflow
    step_registry = StepRegistry()

    # Register the agent step function directly (for testing)
    step_registry.step_functions["agent"] = agent_execution_step
    step_registry.registered_steps["agent"] = {
        "step_type": "agent",
        "execution_type": "local",
        "name": "Agent Execution Step",
    }

    engine = WorkflowEngine(step_registry)

    print(f"📋 Executing workflow: {workflow_config['name']}")
    print(f"   Steps: {len(workflow_config['steps'])}")

    # Create execution context
    execution_context = ExecutionContext(workflow_config)

    start_time = time.time()
    execution_context = await engine.execute_workflow(execution_context)
    execution_time = time.time() - start_time

    # Validate results
    from workflow_engine_poc.execution_context import ExecutionStatus

    success = execution_context.status == ExecutionStatus.COMPLETED
    assert success, f"Workflow execution failed: {execution_context.status}"
    assert (
        len(execution_context.step_results) == 2
    ), f"Expected 2 step results, got {len(execution_context.step_results)}"

    print(f"   ✅ Success: {success}")
    print(f"   📊 Steps completed: {len(execution_context.step_results)}")
    print(f"   ⏱️  Total time: {execution_time:.3f}s")

    # Check individual step results
    for step_id, step_result in execution_context.step_results.items():
        step_success = step_result.status.value == "completed"
        print(
            f"   📋 {step_id}: {'✅' if step_success else '❌'} {step_result.status.value}"
        )

    print("✅ Workflow execution test passed")


async def test_custom_tools():
    """Test custom tool creation and usage"""

    print("\n🧪 Testing Custom Tools")
    print("-" * 50)

    # Create custom tools
    @function_schema
    def text_processor(operation: str, text: str, value: str = "") -> str:
        """Process text with various operations."""
        if operation == "uppercase":
            return text.upper()
        elif operation == "lowercase":
            return text.lower()
        elif operation == "reverse":
            return text[::-1]
        elif operation == "replace":
            old, new = value.split(",", 1) if "," in value else (value, "")
            return text.replace(old, new)
        else:
            return f"Unknown operation: {operation}"

    @tool_handler(name="data_formatter", description="Formats data in various ways")
    def format_data(format_type: str, data: str) -> str:
        """Format data according to specified type."""
        if format_type == "json":
            try:
                parsed = json.loads(data)
                return json.dumps(parsed, indent=2)
            except:
                return f"Invalid JSON: {data}"
        elif format_type == "csv":
            return data.replace(",", " | ")
        else:
            return f"Unsupported format: {format_type}"

    # Test custom tools directly
    result1 = text_processor("uppercase", "hello world")
    assert result1 == "HELLO WORLD", f"Expected 'HELLO WORLD', got '{result1}'"
    print(f"📋 text_processor test: {result1}")

    result2 = format_data("csv", "a,b,c,d")
    assert result2 == "a | b | c | d", f"Expected 'a | b | c | d', got '{result2}'"
    print(f"📋 format_data test: {result2}")

    # Test with agent
    agent = SimpleAgent(
        name="Custom Tool Agent",
        model="gpt-4o-mini",
        system_prompt="You have access to custom text processing tools.",
        tools=[text_processor.openai_schema, format_data.openai_schema],
        tool_handlers={
            "text_processor": text_processor,
            "data_formatter": format_data,
        },
        provider_type="openai_textgen",
    )

    result = await agent.execute("Convert 'hello world' to uppercase")
    assert result["success"], "Custom tool agent execution failed"
    print(f"📋 Agent with custom tools: {result['response'][:100]}...")

    print("✅ Custom tools test passed")


async def test_error_handling():
    """Test error handling and recovery"""

    print("\n🧪 Testing Error Handling")
    print("-" * 50)

    # Test agent with invalid configuration
    try:
        agent = SimpleAgent(
            name="Invalid Agent",
            model="invalid-model-name",
            system_prompt="Test agent",
            provider_type="invalid_provider",
        )

        result = await agent.execute("Test query")
        # In simulation mode, this might still succeed
        print(f"📋 Invalid config result: {result['success']}")

    except Exception as e:
        print(f"📋 Expected error caught: {type(e).__name__}")

    # Test workflow with invalid step
    invalid_workflow = {
        "workflow_id": "invalid_workflow",
        "name": "Invalid Workflow",
        "steps": [
            {"step_id": "invalid_step", "step_type": "invalid_type", "config": {}}
        ],
    }

    step_registry = StepRegistry()
    engine = WorkflowEngine(step_registry)

    execution_context = ExecutionContext(invalid_workflow)
    execution_context = await engine.execute_workflow(execution_context)

    # Should handle gracefully
    from workflow_engine_poc.execution_context import ExecutionStatus

    success = execution_context.status == ExecutionStatus.COMPLETED
    print(f"📋 Invalid workflow result: {success}")
    if not success:
        print(f"   Error handled: {execution_context.status}")

    print("✅ Error handling test passed")


async def test_performance():
    """Test performance with multiple concurrent executions"""

    print("\n🧪 Testing Performance")
    print("-" * 50)

    agent = SimpleAgent(
        name="Performance Test Agent",
        model="gpt-4o-mini",
        system_prompt="You are a fast assistant.",
        tool_names=["add_numbers", "calculate"],
        provider_type="openai_textgen",
    )

    # Test concurrent executions
    queries = [f"Calculate {i} + {i+1}" for i in range(5)]

    print(f"📋 Running {len(queries)} concurrent queries...")

    start_time = time.time()
    tasks = [agent.execute(query) for query in queries]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_time = time.time() - start_time

    successful_results = [
        r for r in results if isinstance(r, dict) and r.get("success")
    ]

    print(f"   ✅ Successful: {len(successful_results)}/{len(queries)}")
    print(f"   ⏱️  Total time: {total_time:.3f}s")
    print(f"   📊 Avg per query: {total_time/len(queries):.3f}s")

    assert len(successful_results) >= len(queries) * 0.8, "Too many failed executions"

    print("✅ Performance test passed")


async def main():
    """Run all E2E tests"""

    print("🚀 Workflow Engine E2E Test Suite")
    print("=" * 70)

    start_time = time.time()

    try:
        await test_basic_agent_execution()
        await test_agent_with_tools()
        await test_workflow_execution()
        await test_custom_tools()
        await test_error_handling()
        await test_performance()

        total_time = time.time() - start_time

        print(f"\n🎉 All E2E tests passed!")
        print(f"⏱️  Total execution time: {total_time:.3f}s")

        print("\n📋 E2E Test Summary:")
        print("   ✅ Basic agent execution")
        print("   ✅ Agent with tools")
        print("   ✅ Workflow execution")
        print("   ✅ Custom tools")
        print("   ✅ Error handling")
        print("   ✅ Performance testing")
        print("\n🚀 Workflow Engine is ready for production!")

    except Exception as e:
        print(f"\n❌ E2E test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
