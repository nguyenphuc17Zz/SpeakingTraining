from typing import Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask
from app.domains.ai.router import AIRouter
from app.domains.analytics.application.analytics_snapshot_service import AnalyticsSnapshotService
from app.domains.analytics.application.bottleneck_analyzer import BottleneckAnalyzer
from app.domains.analytics.application.goal_analytics_service import GoalAnalyticsService
from app.domains.analytics.application.insight_engine import InsightEngine
from app.domains.analytics.application.metric_engine import MetricEngine
from app.domains.analytics.application.weekly_review_service import WeeklyReviewService
from app.domains.analytics.domain.metric_definitions import METRIC_REGISTRY, MetricKey
from app.domains.analytics.models import InsightRecord
from app.domains.analytics.schemas import (
    AnalyticsDashboardDTO,
    BottleneckDTO,
    GoalProgressDTO,
    InsightDTO,
    MetricValueDTO,
    PracticeDistributionDTO,
    WeeklyReviewDTO,
)
from app.domains.learning.models import ExerciseAttempt
from app.domains.users.service import UserService
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


async def get_user_id(db: AsyncSession = Depends(get_db)) -> str:
    """Resolve to real default user (UUID) matching all learning and practice endpoints."""
    user_service = UserService(db)
    user = await user_service.get_or_create_default_user()
    return user.id


@router.get("/dashboard", response_model=AnalyticsDashboardDTO)
async def get_analytics_dashboard(
    period: str = Query(default="30d"),
    force_refresh: bool = Query(default=False),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsSnapshotService(db)
    overview = await service.get_dashboard_overview(user_id, period=period, force_refresh=force_refresh)

    # Convert to DTO
    metrics_dto: dict[str, MetricValueDTO] = {}
    for k, mv in overview.metrics.items():
        defn = METRIC_REGISTRY.get(mv.metric_key)
        metrics_dto[k] = MetricValueDTO(
            metric_key=mv.metric_key.value,
            name=defn.name if defn else mv.metric_key.value,
            ja_name=defn.ja_name if defn else "",
            unit=defn.unit if defn else "",
            category=defn.category if defn else "",
            description=defn.description if defn else "",
            value=mv.value,
            baseline=mv.baseline,
            change=mv.change,
            sample_size=mv.sample_size,
            confidence=mv.confidence.value,
            period=mv.period,
            trend=mv.trend.value,
            metric_version=mv.metric_version,
        )

    bottleneck_dto = (
        BottleneckDTO(
            candidate=overview.bottleneck.candidate,
            confidence=overview.bottleneck.confidence.value,
            description=overview.bottleneck.description,
            evidence_keys=overview.bottleneck.evidence_keys,
            suggested_focus=overview.bottleneck.suggested_focus,
        )
        if overview.bottleneck
        else None
    )

    insights_dto = [
        InsightDTO(
            id=i.id,
            insight_type=i.insight_type.value,
            title=i.title,
            description=i.description,
            confidence=i.confidence.value,
            metric_key=i.metric_key.value if i.metric_key else None,
            metric_value=i.metric_value,
            action_hint=i.action_hint,
            action_target_type=i.action_target_type,
            action_target_key=i.action_target_key,
            evidence_keys=i.evidence_keys,
            lifecycle=i.lifecycle.value,
            generated_at=i.generated_at,
        )
        for i in overview.top_insights
    ]

    goals_dto = [
        GoalProgressDTO(
            goal_id=g.goal_id,
            title=g.title,
            goal_type=g.goal_type,
            progress_ratio=g.progress_ratio,
            confidence=g.confidence.value,
            recent_activity_count=g.recent_activity_count,
            linked_items_count=g.linked_items_count,
            blocked_by=g.blocked_by,
            next_actions=g.next_actions,
        )
        for g in overview.goals
    ]

    distrib_dto = (
        PracticeDistributionDTO(
            total_minutes=overview.practice_distribution.total_minutes,
            conversation_pct=overview.practice_distribution.conversation_pct,
            pronunciation_pct=overview.practice_distribution.pronunciation_pct,
            shadowing_pct=overview.practice_distribution.shadowing_pct,
            review_pct=overview.practice_distribution.review_pct,
            drill_pct=overview.practice_distribution.drill_pct,
            recommendation_note=overview.practice_distribution.recommendation_note,
        )
        if overview.practice_distribution
        else None
    )

    return AnalyticsDashboardDTO(
        user_id=user_id,
        period=overview.period,
        metrics=metrics_dto,
        bottleneck=bottleneck_dto,
        top_insights=insights_dto,
        goals=goals_dto,
        practice_distribution=distrib_dto,
    )


# ── AI Sensei 360 Diagnostic Report ──
@router.get("/diagnostic")
async def get_sensei_diagnostic(
    period: str = Query(default="30d"),
    persona: str = Query(default="tanaka"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Synthesizes comprehensive 360-degree diagnostic report analyzing 4 speaking pillars."""
    from sqlalchemy.orm import selectinload

    stmt = (
        select(ExerciseAttempt)
        .options(selectinload(ExerciseAttempt.exercise))
        .where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.status == "completed")
        .order_by(desc(ExerciseAttempt.started_at))
        .limit(100)
    )
    res = await db.execute(stmt)
    attempts = list(res.scalars().all())

    def get_ex_type(a: ExerciseAttempt) -> str:
        if a.exercise and a.exercise.exercise_type:
            return a.exercise.exercise_type.lower()
        mj = a.metrics_json or {}
        return (mj.get("mode") or mj.get("exercise_type") or "").lower()

    reflex_attempts = [a for a in attempts if "reflex" in get_ex_type(a)]
    keigo_attempts = [a for a in attempts if "keigo" in get_ex_type(a)]
    pitch_attempts = [a for a in attempts if "pitch" in get_ex_type(a) or "mora" in get_ex_type(a)]
    situational_attempts = [a for a in attempts if "situat" in get_ex_type(a)]

    def avg_score(items: list[ExerciseAttempt]) -> float:
        if not items:
            return 0.0
        scores = [a.score for a in items if a.score is not None]
        return round(sum(scores) / len(scores), 1) if scores else 0.0

    pillars = {
        "reflex": {
            "name": "Phản Xạ (Reflex)",
            "icon": "⚡",
            "count": len(reflex_attempts),
            "avg_score": avg_score(reflex_attempts),
            "status": "Thành thạo" if avg_score(reflex_attempts) >= 80 else "Đang cải thiện",
        },
        "keigo": {
            "name": "Kính Ngữ (Keigo)",
            "icon": "👑",
            "count": len(keigo_attempts),
            "avg_score": avg_score(keigo_attempts),
            "status": "Thành thạo" if avg_score(keigo_attempts) >= 80 else "Đang cải thiện",
        },
        "pitch": {
            "name": "Cao Độ & Phách (Pitch & Mora)",
            "icon": "🎵",
            "count": len(pitch_attempts),
            "avg_score": avg_score(pitch_attempts),
            "status": "Thành thạo" if avg_score(pitch_attempts) >= 80 else "Đang cải thiện",
        },
        "situations": {
            "name": "Tình Huống Thực Chiến (Situations)",
            "icon": "🎭",
            "count": len(situational_attempts),
            "avg_score": avg_score(situational_attempts),
            "status": "Thành thạo" if avg_score(situational_attempts) >= 80 else "Đang cải thiện",
        },
    }

    ai_router = AIRouter(db)
    prompt = (
        f"Hãy chẩn đoán năng lực nói tiếng Nhật 360 độ cho học viên dựa trên số liệu thực tế:\n"
        f"- Tổng số lượt luyện tập: {len(attempts)}\n"
        f"- Phản xạ: {pillars['reflex']['count']} bài (Điểm TB: {pillars['reflex']['avg_score']})\n"
        f"- Kính ngữ: {pillars['keigo']['count']} bài (Điểm TB: {pillars['keigo']['avg_score']})\n"
        f"- Cao độ & Phách: {pillars['pitch']['count']} bài (Điểm TB: {pillars['pitch']['avg_score']})\n"
        f"- Tình huống thực tế: {pillars['situations']['count']} bài (Điểm TB: {pillars['situations']['avg_score']})\n\n"
        f"Trả về đúng định dạng JSON:\n"
        f"{{\n"
        f"  \"estimated_level\": \"N3 - Trung cấp\",\n"
        f"  \"summary_title\": \"Tiến độ rèn luyện đa kỹ năng đang phát triển tích cực\",\n"
        f"  \"narrative\": \"Bạn đã hoàn thành các bài luyện với độ tập trung cao.\",\n"
        f"  \"top_strengths\": [\"Phản xạ câu đơn nhanh\", \"Nắm vững thể Desu/Masu\"],\n"
        f"  \"core_bottleneck\": \"Cần trau chuốt thêm về tính chuẩn xác Kính ngữ và ngữ điệu câu dài.\",\n"
        f"  \"action_plan\": \"Dành 10 phút luyện Kính ngữ và 5 phút Cao độ Tokyo mỗi ngày.\",\n"
        f"  \"recommended_route\": \"/keigo\"\n"
        f"}}"
    )

    try:
        req = AIRequest(
            messages=[AIMessage(role=AIMessageRole.USER, content=prompt)],
            system_instruction="Bạn là Trưởng ban Khảo thí tiếng Nhật. Trả về đúng JSON.",
            temperature=0.7,
        )
        resp = await ai_router.generate(task=AITask.COACH_INSIGHT, request=req, user_id=user_id)
        import json
        t = resp.text.strip()
        if t.startswith("```"):
            t = t.split("\n", 1)[-1] if "\n" in t else t
            if t.endswith("```"):
                t = t[:-3]
            t = t.strip()
            if t.startswith("json"):
                t = t[4:].strip()
        report = json.loads(t)
    except Exception:
        report = {
            "estimated_level": "N3 - Trung cấp",
            "summary_title": "Tiến độ rèn luyện đa kỹ năng đang phát triển tích cực",
            "narrative": f"Bạn đã hoàn thành tổng cộng {len(attempts)} bài luyện. Nền tảng phản xạ và ngữ pháp đang ổn định.",
            "top_strengths": ["Phản xạ câu đơn nhanh", "Độ chính xác ngữ pháp cơ bản"],
            "core_bottleneck": "Cần trau chuốt thêm về tính chuẩn xác Kính ngữ và ngữ điệu câu dài.",
            "action_plan": "Dành 10 phút luyện Kính ngữ và 5 phút Cao độ Tokyo mỗi ngày.",
            "recommended_route": "/keigo",
        }

    return {
        "period": period,
        "total_attempts": len(attempts),
        "pillars": pillars,
        "diagnostic_report": report,
    }

# ── Real Activity Speaking Heatmap Endpoint ──
@router.get("/activity-heatmap")
async def get_speaking_activity_heatmap(
    weeks: int = Query(default=14, ge=4, le=52),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves real daily speaking practice duration for the past N weeks."""
    from datetime import datetime, timedelta, timezone
    from app.domains.gamification.models import DailyStreakActivity
    from app.domains.learning.models import ExerciseAttempt

    now = datetime.now(timezone.utc)
    total_days = weeks * 7
    start_date = (now - timedelta(days=total_days - 1)).date()

    start_date_str = start_date.strftime("%Y-%m-%d")

    # Query streak activities
    streak_stmt = (
        select(DailyStreakActivity)
        .where(
            DailyStreakActivity.user_id == user_id,
            DailyStreakActivity.activity_date >= start_date_str,
        )
    )
    s_res = await db.execute(streak_stmt)
    streak_activities = list(s_res.scalars().all())

    # Query exercise attempts
    att_stmt = (
        select(ExerciseAttempt)
        .where(
            ExerciseAttempt.user_id == user_id,
            ExerciseAttempt.started_at >= datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc),
            ExerciseAttempt.status == "completed",
        )
    )
    a_res = await db.execute(att_stmt)
    attempts = list(a_res.scalars().all())

    # Aggregate minutes by date string YYYY-MM-DD
    daily_minutes: dict[str, int] = {}
    for sa in streak_activities:
        d_str = str(sa.activity_date)
        daily_minutes[d_str] = daily_minutes.get(d_str, 0) + 5

    for att in attempts:
        if att.started_at:
            d_str = att.started_at.strftime("%Y-%m-%d")
            if att.completed_at and att.started_at:
                sec = max(30, (att.completed_at - att.started_at).total_seconds())
                mins = max(1, round(sec / 60))
            else:
                mins = 3
            daily_minutes[d_str] = daily_minutes.get(d_str, 0) + mins

    # Build the full date list
    days_list = []
    total_mins = 0
    for i in range(total_days - 1, -1, -1):
        d = (now - timedelta(days=i)).date()
        d_str = d.strftime("%Y-%m-%d")
        mins = daily_minutes.get(d_str, 0)
        total_mins += mins

        level = 0
        if mins >= 20:
            level = 4
        elif mins >= 12:
            level = 3
        elif mins >= 5:
            level = 2
        elif mins > 0:
            level = 1

        days_list.append({
            "date": d_str,
            "minutes": mins,
            "level": level,
        })

    return {
        "weeks": weeks,
        "total_days": total_days,
        "total_speaking_minutes": total_mins,
        "days": days_list,
    }

