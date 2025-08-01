#!/usr/bin/env python3
"""
Comprehensive test suite for async workflow execution with tracing.
Supports both mock testing and real workflow integration testing.
"""

import sys
import os
import asyncio
import time
import uuid
from typing import Optional, List, Dict, Any

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.execution_manager import execution_manager, WorkflowStep
from db.database import get_db
from db import crud, schemas
from datetime import datetime, timedelta

class WorkflowTester:
    """Comprehensive workflow testing class"""
    
    def __init__(self):
        self.db = None
        
    def setup_db(self):
        """Setup database connection"""
        try:
            self.db = next(get_db())
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def cleanup_db(self):
        """Cleanup database connection"""
        if self.db:
            self.db.close()
    
    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """Get list of available workflows from database"""
        if not self.db:
            return []
        
        try:
            workflows = crud.get_workflows(self.db, skip=0, limit=20)
            workflow_list = []
            
            for w in workflows:
                agents = w.configuration.get("agents", [])
                workflow_info = {
                    "id": str(w.workflow_id),
                    "name": w.name,
                    "description": w.description or "No description",
                    "agent_count": len(agents),
                    "agent_types": [agent.get("agent_type") for agent in agents],
                    "is_deployed": w.is_deployed,
                    "is_active": w.is_active
                }
                workflow_list.append(workflow_info)
            
            return workflow_list
        except Exception as e:
            print(f"❌ Error fetching workflows: {e}")
            return []
    
    def display_available_workflows(self):
        """Display available workflows for selection"""
        workflows = self.get_available_workflows()
        
        if not workflows:
            print("❌ No workflows found in database")
            return workflows
        
        print("📋 Available Workflows:")
        print("=" * 60)
        
        for i, w in enumerate(workflows, 1):
            agent_types_str = ", ".join(w["agent_types"]) if w["agent_types"] else "None"
            status = "🟢 Active" if w["is_active"] else "🔴 Inactive"
            deployed = "✅ Deployed" if w["is_deployed"] else "❌ Not Deployed"
            
            print(f"{i:2}. {w['name']}")
            print(f"    ID: {w['id']}")
            print(f"    Description: {w['description'][:80]}...")
            print(f"    Agents: {w['agent_count']} ({agent_types_str})")
            print(f"    Status: {status} | {deployed}")
            print()
        
        return workflows
    
    def test_mock_workflow_tracing(self):
        """Test workflow tracing functionality with mock data"""
        print("🧪 Testing Mock Workflow Tracing")
        print("=" * 50)
        
        # Create a test execution
        execution_id = execution_manager.create_execution(
            execution_type="workflow",
            workflow_id="mock-workflow-test",
            user_id="test_user",
            query="Mock workflow execution test"
        )
        
        print(f"✅ Created mock execution: {execution_id}")
        
        # Initialize workflow trace
        success = execution_manager.init_workflow_trace(execution_id, "mock-workflow-test", 4)
        print(f"✅ Initialized workflow trace: {success}")
        
        # Add and execute workflow steps
        steps = [
            ("init_step", "data_processing", None, "Initialize workflow"),
            ("agent_step_1", "agent_execution", "CommandAgent", "Execute orchestrator"),
            ("agent_step_2", "agent_execution", "DataAgent", "Process data"),
            ("final_step", "data_processing", None, "Finalize results")
        ]
        
        for step_id, step_type, agent_name, description in steps:
            step = WorkflowStep(
                step_id=step_id,
                step_type=step_type,
                agent_name=agent_name,
                status="pending",
                metadata={"description": description}
            )
            execution_manager.add_workflow_step(execution_id, step)
        
        print(f"✅ Added {len(steps)} workflow steps")
        
        # Simulate step execution with timing
        print("\\n📋 Simulating workflow execution...")
        execution_manager.update_execution(execution_id, status="running")
        
        for i, (step_id, step_type, agent_name, description) in enumerate(steps):
            progress = (i + 1) / len(steps)
            
            # Start step
            execution_manager.update_workflow_step(execution_id, step_id, status="running")
            execution_manager.update_execution(
                execution_id, 
                current_step=description, 
                progress=progress * 0.9  # Leave 10% for finalization
            )
            
            if agent_name:
                execution_manager.add_execution_path(execution_id, agent_name)
            
            # Simulate processing time
            time.sleep(0.1)
            
            # Complete step
            execution_manager.update_workflow_step(
                execution_id, 
                step_id, 
                status="completed",
                output_data={"result": f"{description} completed"}
            )
            execution_manager.advance_workflow_step(execution_id)
            
            print(f"  ✓ {description}")
        
        # Add branch decision simulation
        execution_manager.add_branch_decision(execution_id, "processing_strategy", "fast_path")
        
        # Finalize execution
        execution_manager.update_execution(
            execution_id, 
            status="completed", 
            progress=1.0,
            current_step="Completed",
            result={"status": "success", "message": "Mock workflow completed"}
        )
        
        self._display_execution_results(execution_id, "Mock Workflow")
        return execution_id
    
    def test_real_workflow_execution(self, workflow_id: str, query: str = "Test query"):
        """Test real workflow execution with tracing"""
        print(f"🔥 Testing Real Workflow Execution")
        print(f"Workflow ID: {workflow_id}")
        print(f"Query: {query}")
        print("=" * 60)
        
        if not self.db:
            print("❌ Database not available")
            return None
        
        # Get workflow details
        try:
            workflow = crud.get_workflow(self.db, uuid.UUID(workflow_id))
            if not workflow:
                print(f"❌ Workflow {workflow_id} not found")
                return None
            
            print(f"✅ Found workflow: {workflow.name}")
            agents = workflow.configuration.get("agents", [])
            print(f"✅ Agents in workflow: {len(agents)}")
            
            for i, agent in enumerate(agents):
                print(f"  {i+1}. {agent.get('agent_type', 'Unknown')} - {agent.get('agent_id', 'No ID')}")
        
        except Exception as e:
            print(f"❌ Error fetching workflow: {e}")
            return None
        
        # Create execution for real workflow
        execution_id = execution_manager.create_execution(
            execution_type="workflow",
            workflow_id=workflow_id,
            user_id="test_user",
            query=query,
            estimated_duration=30
        )
        
        print(f"✅ Created real execution: {execution_id}")
        
        # Initialize tracing
        estimated_steps = len(agents) + 2  # agents + init + finalize
        execution_manager.init_workflow_trace(execution_id, workflow_id, estimated_steps)
        
        print("⚠️  Real workflow execution would require full FastAPI server and background tasks")
        print("⚠️  This test demonstrates tracing setup for real workflows")
        print("⚠️  Use the API endpoints for full execution testing")
        
        # Show the API call that would execute this workflow
        print(f"\\n🔗 To execute this workflow via API:")
        print(f"POST /api/workflows/{workflow_id}/execute/async")
        print(f"Body: {{\"query\": \"{query}\", \"user_id\": \"test_user\"}}")
        print(f"Then poll: GET /api/executions/{execution_id}/progress")
        
        return execution_id
    
    def interactive_workflow_selection(self):
        """Interactive workflow selection for testing"""
        print("🎯 Interactive Workflow Testing")
        print("=" * 50)
        
        workflows = self.display_available_workflows()
        if not workflows:
            return None
        
        # Get user selection
        while True:
            try:
                choice = input(f"\\nSelect workflow (1-{len(workflows)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                choice_num = int(choice)
                if 1 <= choice_num <= len(workflows):
                    selected_workflow = workflows[choice_num - 1]
                    break
                else:
                    print(f"❌ Please select a number between 1 and {len(workflows)}")
            
            except ValueError:
                print("❌ Please enter a valid number or 'q'")
        
        # Get custom query
        custom_query = input("Enter custom query (or press Enter for default): ").strip()
        if not custom_query:
            custom_query = f"Test execution of {selected_workflow['name']}"
        
        print(f"\\n🎯 Selected: {selected_workflow['name']}")
        print(f"🎯 Query: {custom_query}")
        
        return self.test_real_workflow_execution(selected_workflow['id'], custom_query)
    
    def _display_execution_results(self, execution_id: str, workflow_name: str):
        """Display detailed execution results"""
        execution = execution_manager.get_execution(execution_id)
        if not execution:
            print("❌ Execution not found")
            return
        
        print(f"\\n📊 {workflow_name} Execution Results:")
        print("=" * 50)
        print(f"  Status: {execution.status}")
        print(f"  Progress: {(execution.progress or 0) * 100:.1f}%")
        print(f"  Current Step: {execution.current_step}")
        
        if execution.workflow_trace:
            trace = execution.workflow_trace
            print(f"\\n🔍 Workflow Trace Details:")
            print(f"  Execution Path: {' → '.join(trace.execution_path) if trace.execution_path else 'None'}")
            print(f"  Total Steps: {trace.total_steps}")
            print(f"  Current Step Index: {trace.current_step_index}")
            print(f"  Branch Decisions: {len(trace.branch_decisions)}")
            
            if trace.branch_decisions:
                print("\\n🌳 Branch Decisions:")
                for decision, outcome in trace.branch_decisions.items():
                    print(f"  • {decision}: {outcome.get('outcome', 'N/A')}")
            
            print(f"\\n📋 Step Details:")
            for i, step in enumerate(trace.steps):
                status_emoji = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌", "skipped": "⏭️"}
                emoji = status_emoji.get(step.status, '❓')
                agent_info = f" - {step.agent_name}" if step.agent_name else ""
                duration_info = f" ({step.duration_ms}ms)" if step.duration_ms else ""
                
                print(f"  {i+1:2}. {emoji} {step.step_type}{agent_info}{duration_info}")
                
                if step.error:
                    print(f"      ❌ Error: {step.error}")
    
    def run_comprehensive_tests(self):
        """Run all available tests"""
        print("🚀 Comprehensive Workflow Testing Suite")
        print("=" * 60)
        
        # Setup
        db_available = self.setup_db()
        
        try:
            # Test 1: Mock workflow tracing
            print("\\n" + "="*60)
            mock_execution_id = self.test_mock_workflow_tracing()
            
            if db_available:
                # Test 2: Real workflow integration
                print("\\n" + "="*60)
                workflows = self.get_available_workflows()
                
                if workflows:
                    # Test simple workflow (single agent)
                    simple_workflows = [w for w in workflows if w["agent_count"] == 1]
                    if simple_workflows:
                        print("\\n🧪 Testing Simple Single-Agent Workflow:")
                        self.test_real_workflow_execution(
                            simple_workflows[0]["id"], 
                            f"Test {simple_workflows[0]['name']}"
                        )
                    
                    # Test complex workflow (multi-agent)
                    complex_workflows = [w for w in workflows if w["agent_count"] > 1]
                    if complex_workflows:
                        print("\\n🧪 Testing Complex Multi-Agent Workflow:")
                        self.test_real_workflow_execution(
                            complex_workflows[0]["id"], 
                            f"Test {complex_workflows[0]['name']}"
                        )
                
                # Test 3: Interactive selection
                print("\\n" + "="*60)
                print("ℹ️  Interactive mode available - run with --interactive flag")
            
            else:
                print("\\n⚠️  Database not available - skipping real workflow tests")
            
            # Display summary
            print("\\n" + "="*60)
            print("📈 Test Summary:")
            stats = execution_manager.get_stats()
            for key, value in stats.items():
                if key not in ['oldest_execution', 'newest_execution']:
                    print(f"  {key}: {value}")
            
            print("\\n🎉 Comprehensive testing completed!")
            
        finally:
            self.cleanup_db()

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Async Testing Suite")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run interactive workflow selection")
    parser.add_argument("--mock-only", "-m", action="store_true", help="Run only mock tests")
    parser.add_argument("--workflow-id", "-w", help="Test specific workflow by ID")
    parser.add_argument("--query", "-q", default="Test query", help="Custom query for workflow execution")
    
    args = parser.parse_args()
    
    tester = WorkflowTester()
    
    try:
        if args.mock_only:
            tester.test_mock_workflow_tracing()
        
        elif args.workflow_id:
            if tester.setup_db():
                tester.test_real_workflow_execution(args.workflow_id, args.query)
            else:
                print("❌ Database required for real workflow testing")
        
        elif args.interactive:
            if tester.setup_db():
                tester.interactive_workflow_selection()
            else:
                print("❌ Database required for interactive mode")
        
        else:
            tester.run_comprehensive_tests()
    
    finally:
        tester.cleanup_db()

if __name__ == "__main__":
    main()