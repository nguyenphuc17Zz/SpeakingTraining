import asyncio
from typing import Any
from dataclasses import dataclass


@dataclass
class AnalyticsJob:
    job_type: str  # calculate_session_analytics, refresh_snapshot, generate_weekly_review
    payload: dict[str, Any]


class AnalyticsQueue:
    def __init__(self):
        self._queue: asyncio.Queue[AnalyticsJob] = asyncio.Queue()

    async def enqueue(self, job_type: str, payload: dict[str, Any]) -> None:
        await self._queue.put(AnalyticsJob(job_type=job_type, payload=payload))

    async def dequeue(self) -> AnalyticsJob:
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()


analytics_queue = AnalyticsQueue()
