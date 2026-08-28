import asyncio
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.learning.daily_plan_generator import DailyPlanGenerator
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.queue import learning_job_queue
from app.infrastructure.database.session import AsyncSessionLocal


class LearningWorker:
    """Background worker processing asynchronous learning state updates, plan generation, and memory syncs."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self.jobs_processed: int = 0
        self.jobs_failed: int = 0

    @property
    def is_running(self) -> bool:
        return self._running

    async def execute_task(self, job_data: dict[str, Any], db_session: AsyncSession) -> None:
        """Executes a queued learning task."""
        task_type = job_data.get("task_type")
        user_id = job_data.get("user_id")

        if not task_type or not user_id:
            return

        logger.info(f"[LearningWorker] Processing task '{task_type}' for user '{user_id}'")

        if task_type == "LEARNING_STATE_RECALCULATION":
            item_service = LearningItemService(db_session)
            await item_service.sync_from_memory(user_id)
            logger.info(f"[LearningWorker] Completed learning state recalculation for user '{user_id}'")

        elif task_type == "DAILY_PLAN_GENERATION":
            plan_gen = DailyPlanGenerator(db_session)
            budget = job_data.get("time_budget_minutes", 30)
            await plan_gen.get_or_create_daily_plan(
                user_id=user_id,
                time_budget_minutes=budget,
                regenerate=job_data.get("regenerate", False),
            )
            logger.info(f"[LearningWorker] Completed daily plan generation for user '{user_id}'")

    async def _worker_loop(self) -> None:
        logger.info("[LearningWorker] Background loop started.")
        while self._running:
            try:
                job_data = await learning_job_queue.dequeue(timeout_seconds=2.0)
                if not job_data:
                    continue

                async with AsyncSessionLocal() as session:
                    await self.execute_task(job_data, session)
                self.jobs_processed += 1

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.jobs_failed += 1
                logger.error(f"[LearningWorker] Unexpected error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(1.0)

        logger.info("[LearningWorker] Background loop stopped.")

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._worker_loop())

    async def stop(self) -> None:
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
                self._task = None


learning_worker = LearningWorker()
