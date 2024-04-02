import os
from dotenv import load_dotenv
import redis
from .SingletonMeta import SingletonMeta


class RedisSingleton(metaclass=SingletonMeta):
    connection: redis.Redis = None

    def __init__(self) -> None:
        load_dotenv()
        REDIS_HOST = os.getenv("REDIS_HOST")
        REDIS_PORT = os.getenv("REDIS_PORT")
        REDIS_USERNAME = os.getenv("REDIS_USERNAME")
        REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
        self.connection = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            username=REDIS_USERNAME,
            password=REDIS_PASSWORD,
        )
