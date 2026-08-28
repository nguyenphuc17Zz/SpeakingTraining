import asyncio
import json
from typing import Any

from app.core.logging import logger
from app.infrastructure.redis.client import redis_manager

QUEUE_KEY = "queue:conversation_analysis"


class AnalysisJobQueue:
    """Hybrid job queue using Redis LPUSH/RPOP with in-memory asyncio fallback."""

    def __init__(self):
        self._memory_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def enqueue(self, job_data: dict[str, Any]) -> None:
        """Enqueues job to Redis or in-memory queue."""
        is_redis_alive = await redis_manager.ping()
        if is_redis_alive:
            try:
                client = await redis_manager.get_client()
                await client.lpush(QUEUE_KEY, json.dumps(job_data))
                logger.debug(f"[JobQueue] Enqueued job '{job_data.get('job_id')}' to Redis queue.")
                return
            except Exception as e:
                logger.warning(f"[JobQueue] Redis enqueue failed, falling back to memory queue: {e}")

        await self._memory_queue.put(job_data)
        logger.debug(f"[JobQueue] Enqueued job '{job_data.get('job_id')}' to in-memory queue.")

    async def dequeue(self, timeout_seconds: float = 1.0) -> dict[str, Any] | None:
        """Dequeues next available job."""
        is_redis_alive = await redis_manager.ping()
        if is_redis_alive:
            try:
                client = await redis_manager.get_client()
                raw = await client.rpop(QUEUE_KEY)
                if raw:
                    return json.loads(raw)
            except Exception as e:
                logger.debug(f"[JobQueue] Redis dequeue error: {e}")

        try:
            return await asyncio.wait_for(self._memory_queue.get(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            return None


# Global singleton queue
analysis_job_queue = AnalysisJobQueue()
