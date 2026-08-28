"""CoachContextBudget §8 — priority-based token budgeting."""
from __future__ import annotations

from typing import Any

# Priority order (§8)
BUDGET_PRIORITY = [
    "current_task",        # 1
    "direct_evidence",     # 2
    "recent_attempts",     # 3
    "relevant_mastery",    # 4
    "recent_trend",        # 5
    "long_term_context",   # 6
    "unrelated_history",   # 7
]

# Token budget defaults (approx chars/2.5 per token)
DEFAULT_BUDGET_TOKENS = 2000  # ~5000 chars
DEFAULT_SECTION_BUDGETS = {
    "current_task": 400,
    "direct_evidence": 600,
    "recent_attempts": 400,
    "relevant_mastery": 300,
    "recent_trend": 200,
    "long_term_context": 100,
    "unrelated_history": 0,  # never include
}

def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(len(text) / 2.5))

class CoachContextBudget:
    """Enforces token budget per priority level, prevents dumping full history."""

    def __init__(self, total_tokens: int = DEFAULT_BUDGET_TOKENS):
        self.total_tokens = total_tokens
        self.used_tokens = 0
        self.budget_map = dict(DEFAULT_SECTION_BUDGETS)

    def can_include(self, section: str, content: str) -> bool:
        if section not in self.budget_map:
            return False
        needed = _estimate_tokens(content)
        section_budget = self.budget_map[section]
        # check both section and total budget
        if needed > section_budget:
            return False
        if self.used_tokens + needed > self.total_tokens:
            return False
        return True

    def consume(self, section: str, content: str) -> str:
        """Returns truncated content if needed, updates used tokens."""
        if not content:
            return ""
        budget = self.budget_map.get(section, 0)
        if budget <= 0:
            return ""
        est = _estimate_tokens(content)
        if est <= budget and self.used_tokens + est <= self.total_tokens:
            self.used_tokens += est
            return content
        # truncate
        allowed_chars = int(budget * 2.5)
        remaining_total = int((self.total_tokens - self.used_tokens) * 2.5)
        allowed_chars = min(allowed_chars, remaining_total)
        if allowed_chars <= 50:
            return ""
        truncated = content[: allowed_chars - 20] + "…[truncated]"
        self.used_tokens = self.total_tokens  # mark as full
        return truncated

    def remaining(self) -> int:
        return max(0, self.total_tokens - self.used_tokens)

    @staticmethod
    def select_relevant_sections(current_route: str, intent: str) -> list[str]:
        """Selects which sections to include based on route/intent."""
        # Speaking pages get direct evidence + recent attempts
        if current_route.startswith("/speaking"):
            return ["current_task", "direct_evidence", "recent_attempts", "relevant_mastery", "recent_trend"]
        if current_route.startswith(("/reflex", "/keigo", "/pitch", "/situations")):
            return ["current_task", "direct_evidence", "recent_attempts", "relevant_mastery"]
        if current_route.startswith("/progress"):
            return ["current_task", "direct_evidence", "relevant_mastery", "recent_trend", "long_term_context"]
        if current_route.startswith("/learning"):
            return ["current_task", "direct_evidence", "relevant_mastery", "recent_trend"]
        return ["current_task", "direct_evidence", "relevant_mastery"]
