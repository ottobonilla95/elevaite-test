"""
RabbitMQ Worker - Consumes and executes workflows
"""

import asyncio
import json
import logging
import os

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from workflow_core_sdk.services.workflows_service import WorkflowsService
from workflow_core_sdk.db.database import get_session
from workflow_core_sdk import WorkflowEngine, StepRegistry
from workflow_core_sdk.execution.context_impl import ExecutionContext, UserContext
from db_core.middleware import set_current_tenant_id

logger = logging.getLogger(__name__)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://elevaite:elevaite@localhost:5672/")
QUEUE_NAME = "workflow.execute"
RESUME_QUEUE_NAME = "workflow.resume"
PREFETCH_COUNT = 1  # Process 1 job at a time


async def process_message(
    message: AbstractIncomingMessage,
    workflow_engine: WorkflowEngine,
):
    """Process a single workflow execution job."""
    async with message.process(requeue=True):  # Requeue on failure for retry
        tenant_id = None
        try:
            payload = json.loads(message.body.decode())
            execution_id = payload["execution_id"]
            workflow_id = payload["workflow_id"]
            trigger_data = payload.get("trigger_data", {})
            user_context_data = payload.get("user_context", {})

            logger.info(f"Processing workflow {workflow_id}, execution {execution_id}")

            # Set tenant context for ALL subsequent SDK operations
            # This ensures all internal sessions get the correct search_path
            tenant_id = user_context_data.get("tenant_id")
            if tenant_id:
                set_current_tenant_id(tenant_id)
                logger.info(f"Set tenant context to {tenant_id}")

            # Get workflow config from database using sync session
            # get_session() now automatically applies tenant schema from context
            session_gen = get_session()
            session = next(session_gen)
            try:
                workflow_config = WorkflowsService.get_workflow_config(
                    session, workflow_id
                )
                if not workflow_config:
                    logger.error(f"Workflow {workflow_id} not found")
                    raise ValueError(f"Workflow {workflow_id} not found")

                # Ensure workflow_id is in the config
                if "workflow_id" not in workflow_config:
                    workflow_config["workflow_id"] = workflow_id

                # Create user context
                user_context = UserContext(
                    user_id=user_context_data.get("user_id"),
                    session_id=user_context_data.get("session_id"),
                    organization_id=user_context_data.get("organization_id"),
                )

                # Create execution context
                execution_context = ExecutionContext(
                    workflow_config=workflow_config,
                    user_context=user_context,
                    workflow_engine=workflow_engine,
                    execution_id=execution_id,
                )

                # Seed trigger data
                execution_context.step_io_data["trigger_raw"] = trigger_data

                # Execute workflow
                await workflow_engine.execute_workflow(execution_context)

                logger.info(f"Completed execution {execution_id}")
            finally:
                # Clean up the session generator
                try:
                    session_gen.close()
                except StopIteration:
                    pass

        except Exception as e:
            logger.error(f"Failed to process message: {e}", exc_info=True)
            raise  # Will be requeued or sent to DLQ
        finally:
            # Clear tenant context after processing
            if tenant_id:
                set_current_tenant_id(None)
                logger.debug("Cleared tenant context")


async def process_resume_message(
    message: AbstractIncomingMessage,
    workflow_engine: WorkflowEngine,
):
    """Process a workflow resume job."""
    async with message.process(requeue=True):  # Requeue on failure for retry
        try:
            payload = json.loads(message.body.decode())
            execution_id = payload["execution_id"]
            step_id = payload["step_id"]
            decision_output = payload.get("decision_output", {})

            logger.info(
                f"Processing resume for execution {execution_id}, step {step_id}"
            )

            # Resume workflow execution
            await workflow_engine.resume_execution(
                execution_id=execution_id,
                step_id=step_id,
                decision_output=decision_output,
            )

            logger.info(f"Resumed execution {execution_id} at step {step_id}")

        except Exception as e:
            logger.error(f"Failed to process resume message: {e}", exc_info=True)
            raise  # Will be requeued or sent to DLQ


async def main():
    """Main worker loop."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info("Starting workflow worker...")

    # Initialize workflow engine
    logger.info("Initializing workflow engine...")
    step_registry = StepRegistry()
    await step_registry.register_builtin_steps()
    workflow_engine = WorkflowEngine(step_registry=step_registry)
    logger.info("✅ Workflow engine initialized")

    # Connect to RabbitMQ
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=PREFETCH_COUNT)

    # Declare execute queue with dead-letter exchange
    execute_queue = await channel.declare_queue(
        QUEUE_NAME,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": f"{QUEUE_NAME}.dlq",
        },
    )
    # Declare execute dead-letter queue
    await channel.declare_queue(f"{QUEUE_NAME}.dlq", durable=True)

    # Declare resume queue with dead-letter exchange
    resume_queue = await channel.declare_queue(
        RESUME_QUEUE_NAME,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": f"{RESUME_QUEUE_NAME}.dlq",
        },
    )
    # Declare resume dead-letter queue
    await channel.declare_queue(f"{RESUME_QUEUE_NAME}.dlq", durable=True)

    logger.info(
        f"✅ Connected to RabbitMQ, listening on queues: {QUEUE_NAME}, {RESUME_QUEUE_NAME}"
    )

    # Consume execute messages
    async def execute_handler(message: AbstractIncomingMessage):
        await process_message(message, workflow_engine)

    await execute_queue.consume(execute_handler)

    # Consume resume messages
    async def resume_handler(message: AbstractIncomingMessage):
        await process_resume_message(message, workflow_engine)

    await resume_queue.consume(resume_handler)

    # Keep running
    try:
        logger.info("🚀 Worker ready and waiting for jobs...")
        await asyncio.Future()  # Run forever
    except asyncio.CancelledError:
        logger.info("Worker shutting down...")
    finally:
        await connection.close()
        logger.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
