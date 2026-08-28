"""CoachToolRegistry §17-21 — tool definitions and structured outputs."""
from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, Field

from app.domains.coach.contracts import ToolResult
from app.domains.coach.permissions import CoachPermissionPolicy, ToolPermission


class ToolDefinition(BaseModel):
    name: str
    description: str
    permission: ToolPermission
    params_schema: dict[str, Any] = Field(default_factory=dict)
    returns_schema: dict[str, Any] = Field(default_factory=dict)
    source: str = "learning_engine"


# Registry singleton
class CoachToolRegistry:
    """Central registry of Coach tools. Each tool must return ToolResult with source+confidence."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, Callable] = {}

    def register(self, definition: ToolDefinition, handler: Callable) -> None:
        self._tools[definition.name] = definition
        self._handlers[definition.name] = handler

    def list_tools(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def list_tool_names(self) -> list[str]:
        return list(self._tools.keys())

    def get_definition(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def is_registered(self, name: str) -> bool:
        return name in self._tools

    def describe_for_prompt(self) -> str:
        lines = []
        for t in self._tools.values():
            lines.append(f"- {t.name} ({t.permission.value}): {t.description}")
        return "\n".join(lines)

    async def execute(self, tool_name: str, params: dict[str, Any], user_id: str, db: Any) -> ToolResult:
        allowed, reason = CoachPermissionPolicy.check(tool_name)
        if not allowed:
            return ToolResult(success=False, data=None, source="permission_policy", confidence=1.0, error=reason)
        handler = self._handlers.get(tool_name)
        if not handler:
            return ToolResult(success=False, data=None, source="registry", confidence=1.0, error=f"Handler not found for tool '{tool_name}'")
        try:
            result = await handler(user_id=user_id, db=db, params=params)
            if isinstance(result, ToolResult):
                return result
            # normalize dict returns
            if isinstance(result, dict) and "success" in result:
                return ToolResult(**result)
            return ToolResult(success=True, data=result, source=tool_name, confidence=0.95)
        except Exception as e:
            return ToolResult(success=False, data=None, source=tool_name, confidence=0.0, error=str(e))


# Global registry instance — populated by bootstrap
coach_tool_registry = CoachToolRegistry()
