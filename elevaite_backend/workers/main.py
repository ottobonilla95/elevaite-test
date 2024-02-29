import os
import sys
from dotenv import load_dotenv
import pika

from preprocess.preprocess_worker import preprocess_callback

from ingest.s3_ingest_worker import s3_ingest_callback


def main():
    load_dotenv()
    RABBITMQ_USER = os.getenv("RABBITMQ_USER")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=5672,
            heartbeat=600,
            blocked_connection_timeout=300,
            # credentials=credentials,
            # virtual_host="elevaite_dev",
        )
    )
    channel = connection.channel()
    channel.queue_declare(queue="s3_ingest")
    channel.queue_declare(queue="preprocess")

    channel.basic_consume(
        queue="s3_ingest", on_message_callback=s3_ingest_callback, auto_ack=True
    )
    channel.basic_consume(
        queue="preprocess", on_message_callback=preprocess_callback, auto_ack=True
    )
    print("Awaiting Messages")

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
