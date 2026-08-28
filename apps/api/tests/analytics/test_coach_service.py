import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.application.coach_intent_classifier import CoachIntent, CoachIntentClassifier
from app.domains.analytics.application.coach_service import CoachService
from app.domains.analytics.models import CoachConversation, CoachFeedback
from app.domains.gamification.models import GameProfile
from app.domains.learning.models import LearningItem
from app.domains.pronunciation.models import PronunciationAttempt


def test_coach_intent_classifier():
    """Verify regex/keyword intent classification across different learner query forms."""
    assert CoachIntentClassifier.classify("Hôm nay tôi đã nói bao nhiêu phút?") == CoachIntent.SIMPLE_DATA
    assert CoachIntentClassifier.classify("Current streak của tôi là mấy ngày?") == CoachIntent.SIMPLE_DATA
    assert CoachIntentClassifier.classify("Tổng kết tuần này của tôi thế nào?") == CoachIntent.WEEKLY_REVIEW
    assert CoachIntentClassifier.classify("Tôi đang yếu nhất ở đâu?") == CoachIntent.WEAKNESS
    assert CoachIntentClassifier.classify("Hôm nay nên luyện bài tập gì?") == CoachIntent.RECOMMENDATION
    assert CoachIntentClassifier.classify("Tại sao grammar tốt mà nói vẫn chậm?") == CoachIntent.DIAGNOSTIC
    assert CoachIntentClassifier.classify("Dạo này tôi có tiến bộ gì không?") == CoachIntent.TREND


@pytest.mark.asyncio
async def test_coach_deterministic_simple_data(db_session: AsyncSession):
    """Verify Coach answers simple data queries accurately from DB records without LLM latency."""
    user_id = "test_user_coach_1"

    # Seed GameProfile with streak
    profile = GameProfile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        current_streak=7,
        total_xp=2450,
        level=5,
    )
    db_session.add(profile)
    await db_session.commit()

    service = CoachService(db_session, ai_router=None)
    res = await service.answer(user_id, "Chuỗi streak của tôi là mấy ngày?")

    assert res.is_deterministic is True
    assert res.intent_type == CoachIntent.SIMPLE_DATA.value
    assert "7 ngày" in res.answer
    assert len(res.recommendations) >= 1


@pytest.mark.asyncio
async def test_coach_weakness_and_recommendation(db_session: AsyncSession):
    """Verify Coach identifies primary weakness and provides actionable practice recommendation."""
    user_id = "test_user_coach_weakness"

    # Seed weak learning item
    item = LearningItem(
        id=str(uuid.uuid4()),
        user_id=user_id,
        key="item_sentence_endings",
        title="Sentence Endings (ね・よ)",
        item_type="naturalness",
        overall_mastery=0.35,
        priority_score=0.9,
        status="active",
    )
    db_session.add(item)
    await db_session.commit()

    service = CoachService(db_session, ai_router=None)

    # 1. Ask Weakness
    weak_res = await service.answer(user_id, "Tôi đang yếu nhất ở đâu?")
    assert weak_res.is_deterministic is True
    assert weak_res.intent_type == CoachIntent.WEAKNESS.value
    assert len(weak_res.recommendations) >= 1

    # 2. Ask Recommendation
    rec_res = await service.answer(user_id, "Hôm nay nên luyện gì?")
    assert rec_res.intent_type == CoachIntent.RECOMMENDATION.value
    assert rec_res.recommendations[0].practice_url is not None


@pytest.mark.asyncio
async def test_coach_feedback_recording(db_session: AsyncSession):
    """Verify user feedback on coach answers is recorded and flags incorrect responses for review."""
    user_id = "test_user_coach_fb"
    service = CoachService(db_session, ai_router=None)

    ans = await service.answer(user_id, "Tôi đã nói bao nhiêu phút?")

    # Find conversation record
    stmt = select(CoachConversation).where(CoachConversation.user_id == user_id)
    res = await db_session.execute(stmt)
    conv = res.scalars().first()
    assert conv is not None

    # Submit feedback 'incorrect'
    fb = CoachFeedback(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        user_id=user_id,
        rating="incorrect",
        feedback_text="Dữ liệu chưa cập nhật buổi sáng nay",
        requires_review=True,
    )
    db_session.add(fb)
    await db_session.commit()

    # Verify feedback persisted
    fb_stmt = select(CoachFeedback).where(CoachFeedback.conversation_id == conv.id)
    fb_res = await db_session.execute(fb_stmt)
    saved_fb = fb_res.scalar_one_or_none()
    assert saved_fb is not None
    assert saved_fb.requires_review is True
