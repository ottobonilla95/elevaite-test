#!/usr/bin/env python3
"""
DBOS Adapter Demo Script

This script demonstrates Phase 0 of the DBOS integration:
- Trigger → Agent → Tool → Subflow execution using DBOS durable workflows
- Shows how our existing step registry works with DBOS
- Demonstrates automatic recovery and durability
- No API changes required - runs locally

Usage:
    python scripts/dbos_demo.py
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from workflow_core_sdk.dbos_impl.runtime import get_dbos_adapter, DBOS_AVAILABLE
from workflow_engine_poc.step_registry import StepRegistry

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def create_demo_workflow_config() -> dict:
    """Create a demo workflow configuration that demonstrates the full flow"""
    return {
        "workflow_id": "dbos-demo-workflow",
        "name": "DBOS Demo: Trigger → Agent → Tool → Subflow",
        "description": "Demonstrates DBOS durable execution with our step registry",
        "execution_pattern": "sequential",
        "steps": [
            {"step_id": "trigger", "step_type": "trigger", "name": "Chat Trigger", "config": {"trigger_type": "chat"}},
            {
                "step_id": "agent_step",
                "step_type": "agent_execution",
                "name": "AI Agent Processing",
                "config": {
                    "agent_name": "DemoAgent",
                    "system_prompt": "You are a helpful assistant that can use tools to help users. When you need to perform calculations, use the add_numbers tool.",
                    "query": "Please help me with this request: {current_message}",
                    "force_real_llm": False,  # Use mock for demo
                },
            },
            {
                "step_id": "tool_step",
                "step_type": "tool_execution",
                "name": "Tool Execution",
                "config": {
                    "tool_name": "add_numbers",
                    "param_mapping": {
                        "a": "step_agent_step.result.extracted_numbers.0",
                        "b": "step_agent_step.result.extracted_numbers.1",
                    },
                    "static_params": {
                        "a": 10,  # fallback values
                        "b": 5,
                    },
                },
            },
            {
                "step_id": "subflow_step",
                "step_type": "subflow",
                "name": "Subflow Processing",
                "config": {
                    "workflow_id": "demo-subflow",
                    "input_mapping": {"calculation_result": "step_tool_step.result", "original_message": "current_message"},
                },
            },
        ],
    }


def create_demo_trigger_data() -> dict:
    """Create demo trigger data simulating a chat message"""
    return {
        "kind": "chat",
        "current_message": "Can you add 15 and 25 for me?",
        "messages": [{"role": "user", "content": "Can you add 15 and 25 for me?"}],
        "attachments": [],
        "timestamp": "2025-01-08T10:00:00Z",
    }


def create_demo_user_context() -> dict:
    """Create demo user context"""
    return {"user_id": "demo-user-123", "session_id": "demo-session-456"}


async def demonstrate_basic_execution():
    """Demonstrate basic DBOS workflow execution"""
    logger.info("=== DBOS Demo: Basic Workflow Execution ===")

    # Get the DBOS adapter
    adapter = await get_dbos_adapter()

    # Create demo workflow configuration
    workflow_config = create_demo_workflow_config()
    trigger_data = create_demo_trigger_data()
    user_context = create_demo_user_context()

    logger.info(f"Workflow: {workflow_config['name']}")
    logger.info(f"Steps: {len(workflow_config['steps'])}")
    logger.info(f"Trigger: {trigger_data['current_message']}")

    try:
        # Execute the workflow
        result = await adapter.start_workflow(
            workflow_config=workflow_config, trigger_data=trigger_data, user_context=user_context
        )

        logger.info("=== Workflow Execution Result ===")
        logger.info(f"Success: {result.get('success')}")
        logger.info(f"Execution ID: {result.get('execution_id')}")

        if result.get("success"):
            step_results = result.get("step_results", {})
            logger.info(f"Completed {len(step_results)} steps:")

            for step_id, step_result in step_results.items():
                logger.info(f"  - {step_id}: {'✓' if step_result.get('success') else '✗'}")
                if step_result.get("output_data"):
                    logger.info(f"    Output: {step_result['output_data']}")
        else:
            logger.error(f"Workflow failed: {result.get('error')}")
            if result.get("failed_step"):
                logger.error(f"Failed at step: {result.get('failed_step')}")

    except Exception as e:
        logger.error(f"Exception during workflow execution: {e}")
        raise


async def demonstrate_failure_recovery():
    """Demonstrate DBOS failure recovery (simulated)"""
    logger.info("=== DBOS Demo: Failure Recovery Simulation ===")

    # This would demonstrate how DBOS recovers from failures
    # For now, we'll just show the concept
    logger.info("In a real DBOS environment:")
    logger.info("1. If the process crashes during step execution")
    logger.info("2. DBOS would automatically restart the workflow")
    logger.info("3. It would resume from the last completed step")
    logger.info("4. No duplicate work would be performed")
    logger.info("5. The workflow would complete successfully")


async def demonstrate_step_registry_integration():
    """Demonstrate how DBOS integrates with our existing step registry"""
    logger.info("=== DBOS Demo: Step Registry Integration ===")

    adapter = await get_dbos_adapter()
    step_registry = adapter.step_registry

    # Show registered steps
    logger.info("Registered step types:")
    for step_type in step_registry.registered_steps.keys():
        step_info = step_registry.registered_steps[step_type]
        logger.info(f"  - {step_type}: {step_info['name']} ({step_info['execution_type']})")

    logger.info("\nDBOS Integration Benefits:")
    logger.info("✓ Each step becomes durable automatically")
    logger.info("✓ Failed steps are retried automatically")
    logger.info("✓ Completed steps are never re-executed")
    logger.info("✓ Workflow state is persisted in PostgreSQL")
    logger.info("✓ No changes needed to existing step implementations")


async def main():
    """Main demo function"""
    logger.info("Starting DBOS Workflow Engine Demo")
    logger.info(f"DBOS Available: {DBOS_AVAILABLE}")

    if not DBOS_AVAILABLE:
        logger.warning("DBOS library not installed - running in mock mode")
        logger.warning("To install DBOS: pip install dbos")

    try:
        # Run demonstrations
        await demonstrate_step_registry_integration()
        print("\n" + "=" * 60 + "\n")

        await demonstrate_basic_execution()
        print("\n" + "=" * 60 + "\n")

        await demonstrate_failure_recovery()

        logger.info("Demo completed successfully!")

    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
