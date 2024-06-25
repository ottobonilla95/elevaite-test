import os
from dotenv import load_dotenv
import pika
from elevaitelib.orm.db.database import SessionLocal
from qdrant_client import AsyncQdrantClient
from flytekit.configuration import Config
from flytekit.remote import FlyteRemote
from elevaitelib.schemas import (
    api as api_schemas,
)

from rbac_api import route_validator_map, RBACValidatorProvider


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_rabbitmq_connection():
    load_dotenv()
    RABBITMQ_USER = os.getenv("RABBITMQ_USER")
    # if RABBITMQ_USER is None:
    #     raise Exception("RABBITMQ_USER is null")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
    # if RABBITMQ_PASSWORD is None:
    #     raise Exception("RABBITMQ_PASSWORD is null")
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
    if RABBITMQ_HOST is None:
        raise Exception("RABBITMQ_HOST is null")
    RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST")
    # if RABBITMQ_VHOST is None:
    #     raise Exception("RABBITMQ_VHOST is null")
    # credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=5672,
            heartbeat=600,
            blocked_connection_timeout=300,
            # credentials=credentials,
            # virtual_host=RABBITMQ_VHOST,
        )
    )
    channel = connection.channel()
    channel.queue_declare("s3_ingest")
    channel.queue_declare("preprocess")

    try:
        yield connection
    finally:
        connection.close()


def get_qdrant_connection():
    load_dotenv()
    QDRANT_URL = os.getenv("QDRANT_URL")
    if QDRANT_URL is None:
        raise Exception("QDRANT_URL is null")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    if QDRANT_API_KEY is None:
        return AsyncQdrantClient(url=QDRANT_URL)
    return AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def get_flyte_remote() -> FlyteRemote:
    load_dotenv()
    DEFAULT_DOMAIN = os.getenv("FLYTE_DOMAIN")
    DEFAULT_PROJECT = os.getenv("FLYTE_PROJECT")
    return FlyteRemote(
        config=Config.auto(),
        default_project=DEFAULT_PROJECT if DEFAULT_PROJECT is not None else "elevaite",
        default_domain=DEFAULT_DOMAIN if DEFAULT_DOMAIN is not None else "development",
    )


def get_validation_info(namespace: api_schemas.APINamespace, target: str):
    return route_validator_map[(namespace, target)]  # type: ignore
