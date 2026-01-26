"""
RabbitMQ Queue Service - Publishes workflow jobs
"""

import json
import logging
from typing import Optional, Dict, Any

import aio_pika
from aio_pika import Message, DeliveryMode

logger = logging.getLogger(__name__)

QUEUE_NAME = "workflow.execute"
RESUME_QUEUE_NAME = "workflow.resume"


class QueueService:
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self._connection = None
        self._channel = None

    async def connect(self):
        """Establish connection to RabbitMQ."""
        if not self._connection:
            self._connection = await aio_pika.connect_robust(self.rabbitmq_url)
            self._channel = await self._connection.channel()

            # Declare execute queue with dead-letter exchange
            await self._channel.declare_queue(
                QUEUE_NAME,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": f"{QUEUE_NAME}.dlq",
                },
            )
            # Declare execute dead-letter queue
            await self._channel.declare_queue(f"{QUEUE_NAME}.dlq", durable=True)

            # Declare resume queue with dead-letter exchange
            await self._channel.declare_queue(
                RESUME_QUEUE_NAME,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "",
                    "x-dead-letter-routing-key": f"{RESUME_QUEUE_NAME}.dlq",
                },
            )
            # Declare resume dead-letter queue
            await self._channel.declare_queue(f"{RESUME_QUEUE_NAME}.dlq", durable=True)

    async def close(self):
        """Close connection."""
        if self._connection:
            await self._connection.close()
            self._connection = None
            self._channel = None

    async def publish_workflow_execution(
        self,
        execution_id: str,
        workflow_id: str,
        trigger_data: Dict[str, Any],
        user_context: Optional[Dict[str, Any]] = None,
    ):
        """Publish a workflow execution job to the queue."""
        await self.connect()

        message_body = json.dumps(
            {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "trigger_data": trigger_data,
                "user_context": user_context,
            }
        )

        message = Message(
            body=message_body.encode(),
            delivery_mode=DeliveryMode.PERSISTENT,  # Survive broker restart
        )

        await self._channel.default_exchange.publish(
            message,
            routing_key=QUEUE_NAME,
        )

        logger.info(f"Queued workflow {workflow_id}, execution {execution_id}")

    async def publish_workflow_resume(
        self,
        execution_id: str,
        step_id: str,
        decision_output: Dict[str, Any],
    ):
        """Publish a workflow resume job to the queue."""
        await self.connect()

        message_body = json.dumps(
            {
                "execution_id": execution_id,
                "step_id": step_id,
                "decision_output": decision_output,
            }
        )

        message = Message(
            body=message_body.encode(),
            delivery_mode=DeliveryMode.PERSISTENT,  # Survive broker restart
        )

        await self._channel.default_exchange.publish(
            message,
            routing_key=RESUME_QUEUE_NAME,
        )

        logger.info(
            f"Queued workflow resume for execution {execution_id}, step {step_id}"
        )


# Singleton instance
_queue_service: Optional[QueueService] = None


async def get_queue_service() -> QueueService:
    global _queue_service
    if _queue_service is None:
        import os

        rabbitmq_url = os.getenv(
            "RABBITMQ_URL", "amqp://elevaite:elevaite@localhost:5672/"
        )
        _queue_service = QueueService(rabbitmq_url)
    return _queue_service
