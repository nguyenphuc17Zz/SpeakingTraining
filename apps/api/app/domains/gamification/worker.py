import asyncio
from app.core.logging import logger
from app.domains.gamification.application.game_event_processor import GameEventProcessor
from app.domains.gamification.queue import game_queue
from app.infrastructure.database.session import AsyncSessionLocal


class GameWorker:
    """
    Background worker that continuously dequeues and idempotently processes GameEvents.
    Ensures that failures in gamification event processing NEVER fail active learning actions.
    """

    def __init__(self):
        self._task: asyncio.Task | None = None
        self._running = False
        self.jobs_processed: int = 0
        self.jobs_failed: int = 0

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("[GameWorker] Background gamification worker started.")

    async def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[GameWorker] Background gamification worker stopped.")

    async def _process_loop(self) -> None:
        while self._running:
            try:
                event = await game_queue.dequeue()
                async with AsyncSessionLocal() as session:
                    try:
                        processor = GameEventProcessor(session)
                        res = await processor.process_event(event)
                        if not res.is_duplicate and res.xp_awarded > 0:
                            logger.info(
                                f"[GameWorker] Processed {event.type.value} -> +{res.xp_awarded} XP ({res.reason})"
                            )
                        self.jobs_processed += 1
                    except Exception as e:
                        self.jobs_failed += 1
                        logger.error(f"[GameWorker] Error processing game event: {e}", exc_info=True)
                game_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[GameWorker] Unexpected error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)


game_worker = GameWorker()
