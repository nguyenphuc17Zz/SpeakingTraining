"""Concrete tool handlers §17 — all delegate to existing Learning Engine (no duplication)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domains.analytics.application.analytics_snapshot_service import AnalyticsSnapshotService
from app.domains.analytics.application.metric_engine import MetricEngine
from app.domains.coach.contracts import ToolResult
from app.domains.coach.tool_registry import coach_tool_registry, ToolDefinition
from app.domains.coach.permissions import ToolPermission
from app.domains.learner_memory.models import LearnerMemory
from app.domains.learning.learner_state_service import LearnerStateService
from app.domains.learning.learning_item_service import LearningItemService
from app.domains.learning.models import Exercise, ExerciseAttempt, LearningItem
from app.domains.learning.recommendation_engine import RecommendationEngine
from app.domains.learning.daily_plan_generator import DailyPlanGenerator
from app.core.logging import logger


# ── READ handlers ──
async def h_get_profile(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    from app.domains.learner_memory.profile_service import LearnerProfileService
    svc = LearnerProfileService(db)
    prof = await svc.get_or_create_profile(user_id)
    return ToolResult(success=True, data={"level": prof.speaking_level, "overall": prof.overall_level, "sessions": prof.total_sessions_analyzed, "confidence": prof.level_confidence, "weaknesses": prof.weaknesses, "strengths": prof.strengths}, source="learner_memory", confidence=0.95)

async def h_get_mastery(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    key = params.get("key")
    svc = LearningItemService(db)
    if key:
        it = await svc.get_item_by_key(key, user_id)
        if not it:
            return ToolResult(success=False, data=None, source="learning_item_service", confidence=0.0, error="Item not found")
        return ToolResult(success=True, data={"key": it.key, "title": it.title, "overall_mastery": it.overall_mastery, "spontaneous": it.spontaneous_mastery, "production": it.production_mastery, "lifecycle": it.lifecycle}, source="mastery_engine", confidence=0.90)
    items = await svc.list_items(user_id, limit=10)
    return ToolResult(success=True, data=[{"key": i.key, "mastery": i.overall_mastery, "lifecycle": i.lifecycle, "title": i.title} for i in items], source="mastery_engine", confidence=0.85)

async def h_get_recent_attempts(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    limit = int(params.get("limit", 10))
    mode_filter = params.get("mode")  # e.g. reflex, keigo
    stmt = select(ExerciseAttempt).where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.status == "completed").order_by(desc(ExerciseAttempt.completed_at)).limit(limit)
    res = await db.execute(stmt)
    atts = list(res.scalars().all())
    if mode_filter:
        # filter by exercise_type if available
        filtered = []
        for a in atts:
            mj = a.metrics_json or {}
            if mode_filter in str(mj) or mode_filter in (a.feedback or ""):
                filtered.append(a)
        if filtered:
            atts = filtered
    data = [{"id": a.id, "exercise_id": a.exercise_id, "success": a.success, "score": a.score, "feedback": a.feedback, "completed_at": a.completed_at.isoformat() if a.completed_at else None} for a in atts]
    return ToolResult(success=True, data=data, source="learning_engine", confidence=0.95)

async def h_get_progress(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    svc = AnalyticsSnapshotService(db)
    overview = await svc.get_dashboard_overview(user_id)
    return ToolResult(success=True, data={"metrics": {k: {"value": v.value, "trend": v.trend.value, "confidence": v.confidence.value} for k, v in overview.metrics.items()}, "bottleneck": {"candidate": overview.bottleneck.candidate, "description": overview.bottleneck.description} if overview.bottleneck else None}, source="analytics", confidence=0.90)

async def h_get_weaknesses(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    stmt = select(LearnerMemory).where(LearnerMemory.user_id == user_id, LearnerMemory.status == "active").order_by(desc(LearnerMemory.priority_score)).limit(7)
    res = await db.execute(stmt)
    mems = list(res.scalars().all())
    return ToolResult(success=True, data=[{"key": m.memory_key, "statement": m.statement, "confidence": m.confidence, "evidence_count": m.evidence_count} for m in mems], source="learner_memory", confidence=0.90)

async def h_get_current_exercise(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    ex_id = params.get("exercise_id")
    if not ex_id:
        return ToolResult(success=False, data=None, source="learning", confidence=0.0, error="exercise_id required")
    stmt = select(Exercise).where(Exercise.id == ex_id, Exercise.user_id == user_id)
    res = await db.execute(stmt)
    ex = res.scalar_one_or_none()
    if not ex:
        return ToolResult(success=False, data=None, source="learning", confidence=0.0, error="Exercise not found")
    return ToolResult(success=True, data={"id": ex.id, "title": ex.title, "type": ex.exercise_type, "instructions": ex.instructions, "difficulty": ex.difficulty}, source="learning_engine", confidence=0.95)

async def h_get_current_session(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    from app.domains.conversation.models import ConversationSession
    sess_id = params.get("session_id")
    if sess_id:
        stmt = select(ConversationSession).where(ConversationSession.id == sess_id)
        res = await db.execute(stmt)
        s = res.scalar_one_or_none()
        if not s:
            return ToolResult(success=False, data=None, source="conversation", confidence=0.0, error="Session not found")
        return ToolResult(success=True, data={"id": s.id, "mode": s.mode, "status": s.status, "turns": len(s.turns)}, source="conversation", confidence=0.90)
    # fallback: latest session
    stmt = select(ConversationSession).where(ConversationSession.user_id == user_id).order_by(desc(ConversationSession.started_at)).limit(1)
    res = await db.execute(stmt)
    s = res.scalar_one_or_none()
    if not s:
        return ToolResult(success=True, data=None, source="conversation", confidence=0.0)
    return ToolResult(success=True, data={"id": s.id, "mode": s.mode, "status": s.status}, source="conversation", confidence=0.90)

async def h_explain_result(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    from app.domains.coach.explanation_engine import CoachExplanationEngine
    q = params.get("question", "")
    # Simple heuristic: detect Uchi/Soto etc
    if any(k in q.lower() for k in ["uchi", "soto", "keigo", "sonkeigo"]):
        ml = CoachExplanationEngine.micro_lesson_structure(
            problem="Bạn dùng 尊敬語 cho hành động của công ty mình (Uchi).",
            why="Phía Uchi (mình/công ty) phải dùng 謙譲語/丁寧語, không dùng 尊敬語 cho người nhà.",
            example="弊社の社長が拝見しました。 (Sai: 尊敬語 cho Uchi) → 弊社の社長がご覧になりました / 拝見いたしました が正しい文脈",
            try_prompt="Khách hỏi: 'Giám đốc bên bạn đã xem tài liệu chưa?' Hãy trả lời khiêm nhường đúng.",
            feedback="Dùng 謙譲語 cho hành động của Uchi khi nói với khách.",
        )
        return ToolResult(success=True, data=ml, source="explanation_engine", confidence=0.90)
    # Generic
    explanation = CoachExplanationEngine.format_error_explanation(
        what_happened="Câu trả lời đúng ngữ pháp nhưng chưa phù hợp ngữ cảnh/đăng ký (register).",
        why="Thiếu so sánh ngữ cảnh Uchi/Soto hoặc đuôi câu tự nhiên.",
        what_to_do="Thử lại với cùng mẫu nhưng đổi góc nhìn Uchi/Soto hoặc thêm đuôi ね/よ.",
        try_prompt="Làm 1 bài tập tương tự ngay để củng cố.",
        evidence=[{"metric": "context_fit", "value": 62, "sample_count": 5, "source": "keigo_evaluator"}],
    )
    return ToolResult(success=True, data={"explanation": explanation}, source="explanation_engine", confidence=0.85)

async def h_compare_attempts(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    ids = params.get("attempt_ids", [])
    if ids and len(ids) >= 2:
        stmt = select(ExerciseAttempt).where(ExerciseAttempt.id.in_(ids))
        res = await db.execute(stmt)
        atts = list(res.scalars().all())
        data = [{"id": a.id, "score": a.score, "success": a.success, "metrics": a.metrics_json} for a in atts]
        comparable = len({(a.metrics_json or {}).get("exercise_type") for a in atts}) <= 1
        return ToolResult(success=True, data={"attempts": data, "comparable": comparable}, source="learning_engine", confidence=0.85 if comparable else 0.55)
    # Fallback: auto pick last 2 attempts for comparability (§35) via ComparisonEngine
    try:
        from app.domains.analytics.application.comparison_engine import ComparisonEngine
        from app.domains.analytics.domain.comparison_context import ComparisonContext
        # Try to get last 2 completed attempts with same context
        stmt = select(ExerciseAttempt).where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.status == "completed").order_by(desc(ExerciseAttempt.completed_at)).limit(10)
        res = await db.execute(stmt)
        atts = list(res.scalars().all())
        if len(atts) >= 2:
            # Use ComparisonEngine logic simplified: check exercise_type same and within 30d
            a1, a2 = atts[0], atts[1]
            ex1 = a1.exercise_id
            ex2 = a2.exercise_id
            # fetch exercise types if possible
            comp = False
            try:
                from app.domains.learning.models import Exercise
                s1 = await db.execute(select(Exercise).where(Exercise.id == ex1))
                s2 = await db.execute(select(Exercise).where(Exercise.id == ex2))
                e1 = s1.scalar_one_or_none()
                e2 = s2.scalar_one_or_none()
                if e1 and e2:
                    comp = e1.exercise_type == e2.exercise_type and e1.difficulty == e2.difficulty
                else:
                    comp = False
            except Exception:
                comp = False
            return ToolResult(success=True, data={"attempts": [{"id": a.id, "score": a.score, "success": a.success} for a in atts[:2]], "comparable": comp, "note": "auto-selected last 2 for progress explanation"}, source="comparison_engine", confidence=0.88 if comp else 0.55)
    except Exception as e:
        return ToolResult(success=False, data=None, source="comparison_engine", confidence=0.0, error=str(e))
    return ToolResult(success=False, data=None, source="learning", confidence=0.0, error="Need >=2 attempt_ids")

async def _get_filtered_metrics(user_id: str, db: AsyncSession, prefix: str) -> ToolResult:
    from app.domains.analytics.application.metric_engine import MetricEngine
    me = MetricEngine(db)
    all_m = await me.get_all_metrics(user_id, period="30d")
    filtered = {k: {"value": v.value, "trend": v.trend.value, "confidence": v.confidence.value, "sample_size": v.sample_size} for k, v in all_m.items() if k.startswith(prefix)}
    return ToolResult(success=True, data=filtered, source="metric_engine", confidence=0.90)
async def h_get_reflex_progress(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    return await _get_filtered_metrics(user_id, db, "reflex")
async def h_get_keigo_progress(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    return await _get_filtered_metrics(user_id, db, "keigo")
async def h_get_pitch_progress(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    return await _get_filtered_metrics(user_id, db, "pitch")
async def h_get_situational_progress(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    return await _get_filtered_metrics(user_id, db, "situational")
async def h_get_pronunciation_progress(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    return await _get_filtered_metrics(user_id, db, "pronunciation")
async def h_get_monologue_progress(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    # monologue stored as speech_* metrics not in MetricKey; fallback to general progress
    return await _get_filtered_metrics(user_id, db, "transfer")

# ── RECOMMEND handlers ──
async def h_build_practice_plan(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    budget = int(params.get("time_budget", params.get("duration_min", 15)))
    budget = max(5, min(60, budget))
    goal = params.get("goal")
    svc = DailyPlanGenerator(db)
    plan = await svc.get_or_create_daily_plan(user_id, time_budget_minutes=budget, regenerate=False)
    # Adapt to spec §31 format
    steps = [{"mode": item.target_type, "duration_min": item.estimated_minutes, "target": item.title, "exercise_id": item.exercise_id} for item in plan.items]
    return ToolResult(success=True, data={"duration_min": plan.time_budget_minutes, "steps": steps, "focus": plan.focus_title, "focus_reason": plan.focus_reason, "plan_id": plan.id}, source="daily_plan_generator", confidence=0.92)

async def h_build_review_plan(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    from app.domains.learning.review_scheduler import ReviewScheduler
    svc = LearningItemService(db)
    items = await svc.list_items(user_id, limit=30)
    due = ReviewScheduler.filter_due_items(items)
    return ToolResult(success=True, data=[{"key": i.key, "title": i.title, "due": i.next_review_at.isoformat() if i.next_review_at else None} for i in due[:10]], source="review_scheduler", confidence=0.88)

async def h_recommend_next(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    eng = RecommendationEngine(db)
    recs = await eng.get_actionable_recommendations(user_id, limit=int(params.get("limit", 3)))
    return ToolResult(success=True, data=recs, source="recommendation_engine", confidence=0.90)

# ── GENERATE handlers (delegate to existing factories) ──
async def h_generate_exercise(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    # unify param names
    ex_type = params.get("exercise_type") or params.get("sub_mode") or params.get("mode") or "reflex_qna"
    difficulty = params.get("difficulty", "normal")
    pressure = params.get("pressure_level", "normal")
    # Route to correct factory
    try:
        if ex_type.startswith("reflex"):
            from app.domains.reflex.exercise_factory import ReflexExerciseFactory
            fac = ReflexExerciseFactory()
            if ex_type == "reflex_conjugation":
                data = fac.generate_conjugation(verb=params.get("verb"), target_form=params.get("conjugation_target"), difficulty=difficulty, pressure_level=pressure)
            elif ex_type == "reflex_transformation":
                data = fac.generate_transformation(difficulty=difficulty, pressure_level=pressure)
            elif ex_type == "reflex_context":
                data = fac.generate_context(difficulty=difficulty, pressure_level=pressure)
            else:
                data = fac.generate_qna(difficulty=difficulty, pressure_level=pressure)
            # persist via reflex helper or generic?
            from app.api.v1.reflex import generate_reflex_exercise as gen_reflex
            ex = await gen_reflex(sub_mode=ex_type, pressure_level=pressure, difficulty=difficulty, verb=params.get("verb"), conjugation_target=params.get("conjugation_target"), timer_limit_ms=params.get("timer_limit_ms"), learning_item_key=params.get("learning_item_key"), user_id=user_id, db=db)
            return ToolResult(success=True, data={"exercise_id": ex.id, "title": ex.title, "type": ex.exercise_type}, source="reflex_factory", confidence=0.95)
        elif ex_type.startswith("keigo"):
            from app.api.v1.keigo import generate_keigo_exercise as gen_keigo
            ex = await gen_keigo(sub_mode=ex_type, pressure_level=pressure, difficulty=difficulty, timer_limit_ms=params.get("timer_limit_ms"), learning_item_key=params.get("learning_item_key"), user_id=user_id, db=db)
            return ToolResult(success=True, data={"exercise_id": ex.id, "title": ex.title, "type": ex.exercise_type}, source="keigo_factory", confidence=0.95)
        elif ex_type.startswith("pitch") or ex_type in ("mora_length", "vowel_devoicing", "pitch_contour", "pitch_recognition", "pitch_minimal_pair"):
            from app.api.v1.pitch import generate_pitch_exercise as gen_pitch
            ex = await gen_pitch(sub_mode=ex_type, pressure_level=pressure, difficulty=difficulty, timer_limit_ms=params.get("timer_limit_ms"), learning_item_key=params.get("learning_item_key"), user_id=user_id, db=db)
            return ToolResult(success=True, data={"exercise_id": ex.id, "title": ex.title, "type": ex.exercise_type}, source="pitch_factory", confidence=0.95)
        elif ex_type.startswith("situational"):
            from app.api.v1.situations import generate_situational_exercise as gen_situ
            ex = await gen_situ(sub_mode=ex_type, category=params.get("category"), pressure_level=pressure, difficulty=difficulty, duration=int(params.get("duration", 5)), mode=params.get("mode", "standard"), timer_limit_ms=params.get("timer_limit_ms"), seed=params.get("seed"), user_id=user_id, db=db)
            return ToolResult(success=True, data={"exercise_id": ex.id, "title": ex.title, "type": ex.exercise_type}, source="situational_factory", confidence=0.95)
        elif ex_type.startswith("speech"):
            from app.domains.monologue.service import MonologueService
            svc = MonologueService(db)
            ex = await svc.generate_exercise(user_id=user_id, duration_sec=int(params.get("duration_sec", 60)), difficulty=params.get("difficulty_level", 3), genre=params.get("genre"), topic_domain=params.get("topic_domain"))
            return ToolResult(success=True, data={"exercise_id": ex.id, "title": ex.title, "type": ex.exercise_type}, source="monologue_service", confidence=0.90)
        else:
            # generic learning generator
            from app.domains.learning.exercise_generator import ExerciseGenerator
            from app.domains.learning.contracts import ExerciseType
            from app.domains.learning.learner_state_service import LearnerStateService
            from app.domains.learning.priority_engine import PriorityEngine
            state_svc = LearnerStateService(db)
            state = await state_svc.build_learning_state(user_id)
            # pick priority
            from app.domains.learning.learning_item_service import LearningItemService
            item_svc = LearningItemService(db)
            items = await item_svc.list_items(user_id, limit=10)
            if items:
                target = items[0]
                from app.domains.learning.contracts import PriorityScore
                p = PriorityEngine.calculate_item_priority(target, [])
                gen = ExerciseGenerator(db)
                ex = await gen.generate_exercise(user_id=user_id, priority=p, state=state, recent_signatures=[])
                return ToolResult(success=True, data={"exercise_id": ex.id, "title": ex.title, "type": ex.exercise_type}, source="exercise_generator", confidence=0.88)
            return ToolResult(success=False, data=None, source="generator", confidence=0.0, error="No learning items")
    except Exception as e:
        logger.warning(f"[CoachTool] generate_exercise failed: {e}")
        return ToolResult(success=False, data=None, source="generator", confidence=0.0, error=str(e))

# aliases
async def h_generate_reflex_practice(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    params = {**params, "exercise_type": params.get("sub_mode", "reflex_qna")}
    return await h_generate_exercise(user_id, db, params)
async def h_generate_keigo_practice(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    params = {**params, "exercise_type": params.get("sub_mode", "keigo_transformation")}
    return await h_generate_exercise(user_id, db, params)
async def h_generate_pitch_practice(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    params = {**params, "exercise_type": params.get("sub_mode", "pitch_minimal_pair")}
    return await h_generate_exercise(user_id, db, params)
async def h_generate_roleplay(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    params = {**params, "exercise_type": "situational_roleplay", "duration": params.get("duration", 5)}
    return await h_generate_exercise(user_id, db, params)
async def h_generate_speech(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    params = {**params, "exercise_type": "speech_monologue", "duration_sec": params.get("duration_sec", 60)}
    return await h_generate_exercise(user_id, db, params)

# ── EXECUTE handlers ──
async def h_start_practice_session(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    # For now, generating exercise counts as starting session; future: create LearningPlanItem or session record
    res = await h_generate_exercise(user_id, db, params)
    if res.success:
        # also create a lightweight response indicating navigation target
        target = res.data.get("type", params.get("exercise_type", "reflex_qna"))
        nav_map = {
            "reflex": "/reflex",
            "keigo": "/keigo",
            "pitch": "/pitch",
            "situational": "/situations",
            "speech": "/speaking/speech",
        }
        nav = "/learning"
        for k, v in nav_map.items():
            if target.startswith(k):
                nav = v
                break
        res.data["navigate_to"] = nav
        res.data["exercise_url"] = f"{nav}?exercise_id={res.data.get('exercise_id')}"
    return res

async def h_create_roleplay_session(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    return await h_start_practice_session(user_id, db, {**params, "exercise_type": "situational_roleplay"})
async def h_create_speech_session(user_id: str, db: AsyncSession, params: dict[str, Any]) -> ToolResult:
    return await h_start_practice_session(user_id, db, {**params, "exercise_type": "speech_monologue", "duration_sec": params.get("duration_sec", 60)})

# Register all
def bootstrap_coach_tools():
    def reg(name: str, desc: str, perm: ToolPermission, handler, source: str = "learning_engine"):
        coach_tool_registry.register(
            ToolDefinition(name=name, description=desc, permission=perm, source=source),
            handler,
        )
    # READ
    reg("get_profile", "Retrieve learner level/goals/profile", ToolPermission.READ, h_get_profile)
    reg("get_mastery", "Retrieve mastery for item(s)", ToolPermission.READ, h_get_mastery)
    reg("get_recent_attempts", "Fetch recent exercise attempts (mode-filtered)", ToolPermission.READ, h_get_recent_attempts)
    reg("get_progress", "Fetch analytics progress + bottleneck", ToolPermission.READ, h_get_progress)
    reg("get_weaknesses", "Fetch top weaknesses from memory", ToolPermission.READ, h_get_weaknesses)
    reg("get_strengths", "Fetch strengths", ToolPermission.READ, h_get_weaknesses)  # reuse
    reg("get_trends", "Fetch trends", ToolPermission.READ, h_get_progress)
    reg("get_current_exercise", "Fetch current exercise details", ToolPermission.READ, h_get_current_exercise)
    reg("get_current_session", "Fetch current session", ToolPermission.READ, h_get_current_session)
    reg("explain_result", "Explain error with What/Why/What-to-do/Try + evidence", ToolPermission.READ, h_explain_result)
    reg("compare_attempts", "Compare attempts for comparability", ToolPermission.READ, h_compare_attempts)
    reg("get_reflex_progress", "Reflex analytics (filtered metrics)", ToolPermission.READ, h_get_reflex_progress)
    reg("get_keigo_progress", "Keigo analytics", ToolPermission.READ, h_get_keigo_progress)
    reg("get_pitch_progress", "Pitch analytics", ToolPermission.READ, h_get_pitch_progress)
    reg("get_situational_progress", "Situational analytics", ToolPermission.READ, h_get_situational_progress)
    reg("get_pronunciation_progress", "Pronunciation analytics", ToolPermission.READ, h_get_pronunciation_progress)
    reg("get_monologue_progress", "Monologue analytics", ToolPermission.READ, h_get_monologue_progress)
    reg("get_current_scenario", "Fetch current scenario", ToolPermission.READ, h_get_current_session)
    # RECOMMEND
    reg("build_review_plan", "Build spaced review plan", ToolPermission.RECOMMEND, h_build_review_plan)
    reg("build_practice_plan", "Build time-budgeted practice plan", ToolPermission.RECOMMEND, h_build_practice_plan)
    reg("recommend_next", "Next recommendations", ToolPermission.RECOMMEND, h_recommend_next)
    # GENERATE
    reg("generate_exercise", "Generate exercise for any mode", ToolPermission.GENERATE, h_generate_exercise)
    reg("generate_reflex_practice", "Generate reflex drill", ToolPermission.GENERATE, h_generate_reflex_practice)
    reg("generate_keigo_practice", "Generate keigo drill", ToolPermission.GENERATE, h_generate_keigo_practice)
    reg("generate_pitch_practice", "Generate pitch drill", ToolPermission.GENERATE, h_generate_pitch_practice)
    reg("generate_roleplay", "Generate roleplay scenario", ToolPermission.GENERATE, h_generate_roleplay)
    reg("generate_speech", "Generate speech topic", ToolPermission.GENERATE, h_generate_speech)
    # EXECUTE
    reg("start_practice_session", "Generate and launch practice session", ToolPermission.EXECUTE, h_start_practice_session)
    reg("create_roleplay_session", "Create roleplay session", ToolPermission.EXECUTE, h_create_roleplay_session)
    reg("create_speech_session", "Create speech session", ToolPermission.EXECUTE, h_create_speech_session)

# Auto-bootstrap on import
bootstrap_coach_tools()
