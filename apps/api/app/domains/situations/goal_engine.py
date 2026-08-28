"""GoalEngine — semantic, not exact-string, graph-based."""

from __future__ import annotations

from typing import Any


class GoalEngine:
    def __init__(self, goals: list[dict[str, Any]]):
        # Deep copy to avoid mutation of original
        import copy

        self.goals = copy.deepcopy(goals)
        # Build graph: for MVP, linear chain, but support dependencies
        for idx, g in enumerate(self.goals):
            g.setdefault("status", "NOT_STARTED")
            g.setdefault("depends_on", [self.goals[idx-1]["id"]] if idx > 0 else [])

    def _intent_matches(self, required: str, actual: str) -> bool:
        if required == actual:
            return True
        # Hierarchical: ORDER_FOOD/ORDER_DRINK satisfy REQUEST
        if required == "REQUEST" and actual in ("ORDER_FOOD", "ORDER_DRINK", "ASK_RECOMMENDATION", "REQUEST"):
            return True
        # CONFIRM can be satisfied by REQUEST with confirmation phrase
        if required == "CONFIRM" and actual in ("CONFIRM", "REQUEST"):
            return True
        # APOLOGIZE exact
        return False

    def update(self, intent_result: dict[str, Any], entities: list[dict], transcript: str, scenario_state: dict | None = None) -> list[dict[str, Any]]:
        intent = intent_result.get("intent")
        updated = []
        for g in self.goals:
            if g["status"] == "COMPLETED":
                continue
            # Check dependencies
            deps = g.get("depends_on", [])
            dep_ok = all(self._find_goal(d) and self._find_goal(d)["status"] == "COMPLETED" for d in deps)
            if deps and not dep_ok:
                # Allow REQUEST to be satisfied even if dependency not met if intent is REQUEST-like (for single-turn MVP)
                if not (g.get("required_intent") == "REQUEST" and self._intent_matches("REQUEST", intent)):
                    continue
            # Check intent match (with hierarchy)
            required = g.get("required_intent")
            if required and self._intent_matches(required, intent):
                req_entity = g.get("required_entity")
                if req_entity:
                    ent_vals = [e["value"] for e in entities]
                    if any(req_entity in v for v in ent_vals) or req_entity in transcript:
                        g["status"] = "COMPLETED"
                        updated.append(g)
                else:
                    g["status"] = "COMPLETED"
                    updated.append(g)
                    # For MVP single-turn, break after first completion to allow at least one
                    break
            elif intent != "UNKNOWN" and g["status"] == "NOT_STARTED":
                g["status"] = "IN_PROGRESS"
        return self.goals

    def _find_goal(self, goal_id: str) -> dict | None:
        for g in self.goals:
            if g["id"] == goal_id:
                return g
        return None

    def completion_rate(self) -> float:
        if not self.goals:
            return 0.0
        completed = sum(1 for g in self.goals if g["status"] == "COMPLETED")
        return completed / len(self.goals)

    def hidden_success_rate(self) -> float:
        hidden = [g for g in self.goals if g.get("hidden")]
        if not hidden:
            return 1.0
        completed = sum(1 for g in hidden if g["status"] == "COMPLETED")
        return completed / len(hidden)

    def is_failed(self) -> bool:
        # If any goal marked FAILED (not in MVP)
        return any(g["status"] == "FAILED" for g in self.goals)

    def get_visible_goals(self, mode: str = "standard") -> list[dict]:
        if mode == "blind":
            return []
        if mode == "challenge":
            # Only show first
            return [g for g in self.goals if not g.get("hidden")][:1]
        # standard/guided show all non-hidden
        return [g for g in self.goals if not g.get("hidden")]

    def to_dict(self) -> list[dict]:
        return self.goals
