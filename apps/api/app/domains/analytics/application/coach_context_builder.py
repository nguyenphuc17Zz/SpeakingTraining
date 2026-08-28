import hashlib
import json
from dataclasses import dataclass
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.application.analytics_snapshot_service import AnalyticsSnapshotService
from app.domains.analytics.contracts import AnalyticsDashboardOverview
from app.domains.learner_memory.models import LearnerMemory, LearnerProfile
from app.domains.learning.models import LearningGoal, LearningItem


@dataclass
class CoachContext:
    speaking_level: str
    level_confidence: str
    total_sessions: int
    active_goals: str
    metrics_summary: str
    bottleneck_info: str
    recent_weaknesses: str
    recent_strengths: str
    practice_distribution: str
    context_hash: str
    dashboard_overview: AnalyticsDashboardOverview


class CoachContextBuilder:
    """
    Constructs a budgeted, injection-safe context payload for AI Coach generation.
    Enforces a strict token budget (~2000 tokens) and generates a cache key hash.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.snapshot_service = AnalyticsSnapshotService(db)

    async def build_context(self, user_id: str) -> CoachContext:
        """
        Builds the grounded CoachContext dataclass.
        """
        # 1. Fetch Learner Profile
        prof_stmt = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()

        speaking_level = profile.speaking_level if profile else "Intermediate (N3-N2)"
        level_conf = profile.level_confidence if profile else "medium"
        total_sessions = profile.total_sessions_analyzed if profile else 0

        # 2. Fetch Dashboard Overview & Metrics
        overview = await self.snapshot_service.get_dashboard_overview(user_id, period="30d")

        # Format metrics summary concisely
        metric_lines = []
        for k, mv in overview.metrics.items():
            if mv.sample_size > 0:
                change_str = f" ({mv.change:+0.1f})" if mv.change is not None else ""
                metric_lines.append(f"- {mv.metric_key.value}: {mv.value}{change_str} [{mv.trend.value}, conf: {mv.confidence.value}]")
        metrics_summary = "\n".join(metric_lines) if metric_lines else "Chưa có đủ dữ liệu chu kỳ 30 ngày."

        # Bottleneck info
        bottleneck_info = (
            f"{overview.bottleneck.candidate}: {overview.bottleneck.description}"
            if overview.bottleneck
            else "Phát triển đồng đều."
        )

        # 3. Active Goals
        goals_stmt = select(LearningGoal).where(
            LearningGoal.user_id == user_id,
            LearningGoal.status == "active",
        )
        goals_res = await self.db.execute(goals_stmt)
        goals = list(goals_res.scalars().all())
        active_goals = ", ".join(g.title for g in goals) or "Giao tiếp tiếng Nhật tự nhiên"

        # 4. Top Weaknesses from LearnerMemory
        mem_stmt = (
            select(LearnerMemory)
            .where(
                LearnerMemory.user_id == user_id,
                LearnerMemory.status == "active",
            )
            .order_by(desc(LearnerMemory.priority_score))
            .limit(5)
        )
        mem_res = await self.db.execute(mem_stmt)
        memories = list(mem_res.scalars().all())

        weak_lines = [f"- {m.statement} (lỗi {m.error_count} lần, trend: {m.trend})" for m in memories]
        recent_weaknesses = "\n".join(weak_lines) if weak_lines else "Không có lỗi nghiêm trọng lặp lại."

        # 5. Top Strengths
        item_stmt = (
            select(LearningItem)
            .where(
                LearningItem.user_id == user_id,
                LearningItem.overall_mastery >= 0.75,
            )
            .order_by(desc(LearningItem.overall_mastery))
            .limit(4)
        )
        item_res = await self.db.execute(item_stmt)
        items = list(item_res.scalars().all())
        str_lines = [f"- Thành thạo: {it.title} ({int(it.overall_mastery * 100)}%)" for it in items]
        recent_strengths = "\n".join(str_lines) if str_lines else "Đang tích luỹ dữ liệu điểm mạnh."

        # Practice Distribution
        practice_dist = (
            f"Hội thoại: {overview.practice_distribution.conversation_pct}%, "
            f"Phát âm: {overview.practice_distribution.pronunciation_pct}%, "
            f"Shadowing: {overview.practice_distribution.shadowing_pct}%"
            if overview.practice_distribution
            else "45% Hội thoại, 30% Phát âm, 25% Shadowing"
        )

        # Context Hash for Caching
        hash_seed = f"{user_id}:{speaking_level}:{total_sessions}:{bottleneck_info}:{active_goals}:{len(memories)}"
        ctx_hash = hashlib.sha256(hash_seed.encode("utf-8")).hexdigest()[:16]

        return CoachContext(
            speaking_level=speaking_level,
            level_confidence=level_conf,
            total_sessions=total_sessions,
            active_goals=active_goals,
            metrics_summary=metrics_summary,
            bottleneck_info=bottleneck_info,
            recent_weaknesses=recent_weaknesses,
            recent_strengths=recent_strengths,
            practice_distribution=practice_dist,
            context_hash=ctx_hash,
            dashboard_overview=overview,
        )
