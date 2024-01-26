import os
from dotenv import load_dotenv
import pika

from .SingletonMeta import SingletonMeta


class RabbitMQSingleton(metaclass=SingletonMeta):
    connection: pika.BlockingConnection = None
    channel = None

    def __init__(self) -> None:
        load_dotenv()
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv("RABBITMQ_HOST"),
                heartbeat=600,
                blocked_connection_timeout=300,
            )
        )
        self.channel = self.connection.channel()

    def some_business_logic(self):
        """
        Finally, any singleton should define some business logic, which can be
        executed on its instance.
        """
