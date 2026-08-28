import asyncio
import json
from typing import Any

from app.core.logging import logger
from app.infrastructure.redis.client import redis_manager

QUEUE_KEY = "queue:pronunciation_jobs"


class PronunciationJobQueue:
    """Queue for asynchronous background pronunciation analysis jobs (Redis with asyncio queue fallback)."""

    def __init__(self):
        self._memory_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def enqueue(self, job_data: dict[str, Any]) -> None:
        """Enqueues a pronunciation analysis job payload."""
        is_redis_alive = await redis_manager.ping()
        if is_redis_alive:
            try:
                client = await redis_manager.get_client()
                await client.lpush(QUEUE_KEY, json.dumps(job_data))
                logger.debug(f"[PronunciationJobQueue] Enqueued job {job_data.get('attempt_id')} to Redis.")
                return
            except Exception as e:
                logger.warning(f"[PronunciationJobQueue] Redis enqueue error: {e}. Falling back to memory queue.")

        await self._memory_queue.put(job_data)
        logger.debug(f"[PronunciationJobQueue] Enqueued job {job_data.get('attempt_id')} to memory queue.")

    async def dequeue(self, timeout_seconds: float = 1.0) -> dict[str, Any] | None:
        """Dequeues next available pronunciation analysis job."""
        is_redis_alive = await redis_manager.ping()
        if is_redis_alive:
            try:
                client = await redis_manager.get_client()
                raw = await client.rpop(QUEUE_KEY)
                if raw:
                    return json.loads(raw)
            except Exception as e:
                logger.debug(f"[PronunciationJobQueue] Redis dequeue error: {e}")

        try:
            return await asyncio.wait_for(self._memory_queue.get(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return None


pronunciation_job_queue = PronunciationJobQueue()
