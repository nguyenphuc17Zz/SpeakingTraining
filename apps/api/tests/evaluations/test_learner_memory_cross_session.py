import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.learner_memory.contracts import MemoryCandidate, MemoryType
from app.domains.learner_memory.merger import MemoryMerger
from app.domains.learner_memory.models import LearnerMemory
from app.domains.learner_memory.profile_service import LearnerProfileService
from app.domains.users.models import User


@pytest.mark.asyncio
async def test_learner_memory_multi_session_lifecycle_and_convergence(db_session: AsyncSession):
    """
    Evaluates multi-session progression scenario:
    Session 1: 3x は/が errors -> Single memory created
    Session 2: 2x は/が errors -> Deduplication verified, confidence increases
    Session 3: 3x correct usages -> Trend transitions to 'improving', mastery increases
    Session 4: 2x correct in workplace context -> Context variety bonus applied
    Session 5: 1x error -> Regression tracked; no duplicate memory created.
    """
    user = User(
        id="user-cross-session-eval",
        display_name="Eval Learner",
        timezone="Asia/Tokyo",
        locale="ja-JP",
    )
    db_session.add(user)
    await db_session.commit()

    merger = MemoryMerger(db_session)
    profile_service = LearnerProfileService(db_session)

    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)

    # --- SESSION 1: 3x は/が errors (4 days ago) ---
    sess1_candidates = [
        MemoryCandidate(
            memory_type=MemoryType.PARTICLE,
            key="particle.ha_vs_ga",
            statement="Nhầm lẫn trợ từ は và が",
            severity="MUST_FIX",
            confidence=0.85,
            evidence_weight=1.0,
            evidence_type="error_observation",
            original_snippet=f"私は猫が好きです_{i}",
            corrected_snippet="私が猫は好きです",
            session_id="session-eval-1",
            turn_id=f"s1-t{i}",
            context_tag="casual",
            created_at=now - timedelta(days=4, minutes=30 - i * 5),
        )
        for i in range(1, 4)
    ]
    await merger.merge_candidates(user.id, sess1_candidates)
    await db_session.commit()

    await profile_service.recalculate_profile(user.id, generate_ai_summary=False)

    # Verify after Session 1
    stmt = select(LearnerMemory).where(LearnerMemory.user_id == user.id, LearnerMemory.key == "particle.ha_vs_ga")
    res = await db_session.execute(stmt)
    mem1 = res.scalar_one()
    assert mem1.evidence_count == 3
    assert mem1.error_count == 3
    assert mem1.correct_count == 0
    assert mem1.status in ("new", "active")
    assert mem1.mastery < 0.3
    initial_conf = mem1.confidence

    # --- SESSION 2: 2x は/が errors (3 days ago, Same key) ---
    sess2_candidates = [
        MemoryCandidate(
            memory_type=MemoryType.PARTICLE,
            key="particle.ha_vs_ga",
            statement="Nhầm lẫn trợ từ は và が",
            severity="MUST_FIX",
            confidence=0.90,
            evidence_weight=1.0,
            evidence_type="error_observation",
            session_id="session-eval-2",
            turn_id=f"s2-t{i}",
            context_tag="casual",
            created_at=now - timedelta(days=3, minutes=30 - i * 5),
        )
        for i in range(1, 3)
    ]
    await merger.merge_candidates(user.id, sess2_candidates)
    await db_session.commit()

    await profile_service.recalculate_profile(user.id, generate_ai_summary=False)

    # Verify deduplication after Session 2 (Only 1 memory record exists for this key!)
    stmt_all = select(LearnerMemory).where(LearnerMemory.user_id == user.id, LearnerMemory.key == "particle.ha_vs_ga")
    res_all = await db_session.execute(stmt_all)
    all_records = res_all.scalars().all()
    assert len(all_records) == 1, "Deduplication failed: multiple memories created for same key!"
    mem2 = all_records[0]
    assert mem2.evidence_count == 5
    assert mem2.error_count == 5
    assert mem2.confidence > initial_conf, "Confidence should increase with cross-session evidence."
    prev_mastery_s2 = float(mem2.mastery)

    # --- SESSION 3: 3x correct usages (2 days ago) ---
    sess3_candidates = [
        MemoryCandidate(
            memory_type=MemoryType.PARTICLE,
            key="particle.ha_vs_ga",
            statement="Nhầm lẫn trợ từ は và が",
            severity="SHOULD_FIX",
            confidence=0.85,
            evidence_weight=0.7,
            evidence_type="correct_observation",
            original_snippet=f"猫が好きです_{i}",
            corrected_snippet=f"猫が好きです_{i}",
            session_id="session-eval-3",
            turn_id=f"s3-t{i}",
            context_tag="casual",
            created_at=now - timedelta(days=2, minutes=30 - i * 5),
        )
        for i in range(1, 4)
    ]
    await merger.merge_candidates(user.id, sess3_candidates)
    await db_session.commit()

    await profile_service.recalculate_profile(user.id, generate_ai_summary=False)

    res3 = await db_session.execute(stmt)
    mem3 = res3.scalar_one()
    assert mem3.evidence_count == 8
    assert mem3.correct_count == 3
    assert mem3.trend == "improving", f"Expected improving trend, got {mem3.trend}"
    assert mem3.mastery > prev_mastery_s2
    prev_mastery_s3 = float(mem3.mastery)

    # --- SESSION 4: 2x correct usages in workplace context (1 day ago) ---
    sess4_candidates = [
        MemoryCandidate(
            memory_type=MemoryType.PARTICLE,
            key="particle.ha_vs_ga",
            statement="Nhầm lẫn trợ từ は và が",
            severity="SHOULD_FIX",
            confidence=0.90,
            evidence_weight=0.7,
            evidence_type="correct_observation",
            session_id="session-eval-4",
            turn_id=f"s4-t{i}",
            context_tag="workplace",
            created_at=now - timedelta(days=1, minutes=30 - i * 5),
        )
        for i in range(1, 3)
    ]
    await merger.merge_candidates(user.id, sess4_candidates)
    await db_session.commit()

    await profile_service.recalculate_profile(user.id, generate_ai_summary=False)

    res4 = await db_session.execute(stmt)
    mem4 = res4.scalar_one()
    assert mem4.evidence_count == 10
    assert "workplace" in mem4.contexts_used
    assert "casual" in mem4.contexts_used
    assert mem4.mastery >= prev_mastery_s3

    # --- SESSION 5: 1x error mistake again (today) ---
    sess5_candidates = [
        MemoryCandidate(
            memory_type=MemoryType.PARTICLE,
            key="particle.ha_vs_ga",
            statement="Nhầm lẫn trợ từ は và が",
            severity="MUST_FIX",
            confidence=0.88,
            evidence_weight=1.0,
            evidence_type="error_observation",
            session_id="session-eval-5",
            turn_id="s5-t1",
            context_tag="workplace",
            created_at=now - timedelta(minutes=5),
        )
    ]
    await merger.merge_candidates(user.id, sess5_candidates)
    await db_session.commit()

    await profile_service.recalculate_profile(user.id, generate_ai_summary=False)

    res5 = await db_session.execute(stmt)
    mem5 = res5.scalar_one()
    assert mem5.evidence_count == 11
    assert mem5.error_count == 6
    assert mem5.correct_count == 5
    assert mem5.status == "active"

    # Verify again only 1 single memory record exists across all 5 sessions
    res_final = await db_session.execute(stmt_all)
    assert len(res_final.scalars().all()) == 1
