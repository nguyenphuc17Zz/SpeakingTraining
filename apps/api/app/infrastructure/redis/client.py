
import time

import redis.asyncio as aioredis
from app.core.config import get_settings
from app.core.logging import logger


class RedisManager:
    """Manages Redis async client connections and health checks."""

    def __init__(self, url: str | None = None):
        self._url = url or get_settings().REDIS_URL
        self._client: aioredis.Redis | None = None
        self._last_ping_time: float = 0.0
        self._is_alive_cached: bool = False
        self._cache_ttl_seconds: float = 10.0

    async def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2.0,
            )
        return self._client

    @property
    def client(self) -> aioredis.Redis:
        """Synchronous property to access the Redis client."""
        if self._client is None:
            self._client = aioredis.from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2.0,
            )
        return self._client

    async def ping(self, force: bool = False) -> bool:
        """Tests Redis connectivity with TTL caching to avoid blocking workers when offline."""
        now = time.monotonic()
        if not force and (now - self._last_ping_time) < self._cache_ttl_seconds:
            return self._is_alive_cached

        try:
            client = await self.get_client()
            response = await client.ping()
            self._is_alive_cached = bool(response)
        except Exception as e:
            logger.debug(f"Redis ping failed (Redis might not be running in local mode): {e}")
            self._is_alive_cached = False

        self._last_ping_time = now
        return self._is_alive_cached

    async def is_available(self) -> bool:
        return await self.ping()

    async def get_value(self, key: str) -> str | None:
        """Safely gets value from Redis with silent fallback to None if Redis is unreachable."""
        try:
            client = await self.get_client()
            return await client.get(key)
        except Exception as e:
            logger.debug(f"[RedisManager] Get failed for key '{key}': {e}")
            return None

    async def set_value(self, key: str, value: str, ex_seconds: int = 3600) -> bool:
        """Safely sets value in Redis with silent fallback if Redis is unreachable."""
        try:
            client = await self.get_client()
            await client.set(key, value, ex=ex_seconds)
            return True
        except Exception as e:
            logger.debug(f"[RedisManager] Set failed for key '{key}': {e}")
            return False

    async def close(self) -> None:
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None


redis_manager = RedisManager()


def get_redis_manager() -> RedisManager:
    return redis_manager
