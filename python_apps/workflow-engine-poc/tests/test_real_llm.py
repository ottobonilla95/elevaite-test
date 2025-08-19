"""
Test Real LLM Integration

This script demonstrates how to use the workflow engine with real LLM providers.
To use this, you need to set up environment variables for your chosen provider.

Example environment variables:
- For OpenAI: OPENAI_API_KEY
- For Gemini: GOOGLE_API_KEY
- For Bedrock: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
"""

import asyncio
import os
from typing import Dict, Any

from workflow_engine_poc.agent_steps import (
    SimpleAgent,
    EXAMPLE_CONTENT_ANALYZER,
    EXAMPLE_GEMINI_AGENT,
)
from workflow_engine_poc.execution_context import ExecutionContext, UserContext


async def test_openai_agent():
    """Test agent with OpenAI provider"""

    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set - skipping OpenAI test")
        return

    print("\n🧪 Testing OpenAI Agent")
    print("-" * 40)

    # Create agent with OpenAI configuration
    agent_config = EXAMPLE_CONTENT_ANALYZER.copy()
    agent_config["provider_type"] = "openai_textgen"

    agent = SimpleAgent(
        name=agent_config["agent_name"],
        model=agent_config["model"],
        system_prompt=agent_config["system_prompt"],
        temperature=agent_config["temperature"],
        max_tokens=agent_config["max_tokens"],
        provider_type=agent_config["provider_type"],
    )

    # Test query
    query = "Analyze this text: 'The unified workflow execution engine represents a significant advancement in automation technology, providing clean abstractions and multi-provider support.'"

    result = await agent.execute(query)

    print(f"✅ OpenAI Agent Result:")
    print(f"   Success: {result.get('success')}")
    print(f"   Agent: {result.get('agent_name')}")
    print(f"   Model: {result.get('model')}")
    print(f"   Provider: {result.get('provider_type')}")
    print(f"   Execution Time: {result.get('execution_time'):.3f}s")
    print(f"   Response: {result.get('response', 'No response')[:200]}...")

    return result


async def test_gemini_agent():
    """Test agent with Gemini provider"""

    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  GOOGLE_API_KEY not set - skipping Gemini test")
        return

    print("\n🧪 Testing Gemini Agent")
    print("-" * 40)

    # Create agent with Gemini configuration
    agent_config = EXAMPLE_GEMINI_AGENT.copy()

    agent = SimpleAgent(
        name=agent_config["agent_name"],
        model=agent_config["model"],
        system_prompt=agent_config["system_prompt"],
        temperature=agent_config["temperature"],
        max_tokens=agent_config["max_tokens"],
        provider_type=agent_config["provider_type"],
    )

    # Test query
    query = "What are the key benefits of using a unified workflow execution engine?"

    result = await agent.execute(query)

    print(f"✅ Gemini Agent Result:")
    print(f"   Success: {result.get('success')}")
    print(f"   Agent: {result.get('agent_name')}")
    print(f"   Model: {result.get('model')}")
    print(f"   Provider: {result.get('provider_type')}")
    print(f"   Execution Time: {result.get('execution_time'):.3f}s")
    print(f"   Response: {result.get('response', 'No response')[:200]}...")

    return result


async def test_workflow_with_real_llm():
    """Test a complete workflow with real LLM integration"""

    if not (os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        print("⚠️  No API keys set - skipping workflow test")
        return

    print("\n🧪 Testing Workflow with Real LLM")
    print("-" * 40)

    from .step_registry import StepRegistry
    from .workflow_engine import WorkflowEngine

    # Create step registry and engine
    registry = StepRegistry()
    await registry.register_builtin_steps()

    engine = WorkflowEngine(registry)

    # Choose provider based on available API keys
    if os.getenv("OPENAI_API_KEY"):
        provider_type = "openai_textgen"
        model = "gpt-4o-mini"
    elif os.getenv("GOOGLE_API_KEY"):
        provider_type = "gemini_textgen"
        model = "gemini-1.5-flash"
    else:
        print("No supported API keys found")
        return

    # Create workflow with real LLM
    workflow_config = {
        "workflow_id": "real-llm-test",
        "name": "Real LLM Test Workflow",
        "description": "Test workflow with real LLM integration",
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
                        "content": "The workflow execution engine is a revolutionary system that enables seamless automation across multiple domains. It provides clean abstractions, multi-provider support, and simplified agent integration."
                    },
                },
            },
            {
                "step_id": "analyze_with_llm",
                "step_name": "Analyze with LLM",
                "step_type": "agent_execution",
                "step_order": 2,
                "dependencies": ["input_data"],
                "input_mapping": {"content": "input_data.data.content"},
                "config": {
                    "agent_config": {
                        "agent_name": f"Real {provider_type.split('_')[0].title()} Analyzer",
                        "model": model,
                        "system_prompt": "You are an expert technical analyst. Analyze the provided content and identify key themes, benefits, and technical aspects.",
                        "temperature": 0.1,
                        "max_tokens": 500,
                        "tools": [],
                        "provider_type": provider_type,
                    },
                    "query": "Please analyze this content and provide insights: {content}",
                    "return_simplified": True,
                },
            },
        ],
    }

    user_context = UserContext(user_id="test_user", session_id="real_llm_test")
    context = ExecutionContext(workflow_config, user_context)

    # Execute workflow
    print(f"🚀 Executing workflow with {provider_type}...")
    result_context = await engine.execute_workflow(context)

    print(f"✅ Workflow completed:")
    print(f"   Status: {result_context.status.value}")
    print(f"   Total steps: {len(result_context.steps_config)}")
    print(f"   Completed: {len(result_context.completed_steps)}")
    print(f"   Failed: {len(result_context.failed_steps)}")

    if result_context.step_io_data:
        print("\n📊 Step outputs:")
        for step_id, data in result_context.step_io_data.items():
            if step_id == "analyze_with_llm" and "response" in data:
                print(f"   {step_id}: {data['response'][:300]}...")
            else:
                print(f"   {step_id}: {type(data).__name__} with {len(data)} keys")

    return result_context


async def main():
    """Run real LLM integration tests"""

    print("🚀 Real LLM Integration Tests")
    print("=" * 60)

    print("\n📋 Available API Keys:")
    print(
        f"   OPENAI_API_KEY: {'✅ Set' if os.getenv('OPENAI_API_KEY') else '❌ Not set'}"
    )
    print(
        f"   GOOGLE_API_KEY: {'✅ Set' if os.getenv('GOOGLE_API_KEY') else '❌ Not set'}"
    )
    print(
        f"   AWS Credentials: {'✅ Set' if all([os.getenv('AWS_ACCESS_KEY_ID'), os.getenv('AWS_SECRET_ACCESS_KEY')]) else '❌ Not set'}"
    )

    if not any([os.getenv("OPENAI_API_KEY"), os.getenv("GOOGLE_API_KEY")]):
        print("\n⚠️  No API keys configured!")
        print("To test real LLM integration, set one of the following:")
        print("   export OPENAI_API_KEY='your-openai-key'")
        print("   export GOOGLE_API_KEY='your-google-key'")
        print("\nFalling back to simulation mode...")
        return

    try:
        # Test individual agents
        await test_openai_agent()
        await test_gemini_agent()

        # Test complete workflow
        await test_workflow_with_real_llm()

        print("\n🎉 Real LLM integration tests completed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
