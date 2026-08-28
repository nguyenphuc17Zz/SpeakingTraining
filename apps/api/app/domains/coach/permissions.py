"""CoachPermissionPolicy §18-19."""

from __future__ import annotations

from enum import Enum

from app.domains.coach.contracts import CoachCapability


class ToolPermission(str, Enum):
    READ = "read"
    RECOMMEND = "recommend"
    GENERATE = "generate"
    EXECUTE = "execute"

# Map tool name → required permission level
TOOL_PERMISSIONS: dict[str, ToolPermission] = {
    # READ tools
    "get_profile": ToolPermission.READ,
    "get_mastery": ToolPermission.READ,
    "get_recent_attempts": ToolPermission.READ,
    "get_progress": ToolPermission.READ,
    "get_weaknesses": ToolPermission.READ,
    "get_strengths": ToolPermission.READ,
    "get_trends": ToolPermission.READ,
    "get_current_exercise": ToolPermission.READ,
    "get_current_session": ToolPermission.READ,
    "get_current_scenario": ToolPermission.READ,
    "get_reflex_progress": ToolPermission.READ,
    "get_keigo_progress": ToolPermission.READ,
    "get_pitch_progress": ToolPermission.READ,
    "get_situational_progress": ToolPermission.READ,
    "get_monologue_progress": ToolPermission.READ,
    "get_pronunciation_progress": ToolPermission.READ,
    "compare_attempts": ToolPermission.READ,
    "explain_result": ToolPermission.READ,
    # RECOMMEND
    "build_review_plan": ToolPermission.RECOMMEND,
    "build_practice_plan": ToolPermission.RECOMMEND,
    "recommend_next": ToolPermission.RECOMMEND,
    # GENERATE
    "generate_exercise": ToolPermission.GENERATE,
    "generate_speech": ToolPermission.GENERATE,
    "generate_roleplay": ToolPermission.GENERATE,
    "generate_pitch_practice": ToolPermission.GENERATE,
    "generate_keigo_practice": ToolPermission.GENERATE,
    "generate_reflex_practice": ToolPermission.GENERATE,
    # EXECUTE (validated session creation)
    "start_practice_session": ToolPermission.EXECUTE,
    "create_roleplay_session": ToolPermission.EXECUTE,
    "create_speech_session": ToolPermission.EXECUTE,
    "start_reflex_drill": ToolPermission.EXECUTE,
    "start_keigo_drill": ToolPermission.EXECUTE,
    "start_pitch_drill": ToolPermission.EXECUTE,
}

# Prohibited direct actions §19 — LLM must never be allowed to call these.
PROHIBITED_ACTIONS = frozenset({
    "modify_mastery",
    "award_xp",
    "delete_attempts",
    "change_scores",
    "edit_analytics",
    "change_user_profile",
    "change_subscription",
    "mutate_database",
    "update_mastery_direct",
    "update_xp_direct",
})

# Capability flags per context
CAPABILITY_MATRIX: dict[str, list[ToolPermission]] = {
    # default user can do READ + RECOMMEND; GENERATE/EXECUTE allowed but validated
    "default": [ToolPermission.READ, ToolPermission.RECOMMEND, ToolPermission.GENERATE, ToolPermission.EXECUTE],
    "anonymous": [ToolPermission.READ],
}


class CoachPermissionPolicy:
    """Validates tool calls before execution (§20)."""

    @staticmethod
    def is_allowed(tool_name: str) -> bool:
        if tool_name in PROHIBITED_ACTIONS:
            return False
        return tool_name in TOOL_PERMISSIONS

    @staticmethod
    def required_permission(tool_name: str) -> ToolPermission | None:
        return TOOL_PERMISSIONS.get(tool_name)

    @staticmethod
    def check(tool_name: str, requested: ToolPermission | None = None) -> tuple[bool, str]:
        if tool_name in PROHIBITED_ACTIONS:
            return False, f"Tool '{tool_name}' is prohibited — cannot directly mutate DB/state."
        if tool_name not in TOOL_PERMISSIONS:
            return False, f"Unknown tool '{tool_name}'."
        return True, "allowed"

    @staticmethod
    def filter_available_tools(allowed_permissions: list[ToolPermission]) -> list[str]:
        allowed_set = set(allowed_permissions)
        return [name for name, perm in TOOL_PERMISSIONS.items() if perm in allowed_set]
