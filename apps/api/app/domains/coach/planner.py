"""CoachPlanner — intent interpretation, tool selection, orchestration (§5, §20)."""

from __future__ import annotations

import json
import re
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.domains.coach.contracts import CoachContext, CoachIntent
from app.domains.coach.tool_registry import coach_tool_registry
from app.domains.coach.permissions import CoachPermissionPolicy


# Map intent → preferred tools
INTENT_TOOL_HINTS: dict[str, list[str]] = {
    "practice": ["get_weaknesses", "generate_exercise", "start_practice_session"],
    "plan": ["get_weaknesses", "get_mastery", "build_practice_plan"],
    "recommend": ["get_weaknesses", "build_practice_plan", "recommend_next"],
    "review": ["get_recent_attempts", "build_review_plan", "compare_attempts"],
    "analyze": ["get_progress", "get_recent_attempts", "compare_attempts"],
    "explain": ["get_current_exercise", "get_recent_attempts", "explain_result"],
    "teach": ["get_weaknesses", "generate_exercise"],
    "ask": ["get_profile", "get_progress"],
}


class CoachPlanner:
    """Plans tool calls based on intent + question + context."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def infer_intent(self, question: str) -> CoachIntent:
        q = question.lower()
        if re.search(r"(luyện|practice|drill|10 quick|cho tui|generate|tạo bài|speech|monologue|1-minute|1 phút|roleplay|situation|pitch|keigo|reflex|cho tui luyện)", q):
            return CoachIntent.PRACTICE
        if re.search(r"(plan|kế hoạch|make me a.*session|study session)", q):
            return CoachIntent.PLAN
        if re.search(r"(nên luyện gì|recommend|what should i practice)", q):
            return CoachIntent.RECOMMEND
        if re.search(r"(review|what mistakes|review my|ôn lại)", q):
            return CoachIntent.REVIEW
        if re.search(r"(why|tại sao|explain|giải thích|sao lại sai)", q):
            return CoachIntent.EXPLAIN
        if re.search(r"(teach|dạy|học|what is.*\?)", q):
            return CoachIntent.TEACH
        if re.search(r"(why.*score|why.*slow|analyze|phân tích)", q):
            return CoachIntent.ANALYZE
        if re.search(r"(motivate|động lực|cố lên)", q):
            return CoachIntent.MOTIVATE
        return CoachIntent.ASK

    def plan_tools(self, intent: CoachIntent, ctx: CoachContext, question: str) -> list[tuple[str, dict[str, Any]]]:
        """Returns ordered list of (tool_name, params) to execute."""
        plan: list[tuple[str, dict[str, Any]]] = []

        # Always include profile-level read if intent needs evidence
        if intent in (CoachIntent.ANALYZE, CoachIntent.RECOMMEND, CoachIntent.PLAN, CoachIntent.REVIEW):
            plan.append(("get_progress", {}))
            plan.append(("get_weaknesses", {}))

        if intent == CoachIntent.PRACTICE:
            # detect mode from question
            q_low = question.lower()
            if any(k in q_low for k in ("uchi", "soto", "keigo", "kính ngữ")):
                plan.append(("generate_keigo_practice", {"sub_mode": "keigo_transformation"}))
            elif any(k in q_low for k in ("pitch", "mora", "はし", "accent")):
                plan.append(("generate_pitch_practice", {"sub_mode": "pitch_minimal_pair"}))
            elif any(k in q_low for k in ("reflex", "conjugation", "phản xạ")):
                plan.append(("generate_reflex_practice", {"sub_mode": "reflex_conjugation"}))
            elif any(k in q_low for k in ("roleplay", "situation", "tình huống")):
                plan.append(("generate_roleplay", {}))
            elif any(k in q_low for k in ("speech", "1-minute", "1 phút")):
                plan.append(("generate_speech", {}))
            else:
                # use recent weakness to decide
                plan.append(("get_weaknesses", {}))
                plan.append(("generate_exercise", {}))
            # if execute requested
            if "luyện" in q_low or "practice now" in q_low or "start" in q_low:
                # will be handled as EXECUTE later
                pass

        if intent == CoachIntent.PLAN:
            # parse duration
            m = re.search(r"(\d+)\s*(phút|minute|min)", q_low := question.lower())
            budget = int(m.group(1)) if m else 15
            plan.append(("build_practice_plan", {"time_budget": budget}))

        if intent == CoachIntent.EXPLAIN and ctx.current_exercise_id:
            plan.append(("get_current_exercise", {"exercise_id": ctx.current_exercise_id}))

        if intent == CoachIntent.REVIEW:
            plan.append(("get_recent_attempts", {"limit": 10}))
            plan.append(("build_review_plan", {}))

        # For any score-down / progress question, ensure comparability check §34-35
        if re.search(r"(score.*down|điểm.*giảm|why.*score|tại sao.*điểm|score.*drop)", question.lower()):
            plan.append(("compare_attempts", {"attempt_ids": []}))  # placeholder — auto-select last 2 comparable
            plan.append(("get_progress", {}))

        # For TEACH, add micro-lesson generation via explain_result §29, §53
        if intent == CoachIntent.TEACH:
            plan.append(("explain_result", {"question": question}))
        seen = set()
        deduped: list[tuple[str, dict]] = []
        for name, params in plan:
            if name not in seen:
                seen.add(name)
                deduped.append((name, params))
        # filter by permission (all READ/RECOMMEND allowed by default)
        return [(n, p) for n, p in deduped if CoachPermissionPolicy.is_allowed(n)]

    async def execute_plan(self, plan: list[tuple[str, dict[str, Any]]], user_id: str) -> list[dict[str, Any]]:
        results = []
        for tool_name, params in plan:
            res = await coach_tool_registry.execute(tool_name, params, user_id, self.db)
            results.append({
                "tool": tool_name,
                "params": params,
                "success": res.success,
                "data": res.data,
                "source": res.source,
                "confidence": res.confidence,
                "error": res.error,
            })
            if not res.success:
                logger.warning(f"[CoachPlanner] tool {tool_name} failed: {res.error}")
        return results
