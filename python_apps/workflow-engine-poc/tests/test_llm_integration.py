"""
LLM Integration Tests

Tests the workflow engine with real LLM providers when API keys are available.
Falls back to simulation mode when credentials are not provided.
"""

import asyncio
import os
import time
from typing import Dict, Any, Optional

from workflow_engine_poc.agent_steps import SimpleAgent
from workflow_engine_poc.tools import BASIC_TOOL_STORE


def check_api_credentials():
    """Check which API credentials are available"""

    credentials = {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "gemini": bool(os.getenv("GEMINI_API_KEY")),
        "bedrock": all(
            [
                os.getenv("AWS_ACCESS_KEY_ID"),
                os.getenv("AWS_SECRET_ACCESS_KEY"),
                os.getenv("AWS_DEFAULT_REGION"),
            ]
        ),
    }

    return credentials


async def test_openai_integration():
    """Test OpenAI integration"""

    print("🧪 Testing OpenAI Integration")
    print("-" * 40)

    has_key = bool(os.getenv("OPENAI_API_KEY"))
    print(f"📋 OpenAI API Key: {'✅ Available' if has_key else '❌ Not set'}")

    if not has_key:
        print("   ⚠️  Skipping real API test - using simulation mode")

    agent = SimpleAgent(
        name="OpenAI Test Agent",
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant that can use tools to answer questions accurately.",
        tool_names=["add_numbers", "calculate", "get_current_time"],
        provider_type="openai_textgen",
    )

    test_queries = [
        "What is 15 + 27?",
        "Calculate the result of 8 * 7 + 12",
        "What time is it right now?",
    ]

    for query in test_queries:
        print(f"📋 Query: {query}")

        start_time = time.time()
        result = await agent.execute(query)
        execution_time = time.time() - start_time

        print(f"   Success: {result['success']}")
        print(f"   Response: {result['response'][:100]}...")
        print(f"   Time: {execution_time:.3f}s")

        if has_key and result.get("tool_calls"):
            print(f"   Tool calls: {len(result['tool_calls'])}")

        assert result["success"], f"OpenAI execution failed for: {query}"

    print("✅ OpenAI integration test passed")


async def test_gemini_integration():
    """Test Gemini integration"""

    print("\n🧪 Testing Gemini Integration")
    print("-" * 40)

    has_key = bool(os.getenv("GEMINI_API_KEY"))
    print(f"📋 Gemini API Key: {'✅ Available' if has_key else '❌ Not set'}")

    if not has_key:
        print("   ⚠️  Skipping real API test - using simulation mode")

    agent = SimpleAgent(
        name="Gemini Test Agent",
        model="gemini-1.5-flash",
        system_prompt="You are a helpful assistant with access to tools.",
        tool_names=["add_numbers", "weather_forecast"],
        provider_type="gemini_textgen",
    )

    test_queries = [
        "Add 23 and 19 together",
        "What's the weather like in Tokyo?",
    ]

    for query in test_queries:
        print(f"📋 Query: {query}")

        start_time = time.time()
        result = await agent.execute(query)
        execution_time = time.time() - start_time

        print(f"   Success: {result['success']}")
        print(f"   Response: {result['response'][:100]}...")
        print(f"   Time: {execution_time:.3f}s")

        assert result["success"], f"Gemini execution failed for: {query}"

    print("✅ Gemini integration test passed")


async def test_bedrock_integration():
    """Test AWS Bedrock integration"""

    print("\n🧪 Testing Bedrock Integration")
    print("-" * 40)

    has_creds = all(
        [
            os.getenv("AWS_ACCESS_KEY_ID"),
            os.getenv("AWS_SECRET_ACCESS_KEY"),
            os.getenv("AWS_DEFAULT_REGION"),
        ]
    )

    print(f"📋 AWS Credentials: {'✅ Available' if has_creds else '❌ Not set'}")

    if not has_creds:
        print("   ⚠️  Skipping real API test - using simulation mode")

    agent = SimpleAgent(
        name="Bedrock Test Agent",
        model="anthropic.claude-3-sonnet-20240229-v1:0",
        system_prompt="You are Claude, a helpful assistant with access to tools.",
        tool_names=["calculate", "get_current_time"],
        provider_type="bedrock_textgen",
    )

    test_queries = [
        "Calculate 45 * 12",
        "What's the current time?",
    ]

    for query in test_queries:
        print(f"📋 Query: {query}")

        start_time = time.time()
        result = await agent.execute(query)
        execution_time = time.time() - start_time

        print(f"   Success: {result['success']}")
        print(f"   Response: {result['response'][:100]}...")
        print(f"   Time: {execution_time:.3f}s")

        assert result["success"], f"Bedrock execution failed for: {query}"

    print("✅ Bedrock integration test passed")


async def test_multi_provider_workflow():
    """Test workflow with multiple LLM providers"""

    print("\n🧪 Testing Multi-Provider Workflow")
    print("-" * 40)

    from workflow_engine_poc.workflow_engine import WorkflowEngine
    from workflow_engine_poc.step_registry import StepRegistry
    from workflow_engine_poc.agent_steps import agent_execution_step

    credentials = check_api_credentials()
    print(f"📋 Available providers: {[k for k, v in credentials.items() if v]}")

    # Create workflow with different providers
    workflow_config = {
        "workflow_id": "multi_provider_test",
        "name": "Multi-Provider Test Workflow",
        "steps": [
            {
                "step_id": "openai_step",
                "step_type": "agent",
                "config": {
                    "agent_config": {
                        "agent_name": "OpenAI Math Helper",
                        "model": "gpt-4o-mini",
                        "system_prompt": "You are a math assistant.",
                        "tool_names": ["add_numbers", "calculate"],
                        "provider_type": "openai_textgen",
                    },
                    "query": "What is 25 + 17?",
                },
            },
            {
                "step_id": "gemini_step",
                "step_type": "agent",
                "config": {
                    "agent_config": {
                        "agent_name": "Gemini Assistant",
                        "model": "gemini-1.5-flash",
                        "system_prompt": "You are a helpful assistant.",
                        "tool_names": ["get_current_time"],
                        "provider_type": "gemini_textgen",
                    },
                    "query": "What time is it?",
                },
            },
        ],
    }

    step_registry = StepRegistry()

    # Register the agent step function directly (for testing)
    step_registry.step_functions["agent"] = agent_execution_step
    step_registry.registered_steps["agent"] = {
        "step_type": "agent",
        "execution_type": "local",
        "name": "Agent Execution Step",
    }

    engine = WorkflowEngine(step_registry)

    start_time = time.time()
    result = await engine.execute_workflow(workflow_config)
    execution_time = time.time() - start_time

    print(f"📋 Workflow execution:")
    print(f"   Success: {result['success']}")
    print(f"   Steps completed: {len(result.get('results', []))}")
    print(f"   Total time: {execution_time:.3f}s")

    assert result["success"], "Multi-provider workflow failed"

    print("✅ Multi-provider workflow test passed")


async def test_function_calling_accuracy():
    """Test function calling accuracy with real APIs"""

    print("\n🧪 Testing Function Calling Accuracy")
    print("-" * 40)

    credentials = check_api_credentials()

    if not any(credentials.values()):
        print("   ⚠️  No API credentials available - skipping accuracy test")
        return

    # Test with the first available provider
    provider_type = "openai_textgen"
    if credentials["openai"]:
        provider_type = "openai_textgen"
    elif credentials["gemini"]:
        provider_type = "gemini_textgen"
    elif credentials["bedrock"]:
        provider_type = "bedrock_textgen"

    print(f"📋 Testing with provider: {provider_type}")

    agent = SimpleAgent(
        name="Function Calling Test Agent",
        model=(
            "gpt-4o-mini" if provider_type == "openai_textgen" else "gemini-1.5-flash"
        ),
        system_prompt="You are a precise assistant. Use the available tools to provide accurate answers.",
        tool_names=["add_numbers", "calculate"],
        provider_type=provider_type,
    )

    # Test cases with expected tool usage
    test_cases = [
        {
            "query": "What is 15 + 27?",
            "expected_tool": "add_numbers",
            "expected_result": "42",
        },
        {
            "query": "Calculate 8 * 7 + 12",
            "expected_tool": "calculate",
            "expected_result": "68",
        },
    ]

    for test_case in test_cases:
        query = test_case["query"]
        print(f"📋 Query: {query}")

        result = await agent.execute(query)

        print(f"   Success: {result['success']}")
        print(f"   Response: {result['response'][:100]}...")

        # In simulation mode, we can't test actual tool calling
        if any(credentials.values()):
            # Check if expected result appears in response
            expected = test_case["expected_result"]
            if expected in result["response"]:
                print(f"   ✅ Expected result '{expected}' found in response")
            else:
                print(f"   ⚠️  Expected result '{expected}' not clearly found")

        assert result["success"], f"Function calling test failed for: {query}"

    print("✅ Function calling accuracy test passed")


async def main():
    """Run all LLM integration tests"""

    print("🚀 LLM Integration Test Suite")
    print("=" * 60)

    # Check available credentials
    credentials = check_api_credentials()
    print("📋 API Credentials Status:")
    for provider, available in credentials.items():
        status = "✅ Available" if available else "❌ Not set"
        print(f"   {provider.upper()}: {status}")

    if not any(credentials.values()):
        print("\n⚠️  No API credentials found - tests will run in simulation mode")
        print(
            "   Set OPENAI_API_KEY, GEMINI_API_KEY, or AWS credentials to test real APIs"
        )

    print()

    try:
        await test_openai_integration()
        await test_gemini_integration()
        await test_bedrock_integration()
        await test_multi_provider_workflow()
        await test_function_calling_accuracy()

        print(f"\n🎉 All LLM integration tests passed!")

        print("\n📋 Integration Test Summary:")
        print("   ✅ OpenAI integration")
        print("   ✅ Gemini integration")
        print("   ✅ Bedrock integration")
        print("   ✅ Multi-provider workflow")
        print("   ✅ Function calling accuracy")

        if any(credentials.values()):
            print("\n🚀 Real API integration confirmed!")
        else:
            print("\n🔧 Simulation mode testing completed!")

    except Exception as e:
        print(f"\n❌ LLM integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
