"""CoachActionExecutor §30-32, §45 — validated execution, practice orchestration."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.coach.contracts import CoachContext
from app.domains.coach.tool_registry import coach_tool_registry
from app.domains.coach.permissions import CoachPermissionPolicy


class CoachActionExecutor:
    """Orchestrates generation → session launch per §30."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute(self, tool_name: str, params: dict[str, Any], user_id: str) -> dict[str, Any]:
        allowed, reason = CoachPermissionPolicy.check(tool_name)
        if not allowed:
            return {"success": False, "error": reason, "tool": tool_name}
        # Validate supported mode/configuration
        # e.g., for generate, check exercise_type is known
        if tool_name.startswith("generate") or tool_name == "start_practice_session":
            ex_type = params.get("exercise_type") or params.get("sub_mode") or ""
            # basic whitelist from ExerciseType
            from app.domains.learning.contracts import ExerciseType
            valid = {e.value for e in ExerciseType}
            # also allow reflex/keigo/pitch situational speech aliases
            if ex_type and ex_type not in valid and not any(ex_type.startswith(p) for p in ("reflex_", "keigo_", "pitch_", "situational", "speech")):
                return {"success": False, "error": f"Unsupported exercise_type '{ex_type}'", "tool": tool_name}

        result = await coach_tool_registry.execute(tool_name, params, user_id, self.db)
        if result.success:
            return {"success": True, "data": result.data, "source": result.source, "confidence": result.confidence}
        return {"success": False, "error": result.error, "source": result.source}

    async def orchestrate_practice(self, ctx: CoachContext, weakness_hint: str | None, duration_min: int = 5) -> dict[str, Any]:
        """§30: identify weakness → select mode → generate session → launch."""
        weakness = (weakness_hint or "").lower()
        target_mode = "reflex_qna"
        if any(k in weakness for k in ("uchi", "soto", "keigo", "sonkeigo", "kenjou")):
            target_mode = "keigo_transformation"
        elif any(k in weakness for k in ("pitch", "mora", "downstep", "accent", "はし")):
            target_mode = "pitch_minimal_pair"
        elif any(k in weakness for k in ("conj", "causative", "passive", "retrieval", "latency", "reflex")):
            target_mode = "reflex_conjugation"
        elif any(k in weakness for k in ("roleplay", "scenario", "recovery", "task")):
            target_mode = "situational_roleplay"
        elif any(k in weakness for k in ("fluency", "coherence", "filler", "speech", "discourse")):
            target_mode = "speech_monologue"

        # Action preview §46
        preview = {"starting": f"{target_mode} — {duration_min} min", "mode": target_mode, "duration": duration_min}

        res = await self.execute("start_practice_session", {"exercise_type": target_mode}, ctx.user_id)
        if res.get("success"):
            res["preview"] = preview
        return res
