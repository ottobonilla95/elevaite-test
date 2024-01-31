import os
from dotenv import load_dotenv
import pika

from .SingletonMeta import SingletonMeta


class RabbitMQSingleton(metaclass=SingletonMeta):
    connection: pika.BlockingConnection = None
    channel = None

    def __init__(self) -> None:
        load_dotenv()
        RABBITMQ_USER = os.getenv("RABBITMQ_USER")
        RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
        RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
        credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=5672,
                heartbeat=600,
                blocked_connection_timeout=300,
                credentials=credentials,
                virtual_host="elevaite_dev",
            )
        )
        self.channel = self.connection.channel()

    def some_business_logic(self):
        """
        Finally, any singleton should define some business logic, which can be
        executed on its instance.
        """
