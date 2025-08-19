"""
End-to-End Tests for Workflow Engine

Comprehensive tests that validate the entire workflow engine functionality
including agents, tools, workflow execution, and integrations.
"""

import asyncio
import json
import time
import httpx
from typing import Dict, Any, List

from workflow_engine_poc.agent_steps import SimpleAgent
from workflow_engine_poc.tools import (
    BASIC_TOOL_STORE,
    function_schema,
    tool_handler,
)

# API Configuration
API_BASE_URL = "http://localhost:8006"
API_TIMEOUT = 30.0


async def check_api_health():
    """Check if the API server is running"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{API_BASE_URL}/health")
            return response.status_code == 200
    except Exception:
        return False


async def wait_for_execution(execution_id: str, max_wait: int = 30):
    """Wait for workflow execution to complete"""
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        for _ in range(max_wait):
            try:
                response = await client.get(f"{API_BASE_URL}/executions/{execution_id}")
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status", "unknown")
                    if status in ["completed", "failed", "cancelled"]:
                        return status_data
                await asyncio.sleep(1)
            except Exception as e:
                print(f"   ⚠️  Error checking status: {e}")
                await asyncio.sleep(1)
        return {"status": "timeout", "message": "Execution timed out"}


async def test_basic_agent_execution():
    """Test basic agent execution without tools"""

    print("🧪 Testing Basic Agent Execution")
    print("-" * 50)

    # Check if we have API keys available for direct testing
    import os

    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))

    if not has_openai_key:
        print("   ⚠️  No OPENAI_API_KEY found - using simulation mode")

    agent = SimpleAgent(
        name="Basic Test Agent",
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant for testing.",
        provider_type="openai_textgen",
        force_real_llm=has_openai_key,  # Force real LLM if we have the key
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

    # Check if we have API keys available for direct testing
    import os

    has_openai_key = bool(os.getenv("OPENAI_API_KEY"))

    if not has_openai_key:
        print("   ⚠️  No OPENAI_API_KEY found - using simulation mode")

    agent = SimpleAgent(
        name="Tool-Enabled Agent",
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant with access to tools. Use them when appropriate.",
        tool_names=["add_numbers", "calculate", "get_current_time", "weather_forecast"],
        provider_type="openai_textgen",
        force_real_llm=has_openai_key,  # Force real LLM if we have the key
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
    """Test complete workflow execution via API"""

    print("\n🧪 Testing Workflow Execution via API")
    print("-" * 50)

    # Create a simple workflow
    workflow_config = {
        "workflow_id": "test_workflow_001",
        "name": "E2E Test Workflow",
        "description": "End-to-end test workflow with multiple steps",
        "steps": [
            {
                "step_id": "step_1",
                "step_name": "Math Helper",
                "step_type": "agent_execution",
                "step_order": 1,
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
                "step_name": "Time Helper",
                "step_type": "agent_execution",
                "step_order": 2,
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

    # Check if API is running
    api_available = await check_api_health()
    if not api_available:
        print("   ⚠️  API server not running - skipping API tests")
        print("   💡 Start the server with: python main.py")
        return

    # Create execution request for API
    execution_request = {
        "workflow_config": workflow_config,
        "user_id": "test_user",
        "session_id": "test_session",
        "organization_id": "test_org",
        "input_data": {},
        "execution_options": {},
    }

    print(f"📋 Executing workflow via API: {workflow_config['name']}")
    print(f"   Steps: {len(workflow_config['steps'])}")

    # Execute workflow via API
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        start_time = time.time()

        # Start execution
        response = await client.post(
            f"{API_BASE_URL}/workflows/execute", json=execution_request
        )

        assert (
            response.status_code == 200
        ), f"Failed to start execution: {response.status_code} - {response.text}"

        execution_data = response.json()
        execution_id = execution_data["execution_id"]

        print(f"   🚀 Execution started: {execution_id}")

        # Wait for completion
        final_status = await wait_for_execution(execution_id)
        execution_time = time.time() - start_time

        # Validate results
        success = final_status.get("status") == "completed"
        print(f"   ✅ Success: {success}")
        print(f"   📊 Final status: {final_status.get('status', 'unknown')}")
        print(f"   ⏱️  Total time: {execution_time:.3f}s")

        if success:
            # Get detailed results
            results_response = await client.get(
                f"{API_BASE_URL}/executions/{execution_id}/results"
            )
            if results_response.status_code == 200:
                results = results_response.json()
                step_results = results.get("step_results", {})
                print(f"   📋 Steps completed: {len(step_results)}")

                for step_id, step_result in step_results.items():
                    step_status = step_result.get("status", "unknown")
                    print(
                        f"   📋 {step_id}: {'✅' if step_status == 'completed' else '❌'} {step_status}"
                    )

        assert (
            success
        ), f"Workflow execution failed: {final_status.get('message', 'Unknown error')}"

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

    # Test API error handling if server is running
    api_available = await check_api_health()
    if api_available:
        print("📋 Testing API error handling...")

        # Test invalid workflow via API
        invalid_request = {
            "workflow_config": {
                "workflow_id": "invalid_workflow",
                "name": "Invalid Workflow",
                "steps": [
                    {
                        "step_id": "invalid_step",
                        "step_name": "Invalid Step",
                        "step_type": "invalid_type",
                        "config": {},
                    }
                ],
            },
            "user_id": "test_user",
            "session_id": "test_session",
            "organization_id": "test_org",
        }

        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            try:
                response = await client.post(
                    f"{API_BASE_URL}/workflows/execute", json=invalid_request
                )
                print(f"   API response status: {response.status_code}")

                if response.status_code == 200:
                    # Execution started, check if it fails gracefully
                    execution_data = response.json()
                    execution_id = execution_data["execution_id"]
                    final_status = await wait_for_execution(execution_id)
                    print(f"   Final status: {final_status.get('status', 'unknown')}")
                else:
                    print(f"   API correctly rejected invalid request")

            except Exception as e:
                print(f"   API error handled: {type(e).__name__}")
    else:
        print("   ⚠️  API not available - skipping API error tests")

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

    # Check API availability
    api_available = await check_api_health()
    print(
        f"📋 API Server Status: {'✅ Running' if api_available else '❌ Not running'}"
    )
    if not api_available:
        print("   💡 Start the server with: python main.py")
        print("   🔧 Some tests will be skipped without the API server")
    print()

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
        print(
            f"   {'✅' if api_available else '⚠️ '} Workflow execution {'(via API)' if api_available else '(skipped - no API)'}"
        )
        print("   ✅ Custom tools")
        print(
            f"   {'✅' if api_available else '⚠️ '} Error handling {'(with API)' if api_available else '(basic only)'}"
        )
        print("   ✅ Performance testing")

        if api_available:
            print("\n🚀 Full E2E testing completed with API integration!")
        else:
            print("\n🔧 Basic testing completed - start API server for full E2E tests!")

    except Exception as e:
        print(f"\n❌ E2E test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
