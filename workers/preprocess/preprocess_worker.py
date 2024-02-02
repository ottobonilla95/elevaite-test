import json
import os
import sys
import threading
import lakefs

from dotenv import load_dotenv
import pika


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

    channel.queue_declare(queue="preprocess")

    def callback(ch, method, properties, body):
        _data = json.loads(body)

        print(f" [x] Received {_data}")

        # _formData = S3IngestData(
        #     **_data["dto"], datasetID=_data["id"], applicationID=_data["application_id"]
        # )
        t = threading.Thread(target=preprocess, args=(_formData,))
        # s3_lakefs_cp_stream(formData=_formData)
        t.start()

    channel.basic_consume(
        queue="s3_ingest", on_message_callback=callback, auto_ack=True
    )

    print("Awaiting Messages")

    channel.start_consuming()


def preprocess():
    LAKEFS_ACCESS_KEY_ID = os.getenv("LAKEFS_ACCESS_KEY_ID")
    LAKEFS_SECRET_ACCESS_KEY = os.getenv("LAKEFS_SECRET_ACCESS_KEY")
    LAKEFS_ENDPOINT_URL = os.getenv("LAKEFS_ENDPOINT_URL")
    LAKEFS_STORAGE_NAMESPACE = os.getenv("LAKEFS_STORAGE_NAMESPACE")
    S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_USERNAME = os.getenv("REDIS_USERNAME")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
    ELASTIC_SSL_FINGERPRINT = os.getenv("ELASTIC_SSL_FINGERPRINT")
    ELASTIC_HOST = os.getenv("ELASTIC_HOST")

    clt = lakefs.Client(
        host=LAKEFS_ENDPOINT_URL,
        username=LAKEFS_ACCESS_KEY_ID,
        password=LAKEFS_SECRET_ACCESS_KEY,
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
