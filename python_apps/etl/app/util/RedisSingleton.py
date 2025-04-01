import os
from dotenv import load_dotenv
import redis
from .SingletonMeta import SingletonMeta


class RedisSingleton(metaclass=SingletonMeta):
    connection: redis.Redis = None  # type: ignore

    def __init__(self) -> None:
        load_dotenv()
        REDIS_HOST = os.getenv("REDIS_HOST")
        if REDIS_HOST is None:
            raise Exception("Missing REDIS_HOST from the environment")
        REDIS_PORT = os.getenv("REDIS_PORT")
        if REDIS_PORT is None:
            raise Exception("Missing REDIS_PORT from the environment")
        try:
            REDIS_PORT = int(REDIS_PORT)
        except ValueError:
            raise Exception("REDIS_PORT must be a number")
        # REDIS_USERNAME = os.getenv("REDIS_USERNAME")
        # if REDIS_USERNAME is None:
        #     raise Exception("Missing REDIS_USERNAME from the environment")
        # REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
        # if REDIS_PASSWORD is None:
        #     raise Exception("Missing REDIS_PASSWORD from the environment")
        self.connection = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            # username=REDIS_USERNAME,
            # password=REDIS_PASSWORD,
        )
