import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learner_memory.models import LearnerMemory, LearnerProfile
from app.domains.learner_memory.retriever import MemoryRetriever
from app.domains.users.models import User


@pytest.mark.asyncio
async def test_memory_retriever_context_budget_and_prompt_safety(db_session: AsyncSession):
    # Setup test user and memories
    user = User(
        id="user-retriever-test",
        display_name="Learner Test",
        timezone="Asia/Tokyo",
        locale="ja-JP",
    )
    db_session.add(user)

    profile = LearnerProfile(
        user_id=user.id,
        overall_level="intermediate",
        level_confidence="medium",
        learning_goals=["Giao tiếp công sở tự nhiên"],
    )
    db_session.add(profile)

    now = datetime.now(timezone.utc)

    # Add memories: keigo, particles, casual filler
    mem1 = LearnerMemory(
        user_id=user.id,
        memory_type="politeness",
        key="politeness.keigo_avoidance",
        statement="Xu hướng né tránh kính ngữ với cấp trên",
        priority_score=0.85,
        mastery=0.4,
        trend="improving",
        status="active",
        contexts_used=["workplace"],
        last_seen=now,
    )
    mem2 = LearnerMemory(
        user_id=user.id,
        memory_type="particle",
        key="particle.ha_vs_ga",
        statement="Nhầm lẫn trợ từ は và が",
        priority_score=0.75,
        mastery=0.5,
        trend="stable",
        contexts_used=["casual"],
        last_seen=now,
    )
    mem3 = LearnerMemory(
        user_id=user.id,
        memory_type="strength",
        key="strength.turn_continuity",
        statement="Phản xạ nhanh và duy trì mạch hội thoại tốt",
        priority_score=0.80,
        mastery=0.9,
        trend="stable",
        status="active",
        last_seen=now,
    )
    db_session.add_all([mem1, mem2, mem3])
    await db_session.commit()

    # 1. Retrieve for Workplace context (Boss role)
    retriever = MemoryRetriever(db_session)
    budget = await retriever.retrieve_context(
        user_id=user.id,
        persona_role="Company Boss / Section Chief",
        topic_hint="workplace",
        max_items=3,
    )

    assert budget.level == "intermediate"
    assert len(budget.priority_weaknesses) >= 1
    # Politeness should be prioritized in workplace context
    assert any("kính ngữ" in w for w in budget.priority_weaknesses)
    # Check boundary isolation
    assert "<learner_memory>" in budget.compact_prompt_block
    assert "</learner_memory>" in budget.compact_prompt_block
    assert "company boss" not in budget.compact_prompt_block.lower()  # Should format cleanly without leaking raw query
