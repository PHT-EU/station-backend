from enum import Enum
from typing import Optional
from pydantic import SecretStr

import redis

from station.app.config import settings


class RedisJSONOps(str, Enum):
    SET = "JSON.SET"
    GET = "JSON.GET"


class Cache:

    def __init__(self, host=None, port=6379, password=None, db=None):
        if host:
            self.redis = redis.Redis(decode_responses=True, host=host, port=port, password=password, db=db)
        else:
            self.redis = redis.Redis(decode_responses=True, **settings.config.redis.dict())
    def set(self, key: str, value: str, ttl: int = 3600) -> None:
        """
        Set a key/value pair in the cache. With ttl.
        Args:
            key: key to set
            value: value of the key
            ttl: time until the key expires

        Returns:

        """
        self.redis.set(key, value, ex=ttl)

    def get(self, key: str) -> str:
        """
        Get a key from the cache.
        Args:
            key: cache key

        Returns:
            value of the key or None if not found
        """
        return self.redis.get(key)

    def json_set(self, key: str, value: str, ttl: int = 3600) -> None:
        """
        Adds a json string to the cache. With ttl.
        Args:
            key: key under which the json string is stored
            value: json string
            ttl: time until the key expires

        Returns:

        """
        self.redis.execute_command(
            RedisJSONOps.SET.value,
            key,
            ".",
            value,
        )
        self.redis.expire(key, ttl)

    def json_get(self, key) -> str:
        """
        Get a json string from the cache.
        Args:
            key: key under which the json string is stored

        Returns:
            json string or None if not found
        """
        json_string = self.redis.execute_command(
            RedisJSONOps.GET.value,
            key,
            "."
        )
        return json_string


redis_cache = Cache(settings.config.redis.host)
