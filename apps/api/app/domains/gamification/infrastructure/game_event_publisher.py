from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.gamification.application.game_event_processor import EventProcessingResult, GameEventProcessor
from app.domains.gamification.domain.contracts import GameEventSource, GameEventType
from app.domains.gamification.domain.game_event import GameEvent
from app.domains.gamification.queue import game_queue


class GameEventPublisher:
    """
    Decoupled outbound publisher for emitting learning events to the gamification engine.
    Other domains only depend on this publisher interface, keeping coupling minimal.
    """

    @classmethod
    async def publish(
        cls,
        user_id: str,
        event_type: GameEventType | str,
        source: GameEventSource | str,
        source_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Asynchronously publishes a GameEvent to the background processing queue.
        """
        ev_type = event_type if isinstance(event_type, GameEventType) else GameEventType(str(event_type))
        ev_src = source if isinstance(source, GameEventSource) else GameEventSource(str(source))

        event = GameEvent(
            user_id=user_id,
            type=ev_type,
            source=ev_src,
            source_id=source_id,
            metadata=metadata or {},
        )

        enqueued = await game_queue.enqueue(event)
        return enqueued

    @classmethod
    async def publish_sync(
        cls,
        db: AsyncSession,
        user_id: str,
        event_type: GameEventType | str,
        source: GameEventSource | str,
        source_id: str,
        metadata: dict[str, Any] | None = None,
    ) -> EventProcessingResult:
        """
        Synchronously processes a GameEvent within the caller's active database transaction.
        """
        ev_type = event_type if isinstance(event_type, GameEventType) else GameEventType(str(event_type))
        ev_src = source if isinstance(source, GameEventSource) else GameEventSource(str(source))

        event = GameEvent(
            user_id=user_id,
            type=ev_type,
            source=ev_src,
            source_id=source_id,
            metadata=metadata or {},
        )

        processor = GameEventProcessor(db)
        return await processor.process_event(event)
