import os
from dotenv import load_dotenv
import pika
from ..db.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_rabbitmq_connection():
    load_dotenv()
    RABBITMQ_USER = os.getenv("RABBITMQ_USER")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
    RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST")
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=5672,
            heartbeat=600,
            blocked_connection_timeout=300,
            credentials=credentials,
            virtual_host=RABBITMQ_VHOST,
        )
    )
    channel = connection.channel()
    channel.queue_declare("s3_ingest")
    channel.queue_declare("preprocess")

    try:
        yield connection
    finally:
        connection.close()
