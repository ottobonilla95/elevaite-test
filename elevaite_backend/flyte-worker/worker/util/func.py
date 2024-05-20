import ntpath
import os
from dotenv import load_dotenv
from flytekit.configuration import Config
from flytekit.remote import FlyteRemote
from .interfaces import Secrets


def path_leaf(path: str) -> str:
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def get_secrets() -> Secrets:
    load_dotenv()
    LAKEFS_ACCESS_KEY_ID = os.getenv("LAKEFS_ACCESS_KEY_ID")
    if LAKEFS_ACCESS_KEY_ID is None:
        raise Exception("LAKEFS_ACCESS_KEY_ID is null")
    LAKEFS_SECRET_ACCESS_KEY = os.getenv("LAKEFS_SECRET_ACCESS_KEY")
    if LAKEFS_SECRET_ACCESS_KEY is None:
        raise Exception("LAKEFS_SECRET_ACCESS_KEY is null")
    LAKEFS_ENDPOINT_URL = os.getenv("LAKEFS_ENDPOINT_URL")
    if LAKEFS_ENDPOINT_URL is None:
        raise Exception("LAKEFS_ENDPOINT_URL is null")
    LAKEFS_STORAGE_NAMESPACE = os.getenv("LAKEFS_STORAGE_NAMESPACE")
    if LAKEFS_STORAGE_NAMESPACE is None:
        raise Exception("LAKEFS_STORAGE_NAMESPACE is null")
    S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
    if S3_ACCESS_KEY_ID is None:
        raise Exception("S3_ACCESS_KEY_ID is null")
    S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
    if S3_SECRET_ACCESS_KEY is None:
        raise Exception("S3_SECRET_ACCESS_KEY is null")
    ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
    if ELASTIC_PASSWORD is None:
        raise Exception("ELASTIC_PASSWORD is null")
    ELASTIC_SSL_FINGERPRINT = os.getenv("ELASTIC_SSL_FINGERPRINT")
    if ELASTIC_SSL_FINGERPRINT is None:
        raise Exception("ELASTIC_SSL_FINGERPRINT is null")
    ELASTIC_HOST = os.getenv("ELASTIC_HOST")
    if ELASTIC_HOST is None:
        raise Exception("ELASTIC_HOST is null")

    secrets = Secrets(
        ELASTIC_HOST=ELASTIC_HOST,
        ELASTIC_PASSWORD=ELASTIC_PASSWORD,
        ELASTIC_SSL_FINGERPRINT=ELASTIC_SSL_FINGERPRINT,
        LAKEFS_ACCESS_KEY_ID=LAKEFS_ACCESS_KEY_ID,
        LAKEFS_ENDPOINT_URL=LAKEFS_ENDPOINT_URL,
        LAKEFS_SECRET_ACCESS_KEY=LAKEFS_SECRET_ACCESS_KEY,
        LAKEFS_STORAGE_NAMESPACE=LAKEFS_STORAGE_NAMESPACE,
        S3_ACCESS_KEY_ID=S3_ACCESS_KEY_ID,
        S3_SECRET_ACCESS_KEY=S3_SECRET_ACCESS_KEY,
    )
    return secrets


def get_flyte_remote() -> FlyteRemote:
    return FlyteRemote(
        config=Config.for_sandbox(),
        default_project="elevaite",
        default_domain="development",
    )
