from enum import Enum

import redis

from station.app.config import settings


class RedisJSONOps(str, Enum):
    SET = "JSON.SET"
    GET = "JSON.GET"
    DELETE = "JSON.DEL"


class Cache:

    def __init__(self):
        self.redis = redis.Redis(decode_responses=True, **settings.config.redis.dict())

    def set(self, key, value, ttl: int = 3600):
        self.redis.set(key, value, ex=ttl)

    def get(self, key) -> str:
        return self.redis.get(key)

    def json_set(self, key, value: str, ttl: int = 3600):
        pass

    def json_get(self, key) -> str:
        pass


redis_cache = Cache()
