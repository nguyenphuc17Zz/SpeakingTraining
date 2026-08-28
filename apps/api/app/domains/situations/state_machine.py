"""ScenarioStateMachine — generic, works with any scenario template."""

from __future__ import annotations

from typing import Any


# Generic states
STATES = ["IDLE", "INTRO", "NPC_SPEAKING", "WAITING_FOR_USER", "USER_SPEAKING", "TRANSCRIBING", "RESOLVING_INTENT", "UPDATING_STATE", "GENERATING_RESPONSE", "SPEAKING_RESPONSE", "PAUSED", "COMPLETED", "FAILED"]

# Allowed transitions map
TRANSITIONS: dict[str, list[str]] = {
    "IDLE": ["INTRO"],
    "INTRO": ["NPC_SPEAKING"],
    "NPC_SPEAKING": ["WAITING_FOR_USER", "USER_SPEAKING", "PAUSED", "COMPLETED"],
    "WAITING_FOR_USER": ["USER_SPEAKING", "TRANSCRIBING", "PAUSED", "FAILED"],
    "USER_SPEAKING": ["TRANSCRIBING"],
    "TRANSCRIBING": ["RESOLVING_INTENT"],
    "RESOLVING_INTENT": ["UPDATING_STATE"],
    "UPDATING_STATE": ["GENERATING_RESPONSE", "COMPLETED", "FAILED"],
    "GENERATING_RESPONSE": ["SPEAKING_RESPONSE"],
    "SPEAKING_RESPONSE": ["WAITING_FOR_USER", "COMPLETED", "FAILED"],
    "PAUSED": ["WAITING_FOR_USER", "INTRO", "COMPLETED"],
    "COMPLETED": [],
    "FAILED": [],
}


class ScenarioStateMachine:
    def __init__(self, initial: str = "IDLE"):
        self.state = initial
        self.history: list[tuple[str, str, dict]] = []  # (from, to, context)

    def can_transition(self, target: str) -> bool:
        return target in TRANSITIONS.get(self.state, [])

    def transition(self, target: str, context: dict[str, Any] | None = None) -> bool:
        if not self.can_transition(target):
            return False
        self.history.append((self.state, target, context or {}))
        self.state = target
        return True

    def force(self, target: str):
        self.history.append((self.state, target, {"forced": True}))
        self.state = target

    def is_terminal(self) -> bool:
        return self.state in ("COMPLETED", "FAILED")

    @classmethod
    def check_reachability(cls, start: str, goals: list[dict[str, Any]]) -> bool:
        # Simple BFS to ensure COMPLETED reachable from start given transitions
        visited = set()
        queue = [start]
        while queue:
            cur = queue.pop(0)
            if cur == "COMPLETED":
                return True
            if cur in visited:
                continue
            visited.add(cur)
            for nxt in TRANSITIONS.get(cur, []):
                if nxt not in visited:
                    queue.append(nxt)
        return False
