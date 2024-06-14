import os
from typing import Type
from dotenv import load_dotenv
from ..orm.db.database import SessionLocal
from pydantic import BaseModel
import redis


def _get_redis() -> redis.Redis:
    load_dotenv()
    REDIS_HOST = os.getenv("REDIS_HOST")
    if REDIS_HOST is None:
        raise Exception("REDIS_HOST is null")
    _REDIS_PORT = os.getenv("REDIS_PORT")
    if _REDIS_PORT is None:
        raise Exception("REDIS_PORT is null")
    try:
        REDIS_PORT = int(_REDIS_PORT)
    except ValueError:
        print("REDIS_PORT must be an integer")
    REDIS_USERNAME = os.getenv("REDIS_USERNAME")
    if REDIS_USERNAME is None:
        raise Exception("REDIS_USERNAME is null")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    if REDIS_PASSWORD is None:
        raise Exception("REDIS_PASSWORD is null")

    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
    )
    try:
        r.ping()
    except Exception as e:
        print("Could not connect to Redis")
    return r


def with_redis(func):
    def inner(*args, **kwargs):
        r = _get_redis()
        res = func(r=r, *args, **kwargs)
        r.close()
        return res

    return inner


def with_db(func):
    def inner(*args, **kwargs):
        db = SessionLocal()
        res = func(db=db, *args, **kwargs)
        db.close()
        return res

    return inner


def payload_schema(schema: Type[BaseModel]):
    def wrap(f):
        def inner(*args, **kwargs):
            input = schema()
