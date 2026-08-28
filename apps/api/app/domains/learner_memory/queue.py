import asyncio
import json
from typing import Any

from app.core.logging import logger
from app.infrastructure.redis.client import redis_manager


class LearnerMemoryJobQueue:
    """Queue for asynchronous learner memory updates (Redis with asyncio fallback)."""

    QUEUE_KEY = "queue:learner_memory_jobs"

    def __init__(self):
        self._memory_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def enqueue(self, job_data: dict[str, Any]) -> None:
        """Enqueues a learner memory job payload."""
        is_redis_alive = await redis_manager.ping()
        if is_redis_alive:
            try:
                client = await redis_manager.get_client()
                await client.rpush(self.QUEUE_KEY, json.dumps(job_data))
                logger.debug(f"[LearnerMemoryJobQueue] Enqueued job {job_data.get('session_id')} to Redis.")
                return
            except Exception as e:
                logger.warning(f"[LearnerMemoryJobQueue] Redis enqueue error: {e}. Falling back to memory.")

        await self._memory_queue.put(job_data)
        logger.debug(f"[LearnerMemoryJobQueue] Enqueued job {job_data.get('session_id')} to in-memory queue.")

    async def dequeue(self, timeout_seconds: float = 2.0) -> dict[str, Any] | None:
        """Dequeues next available job."""
        is_redis_alive = await redis_manager.ping()
        if is_redis_alive:
            try:
                client = await redis_manager.get_client()
                res = await client.blpop(self.QUEUE_KEY, timeout=int(timeout_seconds))
                if res:
                    _, val = res
                    return json.loads(val)
            except Exception as e:
                logger.debug(f"[LearnerMemoryJobQueue] Redis dequeue error: {e}")

        try:
            return await asyncio.wait_for(self._memory_queue.get(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return None


learner_memory_job_queue = LearnerMemoryJobQueue()
