import os
import sys
from dotenv import load_dotenv
from elevaitelib.rpc.connection import get_rmq_connection
import pika

from app.preprocess.preprocess_worker import preprocess_callback

from app.ingest.s3_ingest_worker import s3_ingest_callback


def main():
    connection = get_rmq_connection()
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
