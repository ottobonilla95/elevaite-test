"""
Debug Single Agent Execution

Interactive debugging script for testing individual agent configurations
and tool usage. Useful for development and troubleshooting.
"""

import asyncio
import os

from workflow_engine_poc.agent_steps import SimpleAgent
from workflow_engine_poc.tools import BASIC_TOOL_STORE


async def debug_agent_creation():
    """Debug agent creation with different configurations"""
    
    print("🔧 Debug: Agent Creation")
    print("-" * 40)
    
    # Test basic agent
    print("📋 Creating basic agent...")
    basic_agent = SimpleAgent(
        name="Debug Basic Agent",
        model="gpt-4o-mini",
        system_prompt="You are a debug assistant.",
        provider_type="openai_textgen"
    )
    print(f"   ✅ Basic agent created: {basic_agent.name}")
    print(f"   📊 Tools: {len(basic_agent.tools)}")
    print(f"   🔧 Handlers: {len(basic_agent.tool_handlers)}")
    
    # Test agent with tools
    print("\n📋 Creating agent with tools...")
    tool_agent = SimpleAgent(
        name="Debug Tool Agent",
        model="gpt-4o-mini",
        system_prompt="You are a debug assistant with tools.",
        tool_names=["add_numbers", "calculate", "get_current_time"],
        provider_type="openai_textgen"
    )
    print(f"   ✅ Tool agent created: {tool_agent.name}")
    print(f"   📊 Tools: {len(tool_agent.tools)}")
    print(f"   🔧 Handlers: {len(tool_agent.tool_handlers)}")
    
    # List available tools
    print(f"\n📋 Available tools in store: {len(BASIC_TOOL_STORE)}")
    for tool_name in BASIC_TOOL_STORE.keys():
        print(f"   - {tool_name}")
    
    return basic_agent, tool_agent


async def debug_agent_execution(agent: SimpleAgent, queries: list):
    """Debug agent execution with detailed logging"""
    
    print(f"\n🔧 Debug: Agent Execution - {agent.name}")
    print("-" * 40)
    
    for i, query in enumerate(queries, 1):
        print(f"\n📋 Query {i}: {query}")
        
        try:
            # Execute with detailed timing
            import time
            start_time = time.time()
            
            result = await agent.execute(query)
            
            execution_time = time.time() - start_time
            
            # Detailed result analysis
            print(f"   ✅ Success: {result.get('success', False)}")
            print(f"   ⏱️  Execution time: {execution_time:.3f}s")
            print(f"   📝 Response length: {len(result.get('response', ''))}")
            print(f"   🔧 Tools available: {len(result.get('tools_used', []))}")
            
            if result.get('response'):
                response = result['response']
                print(f"   📄 Response preview: {response[:150]}...")
            
            if result.get('tools_used'):
                print(f"   🛠️  Tools in context: {len(result['tools_used'])}")
                for tool in result['tools_used'][:3]:  # Show first 3
                    tool_name = tool.get('function', {}).get('name', 'unknown')
                    print(f"      - {tool_name}")
            
            if result.get('error'):
                print(f"   ❌ Error: {result['error']}")
            
        except Exception as e:
            print(f"   💥 Exception: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()


async def debug_tool_execution():
    """Debug individual tool execution"""
    
    print("\n🔧 Debug: Tool Execution")
    print("-" * 40)
    
    # Test individual tools
    test_cases = [
        ("add_numbers", {"a": 15, "b": 27}),
        ("calculate", {"expression": "8 * 7 + 12"}),
        ("get_current_time", {"timezone": "UTC"}),
        ("weather_forecast", {"location": "San Francisco", "days": 1}),
    ]
    
    for tool_name, args in test_cases:
        print(f"\n📋 Testing tool: {tool_name}")
        print(f"   Args: {args}")
        
        try:
            tool_func = BASIC_TOOL_STORE.get(tool_name)
            if tool_func:
                result = tool_func(**args)
                print(f"   ✅ Result: {result}")
            else:
                print(f"   ❌ Tool not found: {tool_name}")
                
        except Exception as e:
            print(f"   💥 Error: {type(e).__name__}: {e}")


async def debug_provider_types():
    """Debug different provider types"""
    
    print("\n🔧 Debug: Provider Types")
    print("-" * 40)
    
    providers = [
        ("openai_textgen", "gpt-4o-mini"),
        ("gemini_textgen", "gemini-1.5-flash"),
        ("bedrock_textgen", "anthropic.claude-3-sonnet-20240229-v1:0"),
    ]
    
    for provider_type, model in providers:
        print(f"\n📋 Testing provider: {provider_type}")
        print(f"   Model: {model}")
        
        try:
            agent = SimpleAgent(
                name=f"Debug {provider_type} Agent",
                model=model,
                system_prompt="You are a test agent.",
                tool_names=["add_numbers"],
                provider_type=provider_type
            )
            
            result = await agent.execute("What is 5 + 3?")
            
            print(f"   ✅ Success: {result.get('success', False)}")
            print(f"   📝 Response: {result.get('response', '')[:100]}...")
            
        except Exception as e:
            print(f"   💥 Error: {type(e).__name__}: {e}")


async def interactive_debug():
    """Interactive debugging session"""
    
    print("\n🔧 Interactive Debug Session")
    print("-" * 40)
    print("Enter queries to test with the debug agent (type 'quit' to exit)")
    
    # Create a debug agent
    agent = SimpleAgent(
        name="Interactive Debug Agent",
        model="gpt-4o-mini",
        system_prompt="You are an interactive debug assistant with access to tools.",
        tool_names=["add_numbers", "calculate", "get_current_time", "weather_forecast"],
        provider_type="openai_textgen"
    )
    
    print(f"📋 Agent ready: {agent.name}")
    print(f"   Tools available: {len(agent.tools)}")
    
    while True:
        try:
            query = input("\n🔍 Enter query: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            print(f"📋 Processing: {query}")
            
            import time
            start_time = time.time()
            result = await agent.execute(query)
            execution_time = time.time() - start_time
            
            print(f"   ✅ Success: {result.get('success', False)}")
            print(f"   ⏱️  Time: {execution_time:.3f}s")
            print(f"   📝 Response: {result.get('response', '')}")
            
            if result.get('error'):
                print(f"   ❌ Error: {result['error']}")
            
        except KeyboardInterrupt:
            print("\n👋 Exiting interactive session...")
            break
        except Exception as e:
            print(f"   💥 Error: {type(e).__name__}: {e}")


async def main():
    """Main debug function"""
    
    print("🚀 Agent Debug Suite")
    print("=" * 50)
    
    # Check environment
    print("📋 Environment Check:")
    api_keys = {
        "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
        "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY")),
        "AWS_ACCESS_KEY_ID": bool(os.getenv("AWS_ACCESS_KEY_ID")),
    }
    
    for key, available in api_keys.items():
        status = "✅ Set" if available else "❌ Not set"
        print(f"   {key}: {status}")
    
    if not any(api_keys.values()):
        print("   ⚠️  No API keys found - running in simulation mode")
    
    # Run debug tests
    basic_agent, tool_agent = await debug_agent_creation()
    
    # Test queries
    test_queries = [
        "Hello, how are you?",
        "What is 15 + 27?",
        "Calculate 8 * 7 + 12",
        "What time is it?",
        "What's the weather like in Tokyo?",
    ]
    
    await debug_agent_execution(basic_agent, test_queries[:2])
    await debug_agent_execution(tool_agent, test_queries)
    
    await debug_tool_execution()
    await debug_provider_types()
    
    # Interactive session (commented out for automated testing)
    # await interactive_debug()
    
    print("\n🎉 Debug session completed!")
    print("📋 Use the interactive mode to test custom queries")


if __name__ == "__main__":
    asyncio.run(main())
