#!/usr/bin/env python3
"""
API endpoint testing for async workflow execution with tracing.
Tests the actual FastAPI endpoints for workflow execution and monitoring.
"""

import asyncio
import aiohttp
import time
import json
import sys
from typing import Optional, Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:8005"  # Adjust based on your FastAPI server
POLL_INTERVAL = 2  # seconds
MAX_POLL_TIME = 120  # seconds


class WorkflowAPITester:
    """Test class for workflow API endpoints"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_server_health(self) -> bool:
        """Check if the FastAPI server is running"""
        if self.session is None:
            raise Exception("Session is None")
        try:
            async with self.session.get(f"{self.base_url}/docs") as response:
                return response.status == 200
        except Exception as e:
            print(f"❌ Server health check failed: {e}")
            return False

    async def get_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflows"""
        if self.session is None:
            raise Exception("Session is None")
        try:
            async with self.session.get(f"{self.base_url}/api/workflows/") as response:
                if response.status == 200:
                    workflows = await response.json()
                    return workflows
                else:
                    print(f"❌ Failed to get workflows: {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Error fetching workflows: {e}")
            return []

    async def execute_workflow_async(
        self,
        workflow_id: str,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Execute a workflow asynchronously"""
        payload = {
            "query": query,
            "session_id": session_id or f"test_session_{int(time.time())}",
            "user_id": user_id or "test_user",
            "chat_history": [],
        }
        if self.session is None:
            raise Exception("Session is None")

        try:
            async with self.session.post(
                f"{self.base_url}/api/workflows/{workflow_id}/execute/async",
                json=payload,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Workflow execution started: {result['execution_id']}")
                    return result
                else:
                    error_text = await response.text()
                    print(
                        f"❌ Failed to start workflow: {response.status} - {error_text}"
                    )
                    return None
        except Exception as e:
            print(f"❌ Error starting workflow execution: {e}")
            return None

    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution status"""
        if self.session is None:
            raise Exception("Session is None")
        try:
            async with self.session.get(
                f"{self.base_url}/api/executions/{execution_id}/status"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"❌ Failed to get execution status: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ Error getting execution status: {e}")
            return None

    async def get_execution_progress(
        self, execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get execution progress (optimized endpoint)"""
        if self.session is None:
            raise Exception("Session is None")
        try:
            async with self.session.get(
                f"{self.base_url}/api/executions/{execution_id}/progress"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception:
            return None

    async def get_execution_steps(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution steps for detailed monitoring"""
        if self.session is None:
            raise Exception("Session is None")
        try:
            async with self.session.get(
                f"{self.base_url}/api/executions/{execution_id}/steps"
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except Exception:
            return None

    async def get_execution_trace(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get full execution trace"""
        if self.session is None:
            raise Exception("Session is None")
        try:
            async with self.session.get(
                f"{self.base_url}/api/executions/{execution_id}/trace"
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 400:
                    print("ℹ️  Trace not available (not a workflow execution)")
                    return None
                else:
                    return None
        except Exception:
            return None

    async def get_execution_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution result"""
        if self.session is None:
            raise Exception("Session is None")
        try:
            async with self.session.get(
                f"{self.base_url}/api/executions/{execution_id}/result"
            ) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 202:
                    return {"status": "still_running"}
                else:
                    return None
        except Exception:
            return None

    async def monitor_execution(
        self, execution_id: str, show_detailed_steps: bool = True
    ) -> Dict[str, Any]:
        """Monitor execution with real-time updates including trace information"""
        print(f"🔍 Monitoring execution: {execution_id}")
        print("=" * 60)

        start_time = time.time()
        last_progress = -1
        last_step = ""
        step_history = []
        last_trace_update = 0
        displayed_decisions = set()

        while time.time() - start_time < MAX_POLL_TIME:
            # Get basic progress
            progress_data = await self.get_execution_progress(execution_id)

            if progress_data:
                current_progress = progress_data.get("progress", 0) or 0
                current_step = progress_data.get("current_step", "")
                status = progress_data.get("status", "unknown")

                # Show progress updates
                if current_progress != last_progress or current_step != last_step:
                    progress_bar = "█" * int(current_progress * 20) + "░" * (
                        20 - int(current_progress * 20)
                    )
                    print(
                        f"📊 Progress: [{progress_bar}] {current_progress*100:.1f}% | Status: {status}"
                    )

                    if current_step != last_step:
                        print(f"📍 Current Step: {current_step}")

                    # Show workflow-specific progress
                    if "workflow_progress" in progress_data:
                        wp = progress_data["workflow_progress"]
                        print(
                            f"🔄 Workflow Step: {wp.get('current_step_index', 0)}/{wp.get('total_steps', 0)}"
                        )

                        if wp.get("execution_path"):
                            path_str = " → ".join(wp["execution_path"])
                            print(f"🛤️  Execution Path: {path_str}")

                    last_progress = current_progress
                    last_step = current_step

                # Check if execution is complete
                if status in ["completed", "failed", "cancelled"]:
                    print(f"\\n✅ Execution {status.upper()}")
                    break

            # Get detailed steps if requested
            if show_detailed_steps:
                steps_data = await self.get_execution_steps(execution_id)
                if steps_data and steps_data.get("steps"):
                    current_steps = len(steps_data["steps"])
                    if current_steps != len(step_history):
                        new_steps = steps_data["steps"][len(step_history) :]
                        for step in new_steps:
                            status_emoji = {
                                "pending": "⏳",
                                "running": "🔄",
                                "completed": "✅",
                                "failed": "❌",
                                "skipped": "⏭️",
                            }
                            emoji = status_emoji.get(step["status"], "❓")
                            agent_info = (
                                f" - {step['agent_name']}" if step["agent_name"] else ""
                            )
                            print(
                                f"  {emoji} {step['step_type']}{agent_info} [{step['status']}]"
                            )

                        step_history = steps_data["steps"]

            # Get and display trace updates
            trace_data = await self.get_execution_trace(execution_id)
            if trace_data:
                current_trace_steps = len(trace_data.get('steps', []))
                
                # Show new branch decisions
                branch_decisions = trace_data.get('branch_decisions', {})
                for decision_key, decision_data in branch_decisions.items():
                    if decision_key not in displayed_decisions:
                        outcome = decision_data.get('outcome', 'N/A')
                        timestamp = decision_data.get('timestamp', '')
                        print(f"🌳 Branch Decision: {decision_key} → {outcome}")
                        displayed_decisions.add(decision_key)
                
                # Show execution path updates
                execution_path = trace_data.get('execution_path', [])
                if execution_path and current_trace_steps > last_trace_update:
                    current_path = " → ".join(execution_path)
                    if len(execution_path) > 1:  # Only show if there's an actual path
                        print(f"🔗 Live Execution Path: {current_path}")
                    
                    # Show step timing information for completed steps
                    steps = trace_data.get('steps', [])
                    for step in steps[last_trace_update:]:
                        if step.get('status') == 'completed' and step.get('duration_ms'):
                            step_name = step.get('agent_name') or step.get('step_type')
                            duration = step.get('duration_ms')
                            print(f"⏱️  {step_name}: {duration}ms")
                    
                    last_trace_update = current_trace_steps

            await asyncio.sleep(POLL_INTERVAL)

        else:
            print(f"\\n⏰ Monitoring timeout after {MAX_POLL_TIME} seconds")

        # Get final results
        final_status = await self.get_execution_status(execution_id)
        final_trace = await self.get_execution_trace(execution_id)
        final_result = await self.get_execution_result(execution_id)

        return {
            "execution_id": execution_id,
            "final_status": final_status,
            "final_trace": final_trace,
            "final_result": final_result,
            "monitoring_duration": time.time() - start_time,
        }

    async def test_workflow_execution(
        self, workflow_id: str, query: str
    ) -> Dict[str, Any]:
        """Complete test of workflow execution with monitoring"""
        print("🚀 Testing Workflow Execution")
        print(f"Workflow ID: {workflow_id}")
        print(f"Query: {query}")
        print("=" * 60)

        # Start execution
        execution_response = await self.execute_workflow_async(workflow_id, query)
        if not execution_response:
            return {"success": False, "error": "Failed to start execution"}

        execution_id = execution_response["execution_id"]

        # Monitor execution
        monitoring_result = await self.monitor_execution(
            execution_id, show_detailed_steps=True
        )

        # Display detailed results
        print("\\n" + "=" * 60)
        print("📋 EXECUTION SUMMARY")
        print("=" * 60)

        final_status = monitoring_result.get("final_status")
        if final_status:
            print(f"Status: {final_status.get('status', 'unknown')}")
            print(f"Progress: {(final_status.get('progress', 0) or 0) * 100:.1f}%")
            print(
                f"Duration: {monitoring_result.get('monitoring_duration', 0):.1f} seconds"
            )

        final_trace = monitoring_result.get("final_trace")
        if final_trace:
            print("\\n🔍 Complete Trace Analysis:")
            print(f"  Total Steps: {final_trace.get('total_steps', 0)}")
            print(f"  Steps Completed: {final_trace.get('current_step_index', 0)}")
            
            execution_path = final_trace.get('execution_path', [])
            if execution_path:
                print(f"  Full Execution Path: {' → '.join(execution_path)}")
            
            # Show detailed step breakdown
            steps = final_trace.get('steps', [])
            if steps:
                print("\\n📋 Detailed Step Breakdown:")
                total_duration = 0
                for i, step in enumerate(steps, 1):
                    status_emoji = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌", "skipped": "⏭️"}
                    emoji = status_emoji.get(step.get('status'), '❓')
                    
                    step_name = step.get('agent_name') or step.get('step_type', 'Unknown')
                    duration = step.get('duration_ms', 0) or 0
                    total_duration += duration
                    
                    duration_str = f" ({duration}ms)" if duration > 0 else ""
                    error_str = f" - ERROR: {step.get('error')}" if step.get('error') else ""
                    
                    print(f"    {i:2}. {emoji} {step_name}{duration_str}{error_str}")
                    
                    # Show input/output data if available
                    if step.get('input_data') and len(str(step['input_data'])) < 100:
                        print(f"        Input: {step['input_data']}")
                    if step.get('output_data') and len(str(step['output_data'])) < 100:
                        print(f"        Output: {step['output_data']}")
                
                if total_duration > 0:
                    print(f"\\n⏱️  Total Step Duration: {total_duration}ms ({total_duration/1000:.2f}s)")

            # Show branch decisions with timestamps
            if final_trace.get("branch_decisions"):
                print("\\n🌳 Branch Decision Details:")
                for decision, outcome_data in final_trace["branch_decisions"].items():
                    outcome = outcome_data.get('outcome', 'N/A')
                    timestamp = outcome_data.get('timestamp', '')
                    print(f"    • {decision}: {outcome}")
                    if timestamp:
                        print(f"      └─ Decided at: {timestamp}")

            # Show workflow metadata if available
            workflow_id = final_trace.get('workflow_id')
            if workflow_id:
                print("\\n📋 Workflow Metadata:")
                print(f"    Workflow ID: {workflow_id}")
                print(f"    Execution ID: {final_trace.get('execution_id', 'N/A')}")

        final_result = monitoring_result.get("final_result")
        if final_result and final_result != {"status": "still_running"}:
            print("\\n📋 Final Result:")
            if isinstance(final_result, dict):
                if "response" in final_result:
                    response_preview = str(final_result["response"])[:200]
                    print(f"  Response: {response_preview}...")
                else:
                    print(f"  {json.dumps(final_result, indent=2)[:300]}...")

        return {
            "success": True,
            "execution_id": execution_id,
            "monitoring_result": monitoring_result,
        }

    async def run_comprehensive_api_tests(self):
        """Run comprehensive API endpoint tests"""
        print("🌐 Comprehensive Workflow API Testing")
        print("=" * 60)

        # Check server health
        print("🏥 Checking server health...")
        if not await self.check_server_health():
            print(
                "❌ Server is not accessible. Please ensure FastAPI server is running."
            )
            print(f"   Expected server at: {self.base_url}")
            return

        print("✅ Server is accessible")

        # Get available workflows
        print("\\n📋 Fetching available workflows...")
        workflows = await self.get_workflows()

        if not workflows:
            print("❌ No workflows available for testing")
            return

        print(f"✅ Found {len(workflows)} workflows")

        # Test simple workflow (single agent)
        simple_workflows = [
            w
            for w in workflows
            if len(w.get("configuration", {}).get("agents", [])) == 1
        ]
        if simple_workflows:
            workflow = simple_workflows[0]
            print(f"\\n🧪 Testing Simple Workflow: {workflow['name']}")
            await self.test_workflow_execution(
                str(workflow["workflow_id"]), f"API test of {workflow['name']}"
            )

        # Test complex workflow (multi-agent)
        complex_workflows = [
            w
            for w in workflows
            if len(w.get("configuration", {}).get("agents", [])) > 1
        ]
        if complex_workflows:
            workflow = complex_workflows[0]
            print(f"\\n🧪 Testing Complex Workflow: {workflow['name']}")
            await self.test_workflow_execution(
                str(workflow["workflow_id"]), f"API test of {workflow['name']}"
            )

        print("\\n🎉 API testing completed!")

    async def monitor_trace_only(self, execution_id: str):
        """Monitor only trace information for an execution"""
        print(f"🔍 Monitoring Trace for Execution: {execution_id}")
        print("=" * 60)
        
        start_time = time.time()
        displayed_decisions = set()
        last_step_count = 0
        
        while time.time() - start_time < MAX_POLL_TIME:
            # Get trace data
            trace_data = await self.get_execution_trace(execution_id)
            if not trace_data:
                print("⚠️  No trace data available - checking execution status...")
                status_data = await self.get_execution_status(execution_id)
                if status_data:
                    print(f"📊 Status: {status_data.get('status', 'unknown')}")
                    if status_data.get('status') in ['completed', 'failed', 'cancelled']:
                        break
                await asyncio.sleep(POLL_INTERVAL)
                continue
            
            # Show execution progress
            current_step_index = trace_data.get('current_step_index', 0)
            total_steps = trace_data.get('total_steps', 0)
            
            if total_steps > 0:
                progress = current_step_index / total_steps
                progress_bar = "█" * int(progress * 30) + "░" * (30 - int(progress * 30))
                print(f"🔄 Trace Progress: [{progress_bar}] {current_step_index}/{total_steps}")
            
            # Show new steps
            steps = trace_data.get('steps', [])
            if len(steps) > last_step_count:
                new_steps = steps[last_step_count:]
                for step in new_steps:
                    status_emoji = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌", "skipped": "⏭️"}
                    emoji = status_emoji.get(step.get('status'), '❓')
                    step_name = step.get('agent_name') or step.get('step_type', 'Unknown')
                    
                    duration_str = ""
                    if step.get('duration_ms'):
                        duration_str = f" ({step['duration_ms']}ms)"
                    
                    print(f"  {emoji} {step_name} [{step.get('status')}]{duration_str}")
                
                last_step_count = len(steps)
            
            # Show new branch decisions
            branch_decisions = trace_data.get('branch_decisions', {})
            for decision_key, decision_data in branch_decisions.items():
                if decision_key not in displayed_decisions:
                    outcome = decision_data.get('outcome', 'N/A')
                    print(f"🌳 Decision: {decision_key} → {outcome}")
                    displayed_decisions.add(decision_key)
            
            # Show execution path
            execution_path = trace_data.get('execution_path', [])
            if execution_path:
                print(f"🛤️  Path: {' → '.join(execution_path)}")
            
            await asyncio.sleep(POLL_INTERVAL)
        
        print("\\n🎯 Trace monitoring completed")


async def main():
    """Main async test runner"""
    import argparse

    parser = argparse.ArgumentParser(description="Workflow API Testing")
    parser.add_argument("--url", default=API_BASE_URL, help="FastAPI server URL")
    parser.add_argument("--workflow-id", "-w", help="Test specific workflow by ID")
    parser.add_argument("--query", "-q", default="API test query", help="Custom query")
    parser.add_argument("--monitor-only", "-m", help="Monitor existing execution by ID")
    parser.add_argument("--trace-only", "-t", help="Monitor only trace data for execution by ID")

    args = parser.parse_args()

    async with WorkflowAPITester(args.url) as tester:
        if args.monitor_only:
            await tester.monitor_execution(args.monitor_only)

        elif args.trace_only:
            await tester.monitor_trace_only(args.trace_only)

        elif args.workflow_id:
            await tester.test_workflow_execution(args.workflow_id, args.query)

        else:
            await tester.run_comprehensive_api_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n🛑 Testing interrupted by user")
    except Exception as e:
        print(f"\\n❌ Test failed: {e}")
        sys.exit(1)
