"""Tests for FollowUpGenerator (fallback and progression)."""

import pytest
from app.domains.ramp.contracts import FollowUpType
from app.domains.ramp.followup_generator import FollowUpGenerator


@pytest.mark.asyncio
async def test_followup_generator_fallback(db_session):
    generator = FollowUpGenerator(db_session)

    user_response = "週末は京都へ行って、お寺を見学しました。"
    topic = "旅行"

    # Depth 1: fact
    fu1 = await generator.generate(
        user_response=user_response,
        topic=topic,
        stage=5,
        current_depth=1,
    )
    assert fu1 is not None
    assert fu1.question_jp is not None
    assert len(fu1.question_jp) > 0

    # Depth 2: why
    fu2 = await generator.generate(
        user_response=user_response,
        topic=topic,
        stage=5,
        current_depth=2,
    )
    assert fu2 is not None
    assert fu2.follow_up_type in (FollowUpType.WHY, FollowUpType.FACT)


def test_followup_depth_progression(db_session):
    generator = FollowUpGenerator(db_session)
    next_depth = generator.get_next_depth(current_depth=1, previous_followups=["いつ行きましたか？"], stage=6)
    assert next_depth == 2
