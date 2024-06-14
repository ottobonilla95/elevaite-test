import os
from dotenv import load_dotenv
import redis
from .SingletonMeta import SingletonMeta


class RedisSingleton(metaclass=SingletonMeta):
    connection: redis.Redis

    def __init__(self, decode_responses=False) -> None:
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

        self.connection = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            username=REDIS_USERNAME,
            password=REDIS_PASSWORD,
        )
