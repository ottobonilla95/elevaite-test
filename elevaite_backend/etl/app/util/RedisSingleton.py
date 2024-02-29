import os
import redis
from .SingletonMeta import SingletonMeta


class RedisSingleton(metaclass=SingletonMeta):
    connection: redis.Redis = None

    def __init__(self) -> None:
        self.connection = redis.Redis(
            host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT")
        )
