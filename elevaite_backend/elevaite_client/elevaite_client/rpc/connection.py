import os
from dotenv import load_dotenv
import pika


def get_rmq_connection() -> pika.BlockingConnection:
    load_dotenv()
    RABBITMQ_USER = os.getenv("RABBITMQ_USER")
    if RABBITMQ_USER is None:
        raise Exception("RABBITMQ_USER is null")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
    if RABBITMQ_PASSWORD is None:
        raise Exception("RABBITMQ_PASSWORD is null")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
    if RABBITMQ_HOST is None:
        raise Exception("RABBITMQ_HOST is null")
    RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST")
    if RABBITMQ_VHOST is None:
        raise Exception("RABBITMQ_VHOST is null")
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    try:
        conn = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=5672,
                heartbeat=600,
                blocked_connection_timeout=300,
                # credentials=credentials,
                # virtual_host=RABBITMQ_VHOST,
            )
        )
        return conn
    except Exception as e:
        print(e)
        raise e
