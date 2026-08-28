import asyncio
from app.core.logging import logger
from app.domains.gamification.domain.game_event import GameEvent


class GameEventQueue:
    """Async in-memory queue for decoupling game event ingestion from real-time audio/dialogue loops."""

    def __init__(self, maxsize: int = 1000):
        self._queue: asyncio.Queue[GameEvent] = asyncio.Queue(maxsize=maxsize)

    async def enqueue(self, event: GameEvent) -> bool:
        """Pushes event onto background queue."""
        try:
            self._queue.put_nowait(event)
            logger.debug(f"[GameEventQueue] Enqueued event: {event.type.value} ({event.source_id})")
            return True
        except asyncio.QueueFull:
            logger.error("[GameEventQueue] Game event queue is full! Dropping event.")
            return False

    async def dequeue(self) -> GameEvent:
        """Pulls event for processing."""
        return await self._queue.get()

    def task_done(self) -> None:
        self._queue.task_done()

    def qsize(self) -> int:
        return self._queue.qsize()


game_queue = GameEventQueue()
