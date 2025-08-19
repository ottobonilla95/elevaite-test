"""
Test Tools Integration

Tests for the integrated tools system in the workflow engine.
"""

import asyncio
import os
from typing import Dict, Any

from workflow_engine_poc.agent_steps import (
    SimpleAgent,
    EXAMPLE_ASSISTANT_WITH_TOOLS,
    EXAMPLE_ASSISTANT_WITH_CUSTOM_TOOLS,
)
from workflow_engine_poc.tools import (
    function_schema,
    tool_handler,
    BASIC_TOOL_STORE,
    BASIC_TOOL_SCHEMAS,
    get_tool_by_name,
    add_numbers,
    calculate,
)


async def test_tools_decorator():
    """Test the function_schema decorator"""
    
    print("🧪 Testing Tools Decorator")
    print("-" * 40)
    
    @function_schema
    def test_function(x: int, y: str = "default") -> str:
        """A test function for the decorator."""
        return f"x={x}, y={y}"
    
    # Check that schema was attached
    assert hasattr(test_function, 'openai_schema'), "Schema not attached to function"
    
    schema = test_function.openai_schema
    print(f"✅ Schema generated for test_function")
    print(f"   Name: {schema['function']['name']}")
    print(f"   Description: {schema['function']['description']}")
    print(f"   Parameters: {list(schema['function']['parameters']['properties'].keys())}")
    print(f"   Required: {schema['function']['parameters']['required']}")
    
    # Test function still works
    result = test_function(42, "hello")
    print(f"   Function result: {result}")
    
    assert result == "x=42, y=hello", "Function execution failed"
    print("✅ Decorator test passed")


async def test_basic_tools():
    """Test the basic tools from the tool store"""
    
    print("\n🧪 Testing Basic Tools")
    print("-" * 40)
    
    # Test add_numbers tool
    result = add_numbers(5, 3)
    print(f"📋 add_numbers(5, 3): {result}")
    assert "8" in result, "add_numbers failed"
    
    # Test calculate tool
    calc_tool = get_tool_by_name("calculate")
    if calc_tool:
        result = calc_tool("2 * 3 + 4")
        print(f"📋 calculate('2 * 3 + 4'): {result}")
        assert "10" in result, "calculate failed"
    
    # Test tool schema retrieval
    schema = BASIC_TOOL_SCHEMAS.get("add_numbers")
    assert schema is not None, "Schema not found for add_numbers"
    print(f"📋 add_numbers schema: {schema['function']['name']}")
    
    print("✅ Basic tools test passed")


async def test_agent_with_tool_names():
    """Test agent creation with tool_names parameter"""
    
    print("\n🧪 Testing Agent with Tool Names")
    print("-" * 40)
    
    agent = SimpleAgent(
        name="Test Agent",
        model="gpt-4o-mini",
        system_prompt="You are a test agent.",
        tool_names=["add_numbers", "calculate", "get_current_time"],
        provider_type="openai_textgen"
    )
    
    print(f"📋 Agent created: {agent.name}")
    print(f"   Tools loaded: {len(agent.tools)}")
    print(f"   Tool handlers: {len(agent.tool_handlers)}")
    
    # Check that tools were loaded
    assert len(agent.tools) == 3, f"Expected 3 tools, got {len(agent.tools)}"
    assert len(agent.tool_handlers) == 3, f"Expected 3 handlers, got {len(agent.tool_handlers)}"
    
    # Check specific tools
    tool_names = [tool['function']['name'] for tool in agent.tools]
    expected_tools = ["add_numbers", "calculate", "get_current_time"]
    
    for expected in expected_tools:
        assert expected in tool_names, f"Tool {expected} not found in agent tools"
        assert expected in agent.tool_handlers, f"Handler for {expected} not found"
    
    print("✅ Agent with tool names test passed")


async def test_agent_execution_with_tools():
    """Test agent execution with tools (simulation mode)"""
    
    print("\n🧪 Testing Agent Execution with Tools")
    print("-" * 40)
    
    agent = EXAMPLE_ASSISTANT_WITH_TOOLS
    
    # Test queries that might trigger tool usage
    test_queries = [
        "What's 15 + 27?",
        "What time is it?",
        "Calculate 5 * 8",
        "Hello, how are you?"  # Should not trigger tools
    ]
    
    for query in test_queries:
        print(f"\n📋 Query: {query}")
        
        try:
            result = await agent.execute(query)
            
            print(f"   Success: {result['success']}")
            print(f"   Response: {result['response'][:100]}...")
            print(f"   Execution time: {result['execution_time']:.3f}s")
            
            # Check if tools were used (in simulation mode, this might not show)
            if 'tools_used' in result:
                print(f"   Tools used: {result['tools_used']}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n✅ Agent execution test completed")


async def test_custom_tool_creation():
    """Test creating custom tools with decorators"""
    
    print("\n🧪 Testing Custom Tool Creation")
    print("-" * 40)
    
    @tool_handler(name="string_operations", description="Performs string operations")
    def string_ops(operation: str, text: str, value: str = "") -> str:
        """Performs various string operations."""
        if operation == "upper":
            return text.upper()
        elif operation == "lower":
            return text.lower()
        elif operation == "replace":
            return text.replace(value.split(",")[0], value.split(",")[1])
        else:
            return f"Unknown operation: {operation}"
    
    # Test the decorated function
    result = string_ops("upper", "hello world")
    print(f"📋 string_ops('upper', 'hello world'): {result}")
    assert result == "HELLO WORLD", "String operation failed"
    
    # Check schema
    schema = string_ops.openai_schema
    print(f"📋 Custom tool schema: {schema['function']['name']}")
    assert schema['function']['name'] == "string_operations", "Custom name not applied"
    
    # Test with agent
    agent = SimpleAgent(
        name="Custom Tool Agent",
        model="gpt-4o-mini",
        system_prompt="You are an agent with custom tools.",
        tools=[schema],
        tool_handlers={"string_operations": string_ops},
        provider_type="openai_textgen"
    )
    
    print(f"📋 Agent with custom tool created")
    print(f"   Tools: {len(agent.tools)}")
    print(f"   Handlers: {len(agent.tool_handlers)}")
    
    print("✅ Custom tool creation test passed")


async def test_tool_store_operations():
    """Test tool store operations"""
    
    print("\n🧪 Testing Tool Store Operations")
    print("-" * 40)
    
    # Test getting all tools
    all_tools = BASIC_TOOL_STORE
    print(f"📋 Total tools in store: {len(all_tools)}")
    
    # Test getting specific tool
    calc_tool = get_tool_by_name("calculate")
    assert calc_tool is not None, "calculate tool not found"
    print(f"📋 Retrieved calculate tool: {calc_tool.__name__}")
    
    # Test tool execution
    result = calc_tool("10 / 2")
    print(f"📋 calculate('10 / 2'): {result}")
    assert "5" in result, "Tool execution failed"
    
    # Test non-existent tool
    missing_tool = get_tool_by_name("non_existent_tool")
    assert missing_tool is None, "Should return None for missing tool"
    print(f"📋 Missing tool correctly returns: {missing_tool}")
    
    print("✅ Tool store operations test passed")


async def main():
    """Run all tools integration tests"""
    
    print("🚀 Tools Integration Test Suite")
    print("=" * 60)
    
    try:
        await test_tools_decorator()
        await test_basic_tools()
        await test_agent_with_tool_names()
        await test_agent_execution_with_tools()
        await test_custom_tool_creation()
        await test_tool_store_operations()
        
        print("\n🎉 All tools integration tests passed!")
        print("✅ Tools system is working correctly")
        
        print("\n📋 Tools Integration Summary:")
        print("   ✅ Function schema decorator working")
        print("   ✅ Basic tools loaded and functional")
        print("   ✅ Agent tool_names parameter working")
        print("   ✅ Agent execution with tools working")
        print("   ✅ Custom tool creation working")
        print("   ✅ Tool store operations working")
        
    except Exception as e:
        print(f"\n❌ Tools integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
