from datetime import datetime, timezone
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.conversation_intelligence.models import SessionAnalysis
from app.domains.learner_memory.models import LearnerMemory, LearnerProfile
from app.domains.learner_memory.profile_service import LearnerProfileService
from app.domains.learning.contracts import LearnerLearningState
from app.domains.learning.goal_service import GoalService
from app.domains.learning.models import LearningGoal, LearningItem
from app.domains.learning.review_scheduler import ReviewScheduler
from app.domains.pronunciation.models import PronunciationAttempt, PronunciationPracticeTarget


class LearnerStateService:
    """Constructs clean, immutable LearnerLearningState read-models for the adaptive learning engine."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_service = LearnerProfileService(db)
        self.goal_service = GoalService(db)

    async def build_learning_state(self, user_id: str) -> LearnerLearningState:
        """
        Builds a comprehensive, validated snapshot of the learner's state across all subsystems.
        Fast and code-driven.
        """
        # 1. Fetch or create profile
        profile = await self.profile_service.get_or_create_profile(user_id)

        # 2. Fetch active goals
        goals = await self.goal_service.get_or_create_default_goals(user_id)
        goal_titles = [g.title for g in goals]

        # 3. Fetch active learning items
        items_stmt = (
            select(LearningItem)
            .where(
                LearningItem.user_id == user_id,
                LearningItem.status == "active",
            )
            .order_by(desc(LearningItem.priority_score))
        )
        items_res = await self.db.execute(items_stmt)
        active_items = list(items_res.scalars().all())

        # Review due items
        due_items = ReviewScheduler.filter_due_items(active_items)

        # 4. Group priorities by linguistic dimension
        grammar_p = []
        fluency_p = []
        naturalness_p = []
        pron_p = []

        for it in active_items:
            it_dict = {
                "id": it.id,
                "key": it.key,
                "title": it.title,
                "item_type": it.item_type,
                "overall_mastery": it.overall_mastery,
                "priority_score": it.priority_score,
                "lifecycle": it.lifecycle,
                "attempt_count": it.attempt_count,
            }
            if it.item_type in ("grammar", "particle", "conjugation"):
                grammar_p.append(it_dict)
            elif it.item_type in ("pronunciation", "pitch_accent"):
                pron_p.append(it_dict)
            elif it.item_type in ("fluency", "filler"):
                fluency_p.append(it_dict)
            elif it.item_type in ("naturalness", "politeness", "word_choice"):
                naturalness_p.append(it_dict)

        # 5. Fetch recent pronunciation practice targets if active items in pronunciation are sparse
        if not pron_p:
            pt_stmt = (
                select(PronunciationPracticeTarget)
                .where((PronunciationPracticeTarget.user_id == user_id) | (PronunciationPracticeTarget.user_id.is_(None)))
                .limit(5)
            )
            pt_res = await self.db.execute(pt_stmt)
            for pt in pt_res.scalars().all():
                pron_p.append({
                    "id": pt.id,
                    "key": pt.weak_area_key,
                    "title": f"Phát âm: {pt.target_text} ({pt.category})",
                    "item_type": "pronunciation",
                    "overall_mastery": 0.35,
                    "priority_score": 0.70,
                    "lifecycle": "active",
                    "attempt_count": 0,
                })

        # 6. Compute mastery distribution
        mastery_dist = {
            "grammar": round(sum(it["overall_mastery"] for it in grammar_p) / max(1, len(grammar_p)), 2),
            "pronunciation": round(sum(it["overall_mastery"] for it in pron_p) / max(1, len(pron_p)), 2),
            "fluency": round(sum(it["overall_mastery"] for it in fluency_p) / max(1, len(fluency_p)), 2),
            "naturalness": round(sum(it["overall_mastery"] for it in naturalness_p) / max(1, len(naturalness_p)), 2),
        }

        # 7. Recent performance metrics from sessions & attempts
        recent_perf = {
            "total_sessions": profile.total_sessions_analyzed,
            "total_turns": profile.total_turns_analyzed,
            "avg_response_speed_ms": profile.avg_response_speed_ms,
            "current_focus": profile.current_focus,
        }

        return LearnerLearningState(
            user_id=user_id,
            overall_level=profile.overall_level,
            speaking_level=profile.speaking_level,
            confidence_score=profile.confidence_score,
            level_confidence=profile.level_confidence,
            active_goals=goal_titles,
            top_weaknesses=profile.weaknesses or [],
            top_strengths=profile.strengths or [],
            active_learning_items=[
                {
                    "id": it.id,
                    "key": it.key,
                    "title": it.title,
                    "item_type": it.item_type,
                    "overall_mastery": it.overall_mastery,
                    "priority_score": it.priority_score,
                    "lifecycle": it.lifecycle,
                    "next_review_at": it.next_review_at.isoformat() if it.next_review_at else None,
                }
                for it in active_items[:10]
            ],
            review_due_items=[
                {
                    "id": it.id,
                    "key": it.key,
                    "title": it.title,
                    "item_type": it.item_type,
                    "overall_mastery": it.overall_mastery,
                    "priority_score": it.priority_score,
                    "next_review_at": it.next_review_at.isoformat() if it.next_review_at else None,
                }
                for it in due_items
            ],
            pronunciation_priorities=pron_p[:5],
            grammar_priorities=grammar_p[:5],
            fluency_priorities=fluency_p[:5],
            naturalness_priorities=naturalness_p[:5],
            recent_performance=recent_perf,
            mastery_distribution=mastery_dist,
            timestamp=datetime.now(timezone.utc),
        )
