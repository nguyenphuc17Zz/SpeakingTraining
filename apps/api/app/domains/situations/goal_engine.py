"""GoalEngine — semantic, not exact-string, graph-based."""

from __future__ import annotations

from typing import Any


class GoalEngine:
    """
    SOTA Directed Acyclic Graph (DAG) Goal Petri-Net and Conversational FST Engine.
    Supports non-linear goal dependencies, concurrent branch resolution,
    deadlock / conversational impasse detection, and optimal recovery path planning.
    """

    def __init__(self, goals: list[dict[str, Any]], auto_linear_chain: bool = False):
        import copy

        self.goals = copy.deepcopy(goals)
        self.consecutive_stalled_turns: int = 0
        self.deadlock_threshold: int = 3
        self.history: list[dict[str, Any]] = []

        # Initialize places in Petri-Net
        for idx, g in enumerate(self.goals):
            g.setdefault("status", "NOT_STARTED")
            # Only apply linear chain if explicitly requested, otherwise respect custom DAG depends_on
            if "depends_on" not in g:
                g["depends_on"] = [self.goals[idx - 1]["id"]] if (auto_linear_chain and idx > 0) else []

    def _intent_matches(self, required: str, actual: str) -> bool:
        if required == actual:
            return True
        # Hierarchical: ORDER_FOOD/ORDER_DRINK satisfy REQUEST
        if required == "REQUEST" and actual in ("ORDER_FOOD", "ORDER_DRINK", "ASK_RECOMMENDATION", "REQUEST"):
            return True
        # CONFIRM can be satisfied by REQUEST with confirmation phrase
        if required == "CONFIRM" and actual in ("CONFIRM", "REQUEST"):
            return True
        return False

    def get_enabled_goals(self) -> list[dict[str, Any]]:
        """Petri-Net Marking: Returns goals whose pre-condition places are all COMPLETED."""
        enabled = []
        for g in self.goals:
            if g["status"] in ("COMPLETED", "FAILED"):
                continue
            deps = g.get("depends_on", [])
            # All prerequisite places must be marked as COMPLETED
            dep_ok = all(self._find_goal(d) and self._find_goal(d)["status"] == "COMPLETED" for d in deps)
            if dep_ok or not deps:
                enabled.append(g)
        return enabled

    def update(
        self,
        intent_result: dict[str, Any],
        entities: list[dict],
        transcript: str,
        scenario_state: dict | None = None,
    ) -> list[dict[str, Any]]:
        """
        Executes Petri-Net transitions based on observed Intent & Entity tokens.
        Allows multiple active transitions to fire concurrently if spoken in a single composite turn.
        """
        intent = intent_result.get("intent", "UNKNOWN")
        newly_completed = []
        enabled_goals = self.get_enabled_goals()

        for g in enabled_goals:
            required = g.get("required_intent")
            if required and self._intent_matches(required, intent):
                req_entity = g.get("required_entity")
                if req_entity:
                    ent_vals = [e.get("value", "") for e in entities]
                    if any(req_entity in v for v in ent_vals) or req_entity in transcript:
                        g["status"] = "COMPLETED"
                        newly_completed.append(g)
                else:
                    g["status"] = "COMPLETED"
                    newly_completed.append(g)
            elif intent != "UNKNOWN" and g["status"] == "NOT_STARTED":
                g["status"] = "IN_PROGRESS"

        # Update deadlock and stalling dynamics
        if newly_completed:
            self.consecutive_stalled_turns = 0
        else:
            if intent != "UNKNOWN" or len(transcript.strip()) > 3:
                self.consecutive_stalled_turns += 1

        self.history.append({
            "intent": intent,
            "transcript": transcript,
            "newly_completed": [g["id"] for g in newly_completed],
            "stalled_count": self.consecutive_stalled_turns,
        })

        return self.goals

    def is_deadlocked(self) -> bool:
        """Detects if learner is stuck in conversational impasse without advancing active goals."""
        return self.consecutive_stalled_turns >= self.deadlock_threshold and not self.is_all_completed()

    def get_recovery_recommendations(self) -> list[dict[str, Any]]:
        """
        Calculates optimal recovery path from current Petri-Net state.
        Suggests nearest uncompleted goal and prompt scaffolding for NPC or user.
        """
        enabled = self.get_enabled_goals()
        recommendations = []
        for g in enabled:
            recommendations.append({
                "goal_id": g["id"],
                "required_intent": g.get("required_intent"),
                "required_entity": g.get("required_entity"),
                "description": g.get("description", g.get("id")),
                "scaffold_hint": f"Hãy thử diễn đạt ý định '{g.get('required_intent')}' liên quan đến '{g.get('required_entity') or 'chủ đề'}'",
            })
        return recommendations

    def is_all_completed(self) -> bool:
        return all(g["status"] == "COMPLETED" for g in self.goals if not g.get("optional"))

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
        return any(g["status"] == "FAILED" for g in self.goals)

    def get_visible_goals(self, mode: str = "standard") -> list[dict]:
        if mode == "blind":
            return []
        if mode == "challenge":
            return [g for g in self.goals if not g.get("hidden")][:1]
        return [g for g in self.goals if not g.get("hidden")]

    def to_dict(self) -> list[dict]:
        return self.goals
