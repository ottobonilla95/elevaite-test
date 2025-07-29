#!/usr/bin/env python3
"""
Test script for Agent API and Analytics endpoints.
Tests agent execution and retrieves detailed analytics in parallel.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, Any, Optional
import argparse


class AgentAnalyticsTest:
    def __init__(self, base_url: str = "http://localhost:8005"):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_agents(self) -> list:
        """Get list of available agents."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        async with self.session.get(f"{self.base_url}/api/agents/") as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to get agents: {response.status}")
                return []

    async def get_workflows(self) -> list:
        """Get list of available workflows."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        async with self.session.get(f"{self.base_url}/api/workflows/") as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to get workflows: {response.status}")
                return []

    async def get_agent_schema(self, agent_id: str) -> Dict[str, Any]:
        """Get OpenAI schema for an agent."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        async with self.session.get(
            f"{self.base_url}/api/agents/{agent_id}/schema"
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to get agent schema: {response.status}")
                return {}

    async def execute_agent(
        self, agent_id: str, query: str, session_id: str
    ) -> Dict[str, Any]:
        """Execute an agent with a query."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        payload = {
            "query": query,
            "session_id": session_id,
            "user_id": "test_user",
            "chat_history": [],
            "enable_analytics": True,  # Enable analytics to track execution
        }

        print(f"🚀 Executing agent {agent_id} with query: '{query}'")
        start_time = time.time()

        async with self.session.post(
            f"{self.base_url}/api/agents/{agent_id}/execute", json=payload
        ) as response:
            end_time = time.time()
            duration = end_time - start_time

            if response.status == 200:
                result = await response.json()
                print(f"✅ Agent execution completed in {duration:.2f}s")
                print(f"📄 Agent Response: {json.dumps(result, indent=2)}")
                return {
                    "success": True,
                    "result": result,
                    "duration": duration,
                    "execution_id": result.get("execution_id"),  # If returned by API
                }
            else:
                error_text = await response.text()
                print(f"❌ Agent execution failed: {response.status} - {error_text}")
                return {"success": False, "error": error_text, "duration": duration}

    async def execute_agent_stream(
        self, agent_id: str, query: str, session_id: str
    ) -> Dict[str, Any]:
        """Execute an agent with streaming response."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        payload = {"query": query, "chat_history": []}

        print(f"🌊 Executing agent {agent_id} with streaming for query: '{query}'")
        start_time = time.time()
        chunks = []

        async with self.session.post(
            f"{self.base_url}/api/agents/{agent_id}/execute/stream", json=payload
        ) as response:
            if response.status == 200:
                async for line in response.content:
                    if line:
                        line_str = line.decode("utf-8").strip()
                        if line_str.startswith("data: "):
                            try:
                                data = json.loads(
                                    line_str[6:]
                                )  # Remove 'data: ' prefix
                                chunks.append(data)
                                print(
                                    f"📦 Received chunk: {data.get('type', 'unknown')}"
                                )
                            except json.JSONDecodeError:
                                pass

                end_time = time.time()
                duration = end_time - start_time
                print(f"✅ Streaming execution completed in {duration:.2f}s")
                return {"success": True, "chunks": chunks, "duration": duration}
            else:
                error_text = await response.text()
                print(
                    f"❌ Streaming execution failed: {response.status} - {error_text}"
                )
                return {
                    "success": False,
                    "error": error_text,
                    "duration": time.time() - start_time,
                }

    async def execute_workflow(
        self, workflow_id: str, query: str, session_id: str
    ) -> Dict[str, Any]:
        """Execute a workflow with a query."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        payload = {
            "query": query,
            "chat_history": [],
            "runtime_overrides": {},
            "session_id": session_id,
            "user_id": "test_user",
        }

        print(f"🔄 Executing workflow {workflow_id} with query: '{query}'")
        start_time = time.time()

        async with self.session.post(
            f"{self.base_url}/api/workflows/{workflow_id}/execute", json=payload
        ) as response:
            end_time = time.time()
            duration = end_time - start_time

            if response.status == 200:
                result = await response.json()
                print(f"✅ Workflow execution completed in {duration:.2f}s")
                print(f"📄 Workflow Response: {json.dumps(result, indent=2)}")
                return {
                    "success": True,
                    "result": result,
                    "duration": duration,
                    "execution_id": result.get("execution_id"),
                }
            else:
                error_text = await response.text()
                print(f"❌ Workflow execution failed: {response.status} - {error_text}")
                return {"success": False, "error": error_text, "duration": duration}

    async def execute_workflow_stream(
        self, workflow_id: str, query: str, session_id: str
    ) -> Dict[str, Any]:
        """Execute a workflow with streaming response."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        payload = {
            "query": query,
            "chat_history": [],
            "runtime_overrides": {},
            "session_id": session_id,
            "user_id": "test_user",
        }

        print(
            f"🌊 Executing workflow {workflow_id} with streaming for query: '{query}'"
        )
        start_time = time.time()
        chunks = []

        async with self.session.post(
            f"{self.base_url}/api/workflows/{workflow_id}/stream", json=payload
        ) as response:
            if response.status == 200:
                async for line in response.content:
                    if line:
                        line_str = line.decode("utf-8").strip()
                        if line_str.startswith("data: "):
                            try:
                                data = json.loads(
                                    line_str[6:]
                                )  # Remove 'data: ' prefix
                                chunks.append(data)
                                print(
                                    f"📦 Received chunk: {data.get('type', 'unknown')}"
                                )
                            except json.JSONDecodeError:
                                pass

                end_time = time.time()
                duration = end_time - start_time
                print(f"✅ Streaming workflow execution completed in {duration:.2f}s")
                return {"success": True, "chunks": chunks, "duration": duration}
            else:
                error_text = await response.text()
                print(
                    f"❌ Streaming workflow execution failed: {response.status} - {error_text}"
                )
                return {
                    "success": False,
                    "error": error_text,
                    "duration": time.time() - start_time,
                }

    async def get_analytics_summary(self, days: int = 1) -> Dict[str, Any]:
        """Get analytics summary."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        async with self.session.get(
            f"{self.base_url}/api/analytics/summary?days={days}"
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"📊 Analytics Summary Response: {json.dumps(result, indent=2)}")
                return result
            else:
                print(f"Failed to get analytics summary: {response.status}")
                return {}

    async def get_agent_usage_stats(self, days: int = 1) -> list:
        """Get agent usage statistics."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        async with self.session.get(
            f"{self.base_url}/api/analytics/agents/usage?days={days}"
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"Failed to get agent usage stats: {response.status}")
                return []

    async def get_execution_details(self, execution_id: str) -> Dict[str, Any]:
        """Get detailed execution information."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        async with self.session.get(
            f"{self.base_url}/api/analytics/executions/{execution_id}"
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"📋 Execution Details Response: {json.dumps(result, indent=2)}")
                return result
            elif response.status == 404:
                print(f"⚠️  Execution {execution_id} not found yet")
                return {}
            else:
                print(f"Failed to get execution details: {response.status}")
                return {}

    async def get_session_details(self, session_id: str) -> Dict[str, Any]:
        """Get detailed session information."""
        if not self.session:
            raise RuntimeError(
                "Session not initialized. Use 'async with' context manager."
            )

        async with self.session.get(
            f"{self.base_url}/api/analytics/sessions/{session_id}"
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"👤 Session Details Response: {json.dumps(result, indent=2)}")
                return result
            elif response.status == 404:
                print(f"⚠️  Session {session_id} not found yet")
                return {}
            else:
                print(f"Failed to get session details: {response.status}")
                return {}

    async def monitor_analytics_during_execution(
        self, session_id: str, duration: float
    ):
        """Monitor analytics while execution is happening."""
        print(f"📊 Starting analytics monitoring for {duration:.1f}s...")

        start_time = time.time()
        while time.time() - start_time < duration + 5:  # Monitor a bit longer
            await asyncio.sleep(2)  # Check every 2 seconds

            # Get current analytics
            stats = await self.get_agent_usage_stats(days=1)
            if stats:
                print(
                    f"📈 Current agent stats: {len(stats)} agents have recent activity"
                )
                for stat in stats[:3]:  # Show top 3
                    print(
                        f"   - {stat.get('agent_name', 'Unknown')}: "
                        f"{stat.get('total_executions', 0)} executions, "
                        f"{stat.get('success_rate', 0):.1%} success rate"
                    )

    def print_execution_details(self, details: Dict[str, Any]):
        """Pretty print execution details."""
        if not details:
            print("❌ No execution details available")
            return

        print("\n" + "=" * 60)
        print("📋 EXECUTION DETAILS")
        print("=" * 60)
        print(f"Execution ID: {details.get('execution_id', 'N/A')}")
        print(
            f"Agent: {details.get('agent_name', 'N/A')} ({details.get('agent_id', 'N/A')})"
        )
        print(f"Status: {details.get('status', 'N/A')}")
        print(f"Query: {details.get('query', 'N/A')}")
        print(f"Start Time: {details.get('start_time', 'N/A')}")
        print(f"End Time: {details.get('end_time', 'N/A')}")
        print(f"Duration: {details.get('duration_ms', 'N/A')}ms")
        print(f"Tool Count: {details.get('tool_count', 0)}")
        print(f"Retry Count: {details.get('retry_count', 0)}")
        print(f"API Calls: {details.get('api_calls_count', 0)}")
        print(f"Tokens Used: {details.get('tokens_used', 'N/A')}")
        print(f"Session ID: {details.get('session_id', 'N/A')}")
        print(f"User ID: {details.get('user_id', 'N/A')}")

        if details.get("tools_called"):
            print(f"\n🔧 Tools Called:")
            tools = details["tools_called"]
            if isinstance(tools, dict):
                for tool_name, tool_data in tools.items():
                    print(f"   - {tool_name}: {tool_data}")
            else:
                print(f"   {tools}")

        if details.get("error_message"):
            print(f"\n❌ Error: {details['error_message']}")

        if details.get("response"):
            response = details["response"]
            if len(response) > 200:
                response = response[:200] + "..."
            print(f"\n💬 Response: {response}")

    def print_session_details(self, details: Dict[str, Any]):
        """Pretty print session details."""
        if not details:
            print("❌ No session details available")
            return

        print("\n" + "=" * 60)
        print("👤 SESSION DETAILS")
        print("=" * 60)
        print(f"Session ID: {details.get('session_id', 'N/A')}")
        print(f"User ID: {details.get('user_id', 'N/A')}")
        print(f"Start Time: {details.get('start_time', 'N/A')}")
        print(f"End Time: {details.get('end_time', 'N/A')}")
        print(f"Duration: {details.get('duration_ms', 'N/A')}ms")
        print(f"Total Interactions: {details.get('total_interactions', 0)}")
        print(f"Unique Agents Used: {details.get('unique_agents_used', 0)}")
        print(f"Total Tool Calls: {details.get('total_tool_calls', 0)}")

    async def run_comprehensive_test(
        self, agent_id: Optional[str] = None, use_streaming: bool = False
    ):
        """Run a comprehensive test of agent execution and analytics."""
        print("🧪 Starting Comprehensive Agent Analytics Test")
        print("=" * 60)

        # Get available agents if no specific agent provided
        if not agent_id:
            agents = await self.get_agents()
            if not agents:
                print("❌ No agents available for testing")
                return

            agent_id = agents[0]["agent_id"]
            print(f"🤖 Using first available agent: {agents[0]['name']} ({agent_id})")

        # At this point agent_id is guaranteed to be a string
        assert agent_id is not None, "agent_id should not be None at this point"

        # Get agent schema
        print(f"\n📋 Getting agent schema...")
        schema = await self.get_agent_schema(agent_id)
        if schema:
            print(f"✅ Agent Schema Retrieved:")
            print(f"   Name: {schema.get('name', 'N/A')}")
            print(f"   Model: {schema.get('model', 'N/A')}")
            print(f"   Tools: {len(schema.get('tools', []))}")
            print(f"   Temperature: {schema.get('temperature', 'N/A')}")

        # Generate unique session ID
        session_id = f"test_session_{int(time.time())}"

        # Test queries
        test_queries = [
            "Hello, can you help me with a simple task?",
            "What's the weather like today?",
            "Can you add 5 and 3 for me?",
        ]

        for i, query in enumerate(test_queries, 1):
            print(f"\n🔄 Test {i}/{len(test_queries)}")
            print("-" * 40)

            # Start analytics monitoring in parallel
            if use_streaming:
                execution_task = asyncio.create_task(
                    self.execute_agent_stream(agent_id, query, session_id)
                )
            else:
                execution_task = asyncio.create_task(
                    self.execute_agent(agent_id, query, session_id)
                )

            # Monitor analytics while execution runs
            monitor_task = asyncio.create_task(
                self.monitor_analytics_during_execution(session_id, 10)
            )

            # Wait for execution to complete
            execution_result = await execution_task
            monitor_task.cancel()  # Stop monitoring

            # Wait a moment for analytics to be recorded
            await asyncio.sleep(3)

            # Get updated analytics
            print(f"\n📊 Retrieving analytics after execution...")
            summary = await self.get_analytics_summary(days=1)
            if summary:
                agent_stats = summary.get("agent_stats", [])
                print(
                    f"📈 Analytics Summary: {len(agent_stats)} agents with recent activity"
                )

            # Try to get execution details (may not be available immediately)
            if execution_result.get("execution_id"):
                execution_details = await self.get_execution_details(
                    execution_result["execution_id"]
                )
                self.print_execution_details(execution_details)

        # Get final session details
        print(f"\n🔍 Retrieving final session details...")
        await asyncio.sleep(2)  # Wait for session to be recorded
        session_details = await self.get_session_details(session_id)
        self.print_session_details(session_details)

        # Final analytics summary
        print(f"\n📊 Final Analytics Summary")
        print("-" * 40)
        final_summary = await self.get_analytics_summary(days=1)
        if final_summary:
            print(f"Agent Stats: {len(final_summary.get('agent_stats', []))}")
            print(f"Tool Stats: {len(final_summary.get('tool_stats', []))}")
            print(f"Error Summary: {final_summary.get('error_summary', {})}")


async def main():
    parser = argparse.ArgumentParser(description="Test Agent API and Analytics")
    parser.add_argument(
        "--base-url", default="http://localhost:8005", help="Base URL for the API"
    )
    parser.add_argument("--agent-id", help="Specific agent ID to test")
    parser.add_argument(
        "--streaming", action="store_true", help="Use streaming execution"
    )

    args = parser.parse_args()

    async with AgentAnalyticsTest(args.base_url) as test:
        await test.run_comprehensive_test(
            agent_id=args.agent_id, use_streaming=args.streaming
        )


async def quick_test():
    """Quick test function for immediate execution."""
    async with AgentAnalyticsTest() as test:
        # Get first available agent
        agents = await test.get_agents()
        if not agents:
            print("❌ No agents available")
            return

        agent = agents[0]
        agent_id = agent["agent_id"]

        print(f"🤖 Testing agent: {agent['name']}")

        # Test execution
        session_id = f"quick_test_{int(time.time())}"
        result = await test.execute_agent(
            agent_id, "Hello, this is a test query", session_id
        )

        print(
            f"✅ Execution result: {'Success' if result.get('success') else 'Failed'}"
        )

        # Wait for analytics to be recorded
        await asyncio.sleep(3)

        # Get analytics
        summary = await test.get_analytics_summary(days=1)
        print(f"\n📊 Analytics Summary:")
        print(f"   Agent Stats: {len(summary.get('agent_stats', []))}")
        print(f"   Tool Stats: {len(summary.get('tool_stats', []))}")

        # Try to get session details
        session_details = await test.get_session_details(session_id)
        test.print_session_details(session_details)


async def workflow_test():
    """Test workflow execution and analytics."""
    async with AgentAnalyticsTest() as test:
        # Get first available workflow
        workflows = await test.get_workflows()
        if not workflows:
            print("❌ No workflows available")
            return

        workflow = workflows[0]
        workflow_id = workflow["workflow_id"]

        print(f"🔄 Testing workflow: {workflow['name']}")

        # Test execution
        session_id = f"workflow_test_{int(time.time())}"
        result = await test.execute_workflow(
            workflow_id, "Hello, this is a workflow test query", session_id
        )

        print(
            f"✅ Workflow execution result: {'Success' if result.get('success') else 'Failed'}"
        )

        if result.get("execution_id"):
            print(f"📋 Execution ID: {result['execution_id']}")

        # Wait for analytics to be recorded
        await asyncio.sleep(3)

        # Get analytics
        summary = await test.get_analytics_summary(days=1)
        print(f"\n📊 Workflow Analytics Summary:")
        print(f"   Agent Stats: {len(summary.get('agent_stats', []))}")
        print(f"   Tool Stats: {len(summary.get('tool_stats', []))}")
        print(f"   Workflow Stats: {len(summary.get('workflow_stats', []))}")

        # Try to get session details
        session_details = await test.get_session_details(session_id)
        test.print_session_details(session_details)


def run_quick_test():
    """Synchronous wrapper for quick test."""
    asyncio.run(quick_test())


def run_workflow_test():
    """Synchronous wrapper for workflow test."""
    asyncio.run(workflow_test())


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        run_quick_test()
    elif len(sys.argv) > 1 and sys.argv[1] == "workflow":
        run_workflow_test()
    else:
        asyncio.run(main())
