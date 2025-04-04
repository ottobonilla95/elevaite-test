import redis
import os
from dotenv import load_dotenv
import time
load_dotenv()

class CacheControl:
    def __init__(self):
        self.cache = redis.StrictRedis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"))

    def get(self, key):
        return self.cache.get(key)

    def set(self, key, value):
        return self.cache.set(key, value)

    def hset(self, key, field, value):
        return self.cache.hset(key, field, value)

    def hget(self, key, field):
        return self.cache.hget(key, field)

    def delete(self, key):
        return self.cache.delete(key)

    def expire(self, key, exp_time):
        return self.cache.expire(key, exp_time)
    
    def setex(self, key, expiration, value):
        return self.cache.setex(key, expiration, value)
