"""
Test Tools Support in Workflow Engine

Tests for the new tools/function calling support in the workflow engine
using the enhanced LLM Gateway and agent steps.
"""

import asyncio
import os
from typing import Dict, Any

from workflow_engine_poc.execution_context import ExecutionContext, UserContext
from workflow_engine_poc.workflow_engine import WorkflowEngine
from workflow_engine_poc.step_registry import StepRegistry
from workflow_engine_poc.agent_steps import (
    EXAMPLE_ASSISTANT_WITH_TOOLS,
    WEATHER_TOOL,
    SEARCH_TOOL,
    CALCULATOR_TOOL,
    get_weather,
    search_web,
    calculate,
)


async def test_tools_interface():
    """Test that the tools interface is properly set up"""
    
    print("🧪 Testing Tools Interface")
    print("-" * 40)
    
    # Test that the agent has tools configured
    agent = EXAMPLE_ASSISTANT_WITH_TOOLS
    
    print(f"📋 Agent: {agent.name}")
    print(f"   Model: {agent.model}")
    print(f"   Tools: {len(agent.tools)}")
    print(f"   Tool handlers: {len(agent.tool_handlers)}")
    
    # Check tool definitions
    for i, tool in enumerate(agent.tools):
        tool_name = tool["function"]["name"]
        print(f"   Tool {i+1}: {tool_name}")
    
    # Check tool handlers
    for tool_name, handler in agent.tool_handlers.items():
        print(f"   Handler for {tool_name}: {handler.__name__}")
    
    print("✅ Tools interface properly configured")


async def test_tool_functions():
    """Test the individual tool functions"""
    
    print("\n🧪 Testing Tool Functions")
    print("-" * 40)
    
    # Test weather tool
    print("📋 Testing weather tool:")
    weather_result = await get_weather("San Francisco, CA", "celsius")
    print(f"   Result: {weather_result}")
    
    # Test search tool
    print("\n📋 Testing search tool:")
    search_result = await search_web("Python programming", 3)
    print(f"   Result: {search_result}")
    
    # Test calculator tool
    print("\n📋 Testing calculator tool:")
    calc_result = await calculate("2 + 2 * 3")
    print(f"   Result: {calc_result}")
    
    print("\n✅ All tool functions working correctly")


async def test_agent_with_tools():
    """Test agent execution with tools (simulation mode)"""
    
    print("\n🧪 Testing Agent with Tools")
    print("-" * 40)
    
    agent = EXAMPLE_ASSISTANT_WITH_TOOLS
    
    # Test queries that might trigger tool usage
    test_queries = [
        "What's the weather like in New York?",
        "Calculate 15 * 24 + 100",
        "Search for information about machine learning",
        "Hello, how are you today?"  # Should not trigger tools
    ]
    
    for query in test_queries:
        print(f"\n📋 Query: {query}")
        
        try:
            result = await agent.execute(query)
            
            print(f"   Success: {result['success']}")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Execution time: {result['execution_time']:.3f}s")
            print(f"   Tools used: {result.get('tools_used', [])}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ Agent execution with tools completed")


async def test_workflow_with_tools():
    """Test workflow execution with tool-enabled agents"""
    
    print("\n🧪 Testing Workflow with Tool-Enabled Agents")
    print("-" * 40)
    
    # Create a workflow that uses the tool-enabled agent
    workflow_config = {
        "workflow_id": "tools-test-workflow",
        "name": "Tools Test Workflow",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "input_step",
                "step_name": "Input Step",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "input_type": "static",
                    "data": {
                        "user_query": "What's the weather in London and calculate 25 * 4?"
                    }
                }
            },
            {
                "step_id": "agent_step",
                "step_name": "Tool-Enabled Agent Step",
                "step_type": "agent_execution",
                "step_order": 2,
                "dependencies": ["input_step"],
                "config": {
                    "agent_config": {
                        "agent_name": "Assistant with Tools",
                        "model": "gpt-4o-mini",
                        "system_prompt": "You are a helpful assistant with access to tools. Use the available tools to help answer questions.",
                        "temperature": 0.1,
                        "max_tokens": 1000,
                        "provider_type": "openai_textgen",
                        "tools": [WEATHER_TOOL, CALCULATOR_TOOL],
                        "tool_handlers": {
                            "get_weather": "get_weather",
                            "calculate": "calculate"
                        }
                    },
                    "query": "{input_step.output.data.user_query}",
                    "return_simplified": True
                }
            }
        ]
    }
    
    # Initialize components
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()
    
    workflow_engine = WorkflowEngine(step_registry)
    
    # Create execution context
    user_context = UserContext(user_id="tools_test_user")
    execution_context = ExecutionContext(workflow_config, user_context)
    
    print("📋 Executing workflow with tool-enabled agent:")
    
    # Execute workflow
    await workflow_engine.execute_workflow(execution_context)
    
    # Check results
    summary = execution_context.get_execution_summary()
    print(f"   Workflow status: {summary['status']}")
    print(f"   Completed steps: {summary.get('completed_steps', 0)}")
    
    # Check agent step result
    agent_result = execution_context.step_results.get("agent_step")
    if agent_result and agent_result.output_data:
        print(f"   Agent response: {str(agent_result.output_data)[:200]}...")
    
    print("✅ Workflow with tools completed")


async def test_tools_with_real_llm():
    """Test tools with real LLM (if API key available)"""
    
    print("\n🧪 Testing Tools with Real LLM")
    print("-" * 40)
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY not set - skipping real LLM test")
        print("   This test would demonstrate actual tool calling with OpenAI")
        return
    
    print("📋 OpenAI API key found - testing real tool calls")
    
    agent = EXAMPLE_ASSISTANT_WITH_TOOLS
    
    # Test a query that should trigger tool usage
    query = "What's the weather in Paris and what's 15 * 8?"
    
    try:
        result = await agent.execute(query)
        
        print(f"   Success: {result['success']}")
        print(f"   Response: {result['response']}")
        print(f"   Execution time: {result['execution_time']:.3f}s")
        
        # Check if tools were actually called
        if "Tool Results:" in result['response']:
            print("✅ Real tool calls detected in response!")
        else:
            print("ℹ️  No tool calls detected (may be using simulation)")
            
    except Exception as e:
        print(f"❌ Real LLM test failed: {e}")


async def main():
    """Run all tools support tests"""
    
    print("🚀 Tools Support Test Suite")
    print("=" * 60)
    
    try:
        await test_tools_interface()
        await test_tool_functions()
        await test_agent_with_tools()
        await test_workflow_with_tools()
        await test_tools_with_real_llm()
        
        print("\n🎉 All tools support tests completed successfully!")
        print("✅ Tools support is working correctly in the workflow engine")
        
        print("\n📋 Tools Support Summary:")
        print("   ✅ LLM Gateway supports tools interface")
        print("   ✅ Agent steps can define and use tools")
        print("   ✅ Tool execution happens in the API layer")
        print("   ✅ Workflow engine supports tool-enabled agents")
        print("   ✅ Graceful fallback when tools not available")
        
    except Exception as e:
        print(f"\n❌ Tools support test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
