import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.gamification.domain.contracts import GameEventSource, GameEventType
from app.domains.gamification.domain.game_event import GameEvent
from app.domains.gamification.application.streak_service import StreakService
from app.domains.gamification.application.quest_engine import QuestEngine


@pytest.mark.asyncio
async def test_streak_service_recording_and_overview(db_session: AsyncSession):
    """Verify streak recording is idempotent and tracks daily activity."""
    streak_service = StreakService(db_session)
    user_id = "test_user_streak_1"

    # Record initial activity
    cur_streak, incremented = await streak_service.record_qualifying_activity(
        user_id=user_id,
        activity_type="exercise.completed",
        activity_id="test_act_1",
    )
    assert cur_streak >= 1

    # Second activity same day should not double increment
    cur_streak_2, incremented_2 = await streak_service.record_qualifying_activity(
        user_id=user_id,
        activity_type="conversation.completed",
        activity_id="test_act_2",
    )
    assert cur_streak_2 == cur_streak
    assert incremented_2 is False

    overview = await streak_service.get_streak_overview(user_id)
    assert overview["current_streak"] >= 1
    assert overview["is_qualified_today"] is True
    assert len(overview["activity_history_last_7_days"]) == 7


@pytest.mark.asyncio
async def test_quest_engine_generation_and_progress(db_session: AsyncSession):
    """Verify daily and weekly quests are generated and advance upon GameEvents."""
    quest_engine = QuestEngine(db_session)
    user_id = "test_user_quests_1"

    # Ensure quests
    daily_quests = await quest_engine.ensure_daily_quests(user_id)
    assert len(daily_quests) == 3

    weekly_quests = await quest_engine.ensure_weekly_quests(user_id)
    assert len(weekly_quests) >= 2

    # Process an event
    event = GameEvent(
        user_id=user_id,
        type=GameEventType.EXERCISE_COMPLETED,
        source=GameEventSource.LEARNING,
        source_id="quest_ex_test_1",
        metadata={"difficulty": "normal"},
    )
    completed = await quest_engine.process_event_for_quests(event)

    # Retrieve DTOs
    all_dtos = await quest_engine.get_all_active_quests_dto(user_id)
    assert len(all_dtos) >= 5
    assert any(q.current_count > 0 for q in all_dtos)
