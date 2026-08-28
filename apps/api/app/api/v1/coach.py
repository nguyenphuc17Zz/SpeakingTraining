import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

import json
from fastapi.responses import StreamingResponse

from app.domains.ai.router import AIRouter
from app.domains.analytics.application.coach_service import CoachService
from app.domains.analytics.models import CoachConversation, CoachFeedback
from app.domains.analytics.schemas import (
    CoachAnswerDTO,
    CoachAskRequest,
    CoachFeedbackRequest,
    CoachQuickCardDTO,
    DailyBriefingDTO,
)
from app.domains.coach.coach_service import AICoachService
from app.domains.coach.tool_registry import coach_tool_registry
from app.domains.coach.proactive_engine import CoachProactiveTriggerEngine
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/coach", tags=["coach"])


class CoachChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    persona: str = Field(default="tanaka", description="tanaka | aoi | kenji")
    context_mode: str = Field(default="auto", description="auto | speaking | reflex | keigo | pitch | situational | monologue")
    current_route: str | None = None
    current_exercise_id: str | None = None
    current_session_id: str | None = None
    response_mode: str = Field(default="standard", description="brief | standard | detailed | teaching")
    action_mode: str | None = Field(default=None, description="execute to auto-create session")


class CoachActionRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    action_mode: str = Field(default="execute")
    current_route: str | None = None
    current_exercise_id: str | None = None
    current_session_id: str | None = None


class CoachPlanRequest(BaseModel):
    time_budget: int = Field(default=15, ge=5, le=60)
    goal: str | None = None
    current_route: str | None = None


async def get_user_id(db: AsyncSession = Depends(get_db)) -> str:
    """Resolve to real default user (UUID) for consistency with other learning routes."""
    from app.domains.users.service import UserService
    svc = UserService(db)
    user = await svc.get_or_create_default_user()
    return user.id


@router.post("/ask", response_model=CoachAnswerDTO)
async def ask_coach(
    req: CoachAskRequest,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    ai_router = AIRouter(db)
    coach_service = CoachService(db, ai_router)
    return await coach_service.answer(
        user_id=user_id,
        question=req.question,
        session_context_id=req.session_context_id,
    )


@router.get("/history")
async def get_coach_history(
    limit: int = Query(default=20),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(CoachConversation)
        .where(CoachConversation.user_id == user_id)
        .order_by(desc(CoachConversation.created_at))
        .limit(limit)
    )
    res = await db.execute(stmt)
    records = list(res.scalars().all())

    return [
        {
            "id": r.id,
            "question": r.question,
            "intent_type": r.intent_type,
            "answer": r.answer_text,
            "key_points": r.key_points_json or [],
            "evidence_refs": r.evidence_refs_json or [],
            "recommendations": r.recommendations_json or [],
            "confidence": r.confidence,
            "latency_ms": r.latency_ms,
            "created_at": r.created_at,
        }
        for r in records
    ]


@router.post("/feedback")
async def submit_coach_feedback(
    req: CoachFeedbackRequest,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    fb = CoachFeedback(
        id=str(uuid.uuid4()),
        conversation_id=req.conversation_id,
        user_id=user_id,
        rating=req.rating,
        feedback_text=req.feedback_text,
        requires_review=(req.rating == "incorrect"),
    )
    db.add(fb)
    await db.commit()
    return {"status": "ok", "id": fb.id}


@router.get("/briefing", response_model=DailyBriefingDTO)
async def get_daily_briefing(
    persona: str = Query(default="tanaka", description="tanaka | aoi | kenji"),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    ai_router = AIRouter(db)
    service = CoachService(db, ai_router)
    return await service.get_daily_briefing(user_id, persona=persona)


@router.get("/quick-cards", response_model=list[CoachQuickCardDTO])
async def get_quick_cards(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    service = CoachService(db)
    return await service.get_quick_cards(user_id)


# ── AI Coach Core — unified layer (§62) ──
@router.post("/chat")
async def coach_chat(
    req: CoachChatRequest,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = AICoachService(db, AIRouter(db))
    route = req.current_route or "/dashboard"
    # context_mode alias to route if provided
    if req.context_mode and req.context_mode != "auto" and not req.current_route:
        mode_route_map = {
            "speaking": "/speaking",
            "reflex": "/reflex",
            "keigo": "/keigo",
            "pitch": "/pitch",
            "situational": "/situations",
            "monologue": "/speaking/speech",
            "free": "/speaking",
            "review": "/profile",
            "progress": "/progress",
        }
        route = mode_route_map.get(req.context_mode, route)
    return await svc.chat(
        user_id=user_id,
        message=req.message,
        current_route=route,
        current_exercise_id=req.current_exercise_id,
        current_session_id=req.current_session_id,
        response_mode=req.response_mode,
        action_mode=req.action_mode,
        persona=req.persona,
    )


@router.post("/action")
async def coach_action(
    req: CoachActionRequest,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = AICoachService(db, AIRouter(db))
    route = req.current_route or "/dashboard"
    return await svc.chat(
        user_id=user_id,
        message=req.message,
        current_route=route,
        current_exercise_id=req.current_exercise_id,
        current_session_id=req.current_session_id,
        action_mode=req.action_mode or "execute",
    )


@router.get("/context")
async def get_coach_context(
    current_route: str = Query(default="/dashboard"),
    current_exercise_id: str | None = Query(default=None),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = AICoachService(db)
    ctx = await svc.get_context(user_id, current_route, current_exercise_id)
    return {
        "user_id": ctx.user_id,
        "current_route": ctx.current_route,
        "current_mode": ctx.current_mode.value,
        "current_sub_mode": ctx.current_sub_mode,
        "current_exercise_id": ctx.current_exercise_id,
        "current_task": ctx.current_task,
        "current_scenario": (ctx.current_scenario or "")[:500],
        "learner_level": ctx.learner_level,
        "current_streak": ctx.current_streak,
        "bottleneck_info": ctx.bottleneck_info,
        "recent_weaknesses": ctx.recent_weaknesses,
        "recent_strengths": ctx.recent_strengths,
        "available_actions": ctx.available_actions,
        "capability_flags": ctx.capability_flags,
        "context_hash": ctx.context_hash,
        "recent_attempts": ctx.recent_attempts[:3],
    }


@router.get("/insights")
async def get_coach_insights(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = AICoachService(db)
    return await svc.get_insights(user_id)


@router.get("/memory")
async def get_coach_memory(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = AICoachService(db)
    return await svc.get_memory(user_id)


@router.post("/plan")
async def create_coach_plan(
    req: CoachPlanRequest,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    svc = AICoachService(db)
    # delegate to tool
    from app.domains.coach.tool_registry import coach_tool_registry
    res = await coach_tool_registry.execute("build_practice_plan", {"time_budget": req.time_budget, "goal": req.goal}, user_id, db)
    if res.success:
        return res.data
    return {"error": res.error}


@router.get("/tools")
async def list_coach_tools(
    user_id: str = Depends(get_user_id),
):
    return [
        {"name": t.name, "description": t.description, "permission": t.permission.value, "source": t.source}
        for t in coach_tool_registry.list_tools()
    ]


@router.get("/proactive")
async def get_proactive_insights(
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    engine = CoachProactiveTriggerEngine(db)
    insights = await engine.evaluate_for_user(user_id)
    return insights


@router.get("/quick-actions")
async def get_quick_actions(
    current_route: str = Query(default="/dashboard"),
    current_exercise_id: str | None = Query(default=None),
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Contextual quick actions §14 — generated from current context, not hard-coded."""
    svc = AICoachService(db)
    ctx = await svc.get_context(user_id, current_route, current_exercise_id)
    mode = ctx.current_mode.value
    actions: list[dict[str, Any]] = []
    if mode == "reflex":
        actions = [
            {"label": "Explain Mistake", "prompt": "Why was my last answer wrong?", "intent": "explain"},
            {"label": "Train Weak Form", "prompt": "Give me 10 quick conjugation drills for my weak form", "intent": "practice", "action": "start_practice_session"},
            {"label": "Why Was I Slow?", "prompt": "Why am I slow in reflex?", "intent": "analyze"},
            {"label": "Practice Similar", "prompt": "Give me similar reflex exercises", "intent": "practice"},
        ]
    elif mode == "keigo":
        actions = [
            {"label": "Why Is This Keigo Wrong?", "prompt": "Why was my keigo wrong? Explain Uchi/Soto.", "intent": "explain"},
            {"label": "Show Natural Alternative", "prompt": "Show a more natural alternative for my last keigo answer", "intent": "teach"},
            {"label": "Practice Same Pattern", "prompt": "Give me keigo practice on the same pattern", "intent": "practice"},
            {"label": "Explain Uchi/Soto", "prompt": "Teach me Uchi/Soto", "intent": "teach"},
        ]
    elif mode == "pitch":
        actions = [
            {"label": "Why Is My Pitch Wrong?", "prompt": "Why is my pitch wrong for はし?", "intent": "explain"},
            {"label": "Show Pattern", "prompt": "Show the correct pitch pattern and contrast with my attempt", "intent": "teach"},
            {"label": "Retry Slowly", "prompt": "Give me a slow reference retry for this pitch", "intent": "practice"},
            {"label": "Practice Contrast", "prompt": "Give me minimal pair contrast drills", "intent": "practice"},
        ]
    elif mode == "situational":
        actions = [
            {"label": "Why Did I Fail?", "prompt": "Why did I fail the last situational task?", "intent": "explain"},
            {"label": "Replay Turn", "prompt": "Replay my last turn with feedback", "intent": "analyze"},
            {"label": "Try Again", "prompt": "Let me try the same situation again", "intent": "practice"},
            {"label": "Practice Recovery", "prompt": "Give me a recovery-focused roleplay", "intent": "practice"},
        ]
    elif mode == "monologue":
        actions = [
            {"label": "Why Did I Lose Fluency?", "prompt": "Why did my fluency drop after 45 seconds?", "intent": "analyze"},
            {"label": "Improve Structure", "prompt": "Help me improve my speech structure", "intent": "teach"},
            {"label": "Reduce Fillers", "prompt": "Help me reduce filler usage", "intent": "teach"},
            {"label": "Rewrite My Speech", "prompt": "Rewrite my last speech more naturally", "intent": "teach"},
            {"label": "Give Another Topic", "prompt": "Give me another 1-minute speech topic", "intent": "practice"},
        ]
    elif mode == "free_speaking":
        actions = [
            {"label": "What Should I Practice?", "prompt": "What should I practice next based on my recent speaking?", "intent": "recommend"},
            {"label": "Why Was I Not Natural?", "prompt": "Why did my last responses sound unnatural?", "intent": "analyze"},
            {"label": "Teach Me Natural Phrases", "prompt": "Teach me more natural alternatives for my last conversation", "intent": "teach"},
        ]
    else:
        actions = [
            {"label": "What Should I Practice Today?", "prompt": "What should I practice today?", "intent": "recommend"},
            {"label": "Explain My Weaknesses", "prompt": "Explain my weaknesses this week", "intent": "analyze"},
            {"label": "Make Study Plan", "prompt": "Make me a 15-minute Japanese practice plan", "intent": "plan"},
            {"label": "Review Last Sessions", "prompt": "Review my last five sessions", "intent": "review"},
        ]
    # Attach available_actions gating
    return {"mode": mode, "route": current_route, "actions": actions, "available_actions": ctx.available_actions}


@router.post("/chat/stream")
async def coach_chat_stream(
    req: CoachChatRequest,
    user_id: str = Depends(get_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Streaming Coach response (§15) — SSE with TEXT_DELTA then final JSON."""
    import asyncio
    from app.domains.ai.contracts import AIMessage, AIMessageRole, AIRequest, AITask, ResponseFormat, ResponseFormatType
    from app.domains.coach.contracts import CoachIntent
    from app.domains.coach.coach_service import AICoachService

    # For execute actions, return single JSON via streaming wrapper
    if req.action_mode == "execute":
        svc = AICoachService(db, AIRouter(db))
        route = req.current_route or "/dashboard"
        if req.context_mode and req.context_mode != "auto" and not req.current_route:
            mp = {"speaking": "/speaking", "reflex": "/reflex", "keigo": "/keigo", "pitch": "/pitch", "situational": "/situations", "monologue": "/speaking/speech"}
            route = mp.get(req.context_mode, route)
        result = await svc.chat(user_id=user_id, message=req.message, current_route=route, current_exercise_id=req.current_exercise_id, current_session_id=req.current_session_id, response_mode=req.response_mode, action_mode=req.action_mode)
        async def gen_once():
            yield f"data: {json.dumps({'type': 'final', 'data': result}, ensure_ascii=False)}\n\n"
        return StreamingResponse(gen_once(), media_type="text/event-stream")

    # Normal streaming path
    svc = AICoachService(db, AIRouter(db))
    route = req.current_route or "/dashboard"
    if req.context_mode and req.context_mode != "auto" and not req.current_route:
        mp = {"speaking": "/speaking", "reflex": "/reflex", "keigo": "/keigo", "pitch": "/pitch", "situational": "/situations", "monologue": "/speaking/speech"}
        route = mp.get(req.context_mode, route)

    # Use internal resolver + planner to build prompt, then stream
    from app.domains.coach.prompt_builder import CoachPromptBuilder
    ctx = await svc.resolver.resolve(user_id, route, req.current_exercise_id, req.current_session_id, req.message)
    intent = svc.planner.infer_intent(req.message)
    tool_plan = svc.planner.plan_tools(intent, ctx, req.message)
    tool_results = await svc.planner.execute_plan(tool_plan, user_id)

    # Map intent to task for cost control
    from app.domains.ai.contracts import AITask
    from app.domains.coach.contracts import CoachIntent as CIntent
    task_map = {CIntent.EXPLAIN: AITask.COACH_EXPLANATION, CIntent.TEACH: AITask.COACH_EXPLANATION, CIntent.ANALYZE: AITask.COACH_INSIGHT, CIntent.PLAN: AITask.COACH_PLAN, CIntent.RECOMMEND: AITask.COACH_PLAN}
    ai_task = task_map.get(intent, AITask.COACH_CHAT if intent in (CIntent.ASK, CIntent.GENERAL, CIntent.MOTIVATE, CIntent.PRACTICE) else AITask.COACH)

    pb = CoachPromptBuilder()
    system, user_content = pb.build(ctx, req.message, coach_tool_registry.describe_for_prompt())
    ai_router = AIRouter(db)
    ai_req = AIRequest(task=ai_task, messages=[AIMessage(role=AIMessageRole.USER, content=user_content)], system_instruction=system, temperature=0.3, response_format=ResponseFormat(type=ResponseFormatType.JSON_OBJECT))

    async def event_gen():
        full_text = ""
        try:
            async for event in ai_router.stream(task=ai_task, request=ai_req, user_id=user_id):
                if event.type.value == "text_delta" and event.text_delta:
                    full_text += event.text_delta
                    yield f"data: {json.dumps({'type': 'delta', 'text': event.text_delta}, ensure_ascii=False)}\n\n"
                elif event.type.value == "completed":
                    # Try parse final JSON
                    parsed = svc._parse_ai_json(full_text)
                    yield f"data: {json.dumps({'type': 'final', 'data': parsed, 'tool_calls': tool_results, 'context_hash': ctx.context_hash}, ensure_ascii=False)}\n\n"
                    # persist
                    try:
                        await svc._persist(user_id, req.message, intent.value, parsed.get('response') or parsed.get('answer') or full_text, parsed, ctx.context_hash, 0)
                    except Exception:
                        pass
                    break
                elif event.type.value == "error":
                    yield f"data: {json.dumps({'type': 'error', 'error': event.error}, ensure_ascii=False)}\n\n"
                    break
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
