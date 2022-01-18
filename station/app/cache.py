from enum import Enum

import redis

from station.app.config import settings


class RedisJSONOps(str, Enum):
    SET = "JSON.SET"
    GET = "JSON.GET"
    DELETE = "JSON.DEL"


class Cache:

    def __init__(self):
        self.redis = redis.Redis(decode_responses=True, **settings.config.redis)

    def set(self, key, value, ttl: int = 3600):
        pass

    def get(self, key):
        pass
