"""ScenarioEventEngine — adaptive, not spam."""

from __future__ import annotations

import random
from typing import Any


class ScenarioEventEngine:
    def select_events(self, scenario: dict[str, Any], current_state: str, difficulty: str, turn_count: int) -> list[dict[str, Any]]:
        pool = scenario.get("event_pool", [])
        if not pool:
            return []
        # Difficulty to count
        diff_map = {"easy": (0, 1), "normal": (1, 2), "hard": (2, 3), "challenge": (2, 4)}
        min_e, max_e = diff_map.get(difficulty, (1, 2))
        # Count already injected
        injected = scenario.get("_injected_events", [])
        if len(injected) >= max_e:
            return []
        # Filter by allowed_states
        candidates = [e for e in pool if current_state in e.get("allowed_states", [])]
        if not candidates:
            candidates = [e for e in pool if e not in injected]
        if not candidates:
            return []
        # Probability: base * difficulty_modifier
        # For MVP, 30% chance per turn to inject
        if random.random() > 0.3:
            return []
        # Pick one
        ev = random.choice(candidates)
        # Cooldown: don't repeat same type quickly
        if any(x["event_type"] == ev["event_type"] for x in injected[-2:]):
            return []
        return [ev]

    def inject(self, scenario: dict[str, Any], event: dict[str, Any]):
        if "_injected_events" not in scenario:
            scenario["_injected_events"] = []
        scenario["_injected_events"].append(event)
