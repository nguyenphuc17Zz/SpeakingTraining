import asyncio
import json
from typing import Any

from app.core.logging import logger
from app.infrastructure.redis.client import redis_manager


class LearningJobQueue:
    """Queue for asynchronous learning engine tasks (Redis with in-memory asyncio fallback)."""

    QUEUE_KEY = "queue:learning_jobs"

    def __init__(self):
        self._memory_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def enqueue(self, job_data: dict[str, Any]) -> None:
        """Enqueues a learning job payload."""
        is_redis_alive = await redis_manager.ping()
        if is_redis_alive:
            try:
                client = await redis_manager.get_client()
                await client.rpush(self.QUEUE_KEY, json.dumps(job_data))
                logger.debug(f"[LearningJobQueue] Enqueued job {job_data.get('task_type')} to Redis.")
                return
            except Exception as e:
                logger.warning(f"[LearningJobQueue] Redis enqueue error: {e}. Falling back to in-memory queue.")

        await self._memory_queue.put(job_data)
        logger.debug(f"[LearningJobQueue] Enqueued job {job_data.get('task_type')} to in-memory queue.")

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
                logger.debug(f"[LearningJobQueue] Redis dequeue error: {e}")

        try:
            return await asyncio.wait_for(self._memory_queue.get(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return None


learning_job_queue = LearningJobQueue()
