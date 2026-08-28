from datetime import datetime, timezone
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.domains.learner_memory.models import LearnerMemory
from app.domains.learning.daily_plan_generator import DailyPlanGenerator
from app.domains.learning.exercise_session_service import ExerciseSessionService
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.models import Exercise, ExerciseAttempt, LearningItem, LearningPlan
from app.domains.users.models import User
from app.infrastructure.database.base import Base


@pytest.fixture
async def test_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_end_to_end_adaptive_learning_flow(test_db: AsyncSession):
    # 1. Seed user and memory
    user = User(id="u_test_1", display_name="Test User", locale="ja-JP")
    test_db.add(user)

    mem1 = LearnerMemory(
        user_id="u_test_1",
        memory_type="grammar",
        key="grammar.わけではない",
        statement="〜わけではない",
        severity="MUST_FIX",
        severity_score=80,
        priority_score=0.85,
        mastery=0.35,
        confidence=0.8,
        attempt_count=4,
        correct_count=1,
        error_count=3,
        first_seen=datetime.now(timezone.utc),
        last_seen=datetime.now(timezone.utc),
        trend="new",
        status="active",
    )
    test_db.add(mem1)
    await test_db.commit()

    # 2. Sync memory into LearningItems
    item_svc = LearningItemService(test_db)
    synced = await item_svc.sync_from_memory("u_test_1")
    assert len(synced) >= 1
    assert synced[0].key == "grammar.わけではない"
    initial_mastery = synced[0].overall_mastery
    assert initial_mastery >= 0.20

    # 3. Generate Daily Learning Plan
    plan_gen = DailyPlanGenerator(test_db)
    plan = await plan_gen.get_or_create_daily_plan(
        user_id="u_test_1",
        time_budget_minutes=20,
        regenerate=False,
    )
    assert plan is not None
    assert plan.user_id == "u_test_1"
    assert len(plan.items) >= 2
    plan_id = plan.id

    # 4. Verify Plan Persistence on same date refresh
    plan_cached = await plan_gen.get_or_create_daily_plan(
        user_id="u_test_1",
        time_budget_minutes=20,
        regenerate=False,
    )
    assert plan_cached.id == plan_id

    # 5. Start and Submit Exercise
    ex_to_practice = plan.items[0].exercise
    assert ex_to_practice is not None

    session_svc = ExerciseSessionService(test_db)
    attempt = await session_svc.start_exercise(ex_to_practice.id, "u_test_1")
    assert attempt.status == "in_progress"

    # Submit user response with target pattern
    result = await session_svc.submit_exercise_attempt(
        exercise_id=ex_to_practice.id,
        user_id="u_test_1",
        user_transcript="忙しいですが、行きたくないわけではないです。",
        plan_item_id=plan.items[0].id,
    )

    assert result.success is True
    assert result.score >= 70.0

    # 6. Verify closed-loop mastery delta & item progress
    updated_item = await item_svc.get_item_by_key("grammar.わけではない", "u_test_1")
    assert updated_item is not None
    assert updated_item.attempt_count >= 1
    assert updated_item.success_count >= 1
    assert updated_item.overall_mastery > 0.35  # Mastery increased!
    assert updated_item.next_review_at is not None  # Review scheduled
