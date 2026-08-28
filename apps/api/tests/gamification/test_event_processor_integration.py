import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.gamification.domain.contracts import GameEventSource, GameEventType
from app.domains.gamification.domain.game_event import GameEvent
from app.domains.gamification.application.game_event_processor import GameEventProcessor
from app.domains.gamification.application.progression_service import ProgressionService


@pytest.mark.asyncio
async def test_game_event_processor_idempotency_and_level_up(db_session: AsyncSession):
    """Verify processing pipeline is strictly idempotent and handles progression seamlessly."""
    processor = GameEventProcessor(db_session)
    prog_service = ProgressionService(db_session)

    user_id = "test_user_integration_1"

    event = GameEvent(
        user_id=user_id,
        type=GameEventType.EXERCISE_COMPLETED,
        source=GameEventSource.LEARNING,
        source_id="attempt_unique_999",
        metadata={"difficulty": "hard", "score": 95.0, "independence_level": "independent"},
    )

    # 1. First execution
    res1 = await processor.process_event(event)
    assert res1.is_duplicate is False
    assert res1.xp_awarded > 0

    # 2. Replay same event -> should be flagged duplicate with 0 new XP
    res2 = await processor.process_event(event)
    assert res2.is_duplicate is True
    assert res2.xp_awarded == 0

    # 3. Check GameProfile
    profile_dto = await prog_service.get_game_profile_dto(user_id)
    assert profile_dto.total_xp >= res1.xp_awarded
    assert profile_dto.current_streak >= 1
