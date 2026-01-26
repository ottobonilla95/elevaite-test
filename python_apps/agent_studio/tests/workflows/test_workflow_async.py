#!/usr/bin/env python3
"""
Test script for async workflow execution with tracing.
This script demonstrates the new workflow tracing functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.execution_manager import execution_manager, WorkflowStep

def test_workflow_tracing():
    """Test workflow tracing functionality"""
    print("🧪 Testing Workflow Async Execution with Tracing")
    print("=" * 50)
    
    # Create a test execution
    execution_id = execution_manager.create_execution(
        execution_type="workflow",
        workflow_id="test-workflow-123",
        user_id="test_user",
        query="Test workflow execution with tracing"
    )
    
    print(f"✅ Created execution: {execution_id}")
    
    # Initialize workflow trace
    success = execution_manager.init_workflow_trace(execution_id, "test-workflow-123", 4)
    print(f"✅ Initialized workflow trace: {success}")
    
    # Add workflow steps
    steps = [
        WorkflowStep(
            step_id="init_step",
            step_type="data_processing",
            status="pending",
            metadata={"description": "Initialize workflow"}
        ),
        WorkflowStep(
            step_id="agent_step_1",
            step_type="agent_execution",
            agent_name="CommandAgent",
            status="pending",
            input_data={"query": "Test query"},
            metadata={"agent_type": "orchestrator"}
        ),
        WorkflowStep(
            step_id="agent_step_2",
            step_type="agent_execution",
            agent_name="DataAgent",
            status="pending",
            metadata={"orchestrated": True}
        ),
        WorkflowStep(
            step_id="final_step",
            step_type="data_processing",
            status="pending",
            metadata={"description": "Finalize results"}
        )
    ]
    
    for step in steps:
        execution_manager.add_workflow_step(execution_id, step)
    
    print(f"✅ Added {len(steps)} workflow steps")
    
    # Simulate step execution
    print("\n📋 Simulating workflow execution...")
    
    # Step 1: Initialize
    execution_manager.update_workflow_step(execution_id, "init_step", status="running")
    execution_manager.update_execution(execution_id, status="running", current_step="Initializing")
    execution_manager.update_workflow_step(execution_id, "init_step", status="completed")
    execution_manager.advance_workflow_step(execution_id)
    print("  ✓ Initialization completed")
    
    # Step 2: Agent 1 execution
    execution_manager.update_workflow_step(execution_id, "agent_step_1", status="running")
    execution_manager.update_execution(execution_id, current_step="Executing CommandAgent")
    execution_manager.add_execution_path(execution_id, "CommandAgent")
    execution_manager.update_workflow_step(
        execution_id, 
        "agent_step_1", 
        status="completed",
        output_data={"result": "Agent 1 completed successfully"}
    )
    execution_manager.advance_workflow_step(execution_id)
    print("  ✓ CommandAgent execution completed")
    
    # Step 3: Agent 2 execution
    execution_manager.update_workflow_step(execution_id, "agent_step_2", status="running")
    execution_manager.update_execution(execution_id, current_step="Executing DataAgent")
    execution_manager.add_execution_path(execution_id, "DataAgent")
    execution_manager.add_branch_decision(execution_id, "data_processing_choice", "use_fast_path")
    execution_manager.update_workflow_step(
        execution_id, 
        "agent_step_2", 
        status="completed",
        output_data={"result": "Data processing completed"}
    )
    execution_manager.advance_workflow_step(execution_id)
    print("  ✓ DataAgent execution completed")
    
    # Step 4: Finalize
    execution_manager.update_workflow_step(execution_id, "final_step", status="running")
    execution_manager.update_execution(execution_id, current_step="Finalizing")
    execution_manager.update_workflow_step(
        execution_id, 
        "final_step", 
        status="completed",
        output_data={"final_result": "Workflow completed successfully"}
    )
    execution_manager.advance_workflow_step(execution_id)
    execution_manager.update_execution(
        execution_id, 
        status="completed", 
        progress=1.0,
        result={"status": "success", "message": "Test workflow completed"}
    )
    print("  ✓ Workflow finalization completed")
    
    # Get final execution status
    final_execution = execution_manager.get_execution(execution_id)
    if final_execution:
        print("\n📊 Final Execution Status:")
        print(f"  Status: {final_execution.status}")
        print(f"  Progress: {(final_execution.progress or 0) * 100:.1f}%")
        print(f"  Current Step: {final_execution.current_step}")
        
        if final_execution.workflow_trace:
            trace = final_execution.workflow_trace
            print("\n🔍 Workflow Trace Details:")
            print(f"  Execution Path: {' → '.join(trace.execution_path)}")
            print(f"  Total Steps: {trace.total_steps}")
            print(f"  Current Step Index: {trace.current_step_index}")
            print(f"  Branch Decisions: {len(trace.branch_decisions)}")
            
            print("\n📋 Step Details:")
            for i, step in enumerate(trace.steps):
                status_emoji = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌", "skipped": "⏭️"}
                print(f"  {i+1}. {status_emoji.get(step.status, '❓')} {step.step_type} - {step.agent_name or 'System'}")
                if step.duration_ms:
                    print(f"     Duration: {step.duration_ms}ms")
                if step.error:
                    print(f"     Error: {step.error}")
    
    print("\n📈 Execution Manager Stats:")
    stats = execution_manager.get_stats()
    for key, value in stats.items():
        if key not in ['oldest_execution', 'newest_execution']:
            print(f"  {key}: {value}")
    
    print("\n🎉 Test completed successfully!")
    return True

if __name__ == "__main__":
    test_workflow_tracing()