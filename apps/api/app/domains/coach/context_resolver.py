"""CoachContextResolver §7 — determines what learner is doing and what evidence is relevant."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.analytics.application.analytics_snapshot_service import AnalyticsSnapshotService
from app.domains.coach.context_budget import CoachContextBudget
from app.domains.coach.contracts import CoachContext, CoachMode
from app.domains.gamification.models import GameProfile
from app.domains.learner_memory.models import LearnerMemory, LearnerProfile
from app.domains.learning.models import Exercise, ExerciseAttempt, LearningGoal, LearningItem


# Route → Mode mapping
ROUTE_MODE_MAP: dict[str, CoachMode] = {
    "/speaking": CoachMode.FREE_SPEAKING,
    "/reflex": CoachMode.REFLEX,
    "/keigo": CoachMode.KEIGO,
    "/pitch": CoachMode.PITCH,
    "/situations": CoachMode.SITUATIONAL,
    "/speaking/speech": CoachMode.MONOLOGUE,
    "/speaking/pronunciation": CoachMode.PITCH,
    "/progress": CoachMode.PROGRESS,
    "/learning": CoachMode.LEARNING,
    "/shadowing": CoachMode.SHADOWING,
    "/dashboard": CoachMode.DASHBOARD,
    "/profile": CoachMode.REVIEW,
}


def _infer_mode_from_route(route: str) -> CoachMode:
    if not route:
        return CoachMode.UNKNOWN
    # longest prefix wins
    matched = CoachMode.UNKNOWN
    best_len = -1
    for prefix, mode in ROUTE_MODE_MAP.items():
        if route.startswith(prefix) and len(prefix) > best_len:
            matched = mode
            best_len = len(prefix)
    return matched


_CONTEXT_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 60.0  # seconds §61

class CoachContextResolver:
    """Resolves full CoachContext with selective evidence per Spec §7."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.snapshot_service = AnalyticsSnapshotService(db)

    async def resolve(
        self,
        user_id: str,
        current_route: str = "/dashboard",
        current_exercise_id: str | None = None,
        current_session_id: str | None = None,
        question: str | None = None,
    ) -> CoachContext:
        # cache check §61 (§61: invalidate on new evidence — TTL short)
        cache_key = f"{user_id}:{current_route}:{current_exercise_id or ''}:{current_session_id or ''}:{hash(question) if question else 0}"
        now = time.time()
        if cache_key in _CONTEXT_CACHE:
            ts, cached = _CONTEXT_CACHE[cache_key]
            if now - ts < _CACHE_TTL:
                return cached
        mode = _infer_mode_from_route(current_route)

        # 1. Learner profile
        prof_stmt = select(LearnerProfile).where(LearnerProfile.user_id == user_id)
        prof_res = await self.db.execute(prof_stmt)
        profile = prof_res.scalar_one_or_none()
        speaking_level = profile.speaking_level if profile else "Intermediate (N3-N2)"
        level_conf = profile.level_confidence if profile else "medium"
        total_sessions = profile.total_sessions_analyzed if profile else 0

        # 2. Game streak
        game_stmt = select(GameProfile).where(GameProfile.user_id == user_id)
        game_res = await self.db.execute(game_stmt)
        game_profile = game_res.scalar_one_or_none()
        streak = game_profile.current_streak if game_profile else 0

        # 3. Goals
        goals_stmt = select(LearningGoal).where(LearningGoal.user_id == user_id, LearningGoal.status == "active")
        goals_res = await self.db.execute(goals_stmt)
        goals = [g.title for g in list(goals_res.scalars().all())]

        # 4. Dashboard overview (metrics + bottleneck)
        overview = await self.snapshot_service.get_dashboard_overview(user_id, period="30d")

        metric_lines = []
        for k, mv in overview.metrics.items():
            if mv.sample_size > 0:
                change_str = f" ({mv.change:+0.1f})" if mv.change is not None else ""
                metric_lines.append(f"- {mv.metric_key.value}: {mv.value}{change_str} [{mv.trend.value}, conf:{mv.confidence.value}]")
        metrics_summary = "\n".join(metric_lines) if metric_lines else "Chưa có đủ dữ liệu 30 ngày."

        bottleneck_info = (
            f"{overview.bottleneck.candidate}: {overview.bottleneck.description}" if overview.bottleneck else "Phát triển đồng đều."
        )

        # 5. Memories with budget selection based on mode
        # For pitch mode, prioritize pitch-related memories; for keigo, keigo, etc.
        mem_query = (
            select(LearnerMemory)
            .where(LearnerMemory.user_id == user_id, LearnerMemory.status == "active")
            .order_by(desc(LearnerMemory.priority_score))
            .limit(10)
        )
        mem_res = await self.db.execute(mem_query)
        all_mems = list(mem_res.scalars().all())

        # Filter by mode relevance
        mode_keywords: dict[CoachMode, list[str]] = {
            CoachMode.REFLEX: ["reflex", "conjugation", "particle", "automaticity", "reaction"],
            CoachMode.KEIGO: ["keigo", "politeness", "uchi", "soto", "register", "sonkeigo", "kenjougo"],
            CoachMode.PITCH: ["pitch", "mora", "pronunciation", "accent", "intona"],
            CoachMode.SITUATIONAL: ["situational", "conversation", "recovery", "intent"],
            CoachMode.MONOLOGUE: ["fluency", "coherence", "filler", "discourse", "speech"],
            CoachMode.FREE_SPEAKING: ["grammar", "naturalness", "fluency", "pronunciation"],
        }
        keywords = mode_keywords.get(mode, [])
        relevant_mems = []
        if keywords and question:
            q_low = question.lower()
            # if question explicitly mentions はし or Uchi etc, include all
            relevant_mems = [m for m in all_mems if any(kw in (m.memory_key or "").lower() or kw in (m.statement or "").lower() for kw in keywords)] or all_mems[:5]
        else:
            relevant_mems = all_mems[:5]

        weak_lines = [f"- {m.statement} (lỗi {m.error_count} lần, trend:{m.trend})" for m in relevant_mems]
        recent_weaknesses = "\n".join(weak_lines) if weak_lines else "Không có lỗi nghiêm trọng lặp lại."

        # Strengths from LearningItem
        item_stmt = (
            select(LearningItem)
            .where(LearningItem.user_id == user_id, LearningItem.overall_mastery >= 0.75)
            .order_by(desc(LearningItem.overall_mastery))
            .limit(4)
        )
        item_res = await self.db.execute(item_stmt)
        items = list(item_res.scalars().all())
        strength_lines = [f"- Thành thạo: {it.title} ({int(it.overall_mastery*100)}%)" for it in items]
        recent_strengths = "\n".join(strength_lines) if strength_lines else "Đang tích luỹ dữ liệu điểm mạnh."

        # 6. Recent attempts — mode-filtered (Spec §7 example: はし in Mode3 should not fetch Mode4 history)
        # For FREE_SPEAKING, fetch recent conversation turns instead of exercise attempts (§41)
        recent_attempts = []
        recent_errors = []
        if mode == CoachMode.FREE_SPEAKING:
            # Fetch recent conversation sessions with turn counts for speaking room (§41)
            try:
                from app.domains.conversation.models import ConversationSession
                sess_stmt = (
                    select(ConversationSession)
                    .where(ConversationSession.user_id == user_id, ConversationSession.status == "completed")
                    .order_by(desc(ConversationSession.started_at))
                    .limit(5)
                )
                sess_res = await self.db.execute(sess_stmt)
                sessions = list(sess_res.scalars().all())
                recent_attempts = [
                    {
                        "session_id": s.id,
                        "mode": s.mode,
                        "turns": len(s.turns) if hasattr(s, "turns") and s.turns else 0,
                        "duration_seconds": s.duration_seconds,
                        "started_at": s.started_at.isoformat() if s.started_at else None,
                        "status": s.status,
                    }
                    for s in sessions
                ]
            except Exception:
                recent_attempts = []
        elif mode in (CoachMode.REFLEX, CoachMode.KEIGO, CoachMode.PITCH, CoachMode.SITUATIONAL, CoachMode.MONOLOGUE):
            prefix_map = {
                CoachMode.REFLEX: "reflex",
                CoachMode.KEIGO: "keigo",
                CoachMode.PITCH: "pitch",
                CoachMode.SITUATIONAL: "situational",
                CoachMode.MONOLOGUE: "speech",
            }
            prefix = prefix_map.get(mode)
            if prefix:
                att_stmt = (
                    select(ExerciseAttempt)
                    .where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.status == "completed")
                    .order_by(desc(ExerciseAttempt.completed_at))
                    .limit(10)
                )
                att_res = await self.db.execute(att_stmt)
                all_atts = list(att_res.scalars().all())
                # join load exercise type would need extra query; we approximate via metrics_json keys
                filtered = []
                for a in all_atts:
                    mj = a.metrics_json or {}
                    if prefix == "speech":
                        if a.exercise_id and "speech" in str(a.exercise_id):
                            filtered.append(a)
                        elif "speech" in mj or "monologue" in mj:
                            filtered.append(a)
                    else:
                        if prefix in mj or any(prefix in str(v) for v in mj.values() if isinstance(v, str)):
                            filtered.append(a)
                # fallback: if we filtered too aggressively, take last 5 directly from DB with exercise join
                if not filtered:
                    # try direct exercise type query
                    from sqlalchemy.orm import selectinload
                    j_stmt = (
                        select(ExerciseAttempt)
                        .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
                        .where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.status == "completed", Exercise.exercise_type.like(f"{prefix}%"))
                        .order_by(desc(ExerciseAttempt.completed_at))
                        .limit(8)
                    )
                    try:
                        j_res = await self.db.execute(j_stmt)
                        filtered = list(j_res.scalars().all())
                    except Exception:
                        filtered = all_atts[:5]
                recent_attempts = [
                    {
                        "exercise_id": a.exercise_id,
                        "success": a.success,
                        "score": a.score,
                        "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                        "feedback": a.feedback,
                        "metrics": a.metrics_json,
                    }
                    for a in filtered[:5]
                ]
                recent_errors = [a for a in recent_attempts if not a["success"]]

        # 6b. Detailed speaking evidence (TurnAnalysis, Pronunciation, SessionAnalysis) §36-41
        pronunciation_summary: dict[str, Any] = {}
        recent_corrections: list[dict[str, Any]] = []
        session_patterns: list[str] = []
        current_session_detail: dict[str, Any] | None = None
        try:
            # If free speaking or speaking route, pull TurnAnalysis top 3 MUST_FIX
            if mode in (CoachMode.FREE_SPEAKING, CoachMode.PROGRESS, CoachMode.DASHBOARD):
                from app.domains.conversation_intelligence.models import SessionAnalysis, TurnAnalysis
                # recent TurnAnalysis for last 5 completed sessions within 30d
                if recent_attempts:
                    sess_ids = [a.get("session_id") for a in recent_attempts if a.get("session_id")]
                    if sess_ids:
                        ta_stmt = (
                            select(TurnAnalysis)
                            .where(TurnAnalysis.session_id.in_(sess_ids))
                            .order_by(desc(TurnAnalysis.created_at))
                            .limit(10)
                        )
                        ta_res = await self.db.execute(ta_stmt)
                        tas = list(ta_res.scalars().all())
                        for ta in tas:
                            for c in (ta.corrections or [])[:2]:
                                recent_corrections.append({
                                    "session_id": ta.session_id,
                                    "original": getattr(c, "original", "")[:80] if hasattr(c, "original") else str(c)[:80],
                                    "corrected": getattr(c, "corrected", "")[:80] if hasattr(c, "corrected") else "",
                                    "category": getattr(c, "category", "unknown"),
                                    "severity": getattr(c, "severity", "unknown"),
                                })
                                if len(recent_corrections) >= 6:
                                    break
                # SessionAnalysis repeated patterns
                try:
                    from sqlalchemy import select as _select
                    sa_stmt = _select(SessionAnalysis).where(SessionAnalysis.user_id == user_id).order_by(desc(SessionAnalysis.created_at)).limit(3)
                    sa_res = await self.db.execute(sa_stmt)
                    sas = list(sa_res.scalars().all())
                    for sa in sas:
                        if getattr(sa, "repeated_patterns", None):
                            session_patterns.extend(sa.repeated_patterns[:3])
                except Exception:
                    pass
                # Pronunciation last 3 attempts (5 pillars)
                try:
                    from app.domains.pronunciation.models import PronunciationAttempt
                    pa_stmt = select(PronunciationAttempt).where(PronunciationAttempt.user_id == user_id, PronunciationAttempt.analysis_status == "completed").order_by(desc(PronunciationAttempt.created_at)).limit(3)
                    pa_res = await self.db.execute(pa_stmt)
                    pas = list(pa_res.scalars().all())
                    if pas:
                        # average overall + per-pillar
                        avg_overall = sum(p.overall_score for p in pas if p.overall_score) / len(pas) if pas else None
                        # pillar breakdown from last attempt
                        last = pas[0]
                        pronunciation_summary = {
                            "avg_overall": round(avg_overall, 1) if avg_overall else None,
                            "last_overall": last.overall_score,
                            "pillar": last.scores_json if hasattr(last, "scores_json") else {},
                            "attempts_count": len(pas),
                        }
                except Exception:
                    pass
            # current_session detail if provided — also enrich live corrections for active session §7
            if current_session_id:
                try:
                    from app.domains.conversation.models import ConversationSession
                    cs_stmt = select(ConversationSession).where(ConversationSession.id == current_session_id)
                    cs_res = await self.db.execute(cs_stmt)
                    cs = cs_res.scalar_one_or_none()
                    if cs:
                        current_session_detail = {
                            "id": cs.id,
                            "mode": cs.mode,
                            "status": cs.status,
                            "turns": len(cs.turns) if hasattr(cs, "turns") and cs.turns else 0,
                            "started_at": cs.started_at.isoformat() if cs.started_at else None,
                        }
                        # live: fetch TurnAnalysis for this active session even if not completed
                        from app.domains.conversation_intelligence.models import TurnAnalysis
                        live_ta_stmt = select(TurnAnalysis).where(TurnAnalysis.session_id == current_session_id).order_by(desc(TurnAnalysis.created_at)).limit(5)
                        live_ta_res = await self.db.execute(live_ta_stmt)
                        live_tas = list(live_ta_res.scalars().all())
                        for ta in live_tas:
                            for c in (ta.corrections or [])[:2]:
                                recent_corrections.append({
                                    "session_id": ta.session_id,
                                    "original": getattr(c, "original", "")[:80] if hasattr(c, "original") else str(c)[:80],
                                    "corrected": getattr(c, "corrected", "")[:80] if hasattr(c, "corrected") else "",
                                    "category": getattr(c, "category", "unknown"),
                                    "severity": getattr(c, "severity", "unknown"),
                                })
                                if len(recent_corrections) >= 6:
                                    break
                except Exception:
                    pass
        except Exception:
            pass

        # 7. Current exercise details
        current_exercise = None
        current_task = None
        current_scenario = None
        learning_targets: list[str] = []
        sub_mode: str | None = None
        if current_exercise_id:
            ex_stmt = select(Exercise).where(Exercise.id == current_exercise_id)
            ex_res = await self.db.execute(ex_stmt)
            ex = ex_res.scalar_one_or_none()
            if ex:
                current_exercise = ex
                sub_mode = ex.exercise_type
                current_task = ex.title
                current_scenario = ex.scenario
                learning_targets = ex.learning_item_keys or []

        # 8. Mastery snapshot per mode
        mastery_snapshot = {}
        automaticity_snapshot = {}
        # pull from items
        for it in items[:5]:
            mastery_snapshot[it.key] = {"mastery": it.overall_mastery, "lifecycle": it.lifecycle}
            if hasattr(it, "automaticity_mastery"):
                automaticity_snapshot[it.key] = float(getattr(it, "automaticity_mastery") or 0)

        # Also fetch all active items for distribution
        all_items_stmt = select(LearningItem).where(LearningItem.user_id == user_id, LearningItem.status == "active").limit(10)
        all_items_res = await self.db.execute(all_items_stmt)
        all_items = list(all_items_res.scalars().all())
        if not automaticity_snapshot and all_items:
            for it in all_items[:5]:
                if hasattr(it, "automaticity_mastery"):
                    automaticity_snapshot[it.key] = float(getattr(it, "automaticity_mastery") or 0)

        progress_summary = {
            "total_sessions": total_sessions,
            "streak": streak,
            "level": speaking_level,
            "bottleneck": bottleneck_info,
        }

        # capability flags
        available_actions = ["ask", "explain", "practice", "review", "plan"]
        if mode != CoachMode.UNKNOWN:
            available_actions.extend(["generate_exercise", "start_practice"])
        capability_flags = {
            "can_generate_exercise": True,
            "can_start_session": True,
            "can_view_progress": True,
            "is_exercise_context": bool(current_exercise_id),
        }

        hash_seed = f"{user_id}:{current_route}:{mode.value}:{total_sessions}:{bottleneck_info[:50]}:{len(relevant_mems)}:{current_exercise_id or ''}"
        ctx_hash = hashlib.sha256(hash_seed.encode()).hexdigest()[:16]

        ctx = CoachContext(
            user_id=user_id,
            current_route=current_route,
            current_mode=mode,
            current_sub_mode=sub_mode,
            current_exercise_id=current_exercise_id,
            current_session_id=current_session_id,
            current_learning_targets=learning_targets,
            current_task=current_task,
            current_scenario=current_scenario,
            recent_attempts=recent_attempts,
            recent_errors=recent_errors,
            mastery_snapshot=mastery_snapshot,
            automaticity_snapshot=automaticity_snapshot,
            progress_summary=progress_summary,
            active_recommendations=[],
            learner_goals=goals,
            learner_level=speaking_level,
            current_streak=streak,
            available_actions=available_actions,
            capability_flags=capability_flags,
            context_hash=ctx_hash,
            metrics_summary=metrics_summary,
            bottleneck_info=bottleneck_info,
            recent_weaknesses=recent_weaknesses,
            recent_strengths=recent_strengths,
            speaking_level=speaking_level,
            level_confidence=level_conf,
            total_sessions=total_sessions,
            dashboard_overview=overview,
            pronunciation_summary=pronunciation_summary,
            recent_corrections=recent_corrections,
            session_patterns=session_patterns,
            current_session_detail=current_session_detail,
        )
        # cache store
        _CONTEXT_CACHE[cache_key] = (now, ctx)
        # prune cache if too large
        if len(_CONTEXT_CACHE) > 200:
            oldest = min(_CONTEXT_CACHE, key=lambda k: _CONTEXT_CACHE[k][0])
            del _CONTEXT_CACHE[oldest]
        return ctx
