import os
import redis
from .SingletonMeta import SingletonMeta


class RedisSingleton(metaclass=SingletonMeta):
    connection: redis.Redis = None

    def __init__(self, decode_responses=False) -> None:
        print(f'os.getenv("REDIS_HOST") = {os.getenv("REDIS_HOST")}')
        print(f'os.getenv("REDIS_PORT") = {os.getenv("REDIS_PORT")}')
        self.connection = redis.Redis(
            host=os.getenv("REDIS_HOST"),
            port=os.getenv("REDIS_PORT"),
            decode_responses=decode_responses,
            password=os.getenv("REDIS_PASSWORD"),
        )
