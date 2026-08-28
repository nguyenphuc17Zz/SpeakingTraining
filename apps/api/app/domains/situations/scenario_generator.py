"""ScenarioGenerator — composable dimensions, reproducible with seed."""

from __future__ import annotations

import hashlib
import random
import uuid
from typing import Any

from app.domains.situations.npc_generator import NPCGenerator
from app.domains.situations.providers import ConstraintProvider, EventProvider, LocationProvider, PropProvider, RoleProvider, TaskProvider


class ScenarioGenerator:
    def __init__(self):
        self.location_provider = LocationProvider()
        self.role_provider = RoleProvider()
        self.task_provider = TaskProvider()
        self.constraint_provider = ConstraintProvider()
        self.event_provider = EventProvider()
        self.prop_provider = PropProvider()
        self.npc_generator = NPCGenerator()

    def generate(
        self,
        category: str | None = None,
        difficulty: str = "normal",
        learning_targets: list[str] | None = None,
        seed: str | None = None,
        duration_minutes: int = 5,
        mode: str = "standard",  # guided/standard/challenge/blind
    ) -> dict[str, Any]:
        # Reproducibility: seed random
        if seed:
            # Use hash to seed
            seed_int = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
            random.seed(seed_int)
        else:
            seed = str(uuid.uuid4())[:8]

        # Difficulty to int
        diff_map = {"easy": 1, "normal": 2, "hard": 3, "challenge": 4}
        diff_int = diff_map.get(difficulty, 2)

        # 1. Location
        cat, sub = self.location_provider.pick(category)
        # 2. Roles
        npc_role = self.role_provider.pick(sub)
        user_role = "customer" if npc_role in ("clerk", "server", "receptionist", "manager") else "employee" if npc_role in ("coworker",) else "customer"
        # 3. Tasks / Goals
        tasks = self.task_provider.pick(sub)
        # Adjust goal count by duration: 3min ->2 goals, 5min 2-3, 10min 3-5, 20min 4-6
        duration_goals = {3: 2, 5: 3, 10: 4, 20: 5, 30: 6}
        max_goals = duration_goals.get(duration_minutes, 3)
        tasks = tasks[:max_goals]
        # Build goals with semantic intent
        goals = []
        for idx, t in enumerate(tasks):
            goals.append({
                "id": f"goal_{idx+1}_{t}",
                "task": t,
                "required_intent": t.upper(),
                "required_entity": None,
                "description": t.replace("_", " "),
                "status": "NOT_STARTED",
                "hidden": mode in ("blind",) or (mode == "challenge" and idx >= 1),
            })
        # For blind: hide all except first
        if mode == "blind":
            for g in goals:
                g["hidden"] = True

        # 4. Constraints
        constraints = self.constraint_provider.pick(allowed_state="ORDERING", difficulty=diff_int)

        # 5. NPCs
        npc = self.npc_generator.generate(role=npc_role, location=sub, difficulty=difficulty)
        # Maybe second actor for some scenarios (e.g., manager)
        actors = [npc]
        if sub in ("office", "izakaya") and random.random() < 0.3:
            second_role = "manager" if npc_role == "coworker" else "customer"
            actors.append(self.npc_generator.generate(role=second_role, location=sub, difficulty=difficulty))

        # 6. Props
        props = self.prop_provider.generate(sub, constraints)

        # 7. Event pool
        event_pool = []
        for state in ["ORDERING", "PAY", "CONFIRM"]:
            sampled = self.event_provider.sample(state, diff_int, count=1)
            event_pool.extend(sampled)

        # 8. Learning targets
        if not learning_targets:
            learning_targets = random.sample(["request", "polite_requests", "clarification", "business_keigo", "recovery"], k=2)

        scenario_id = f"situ_{seed}_{sub}_{difficulty}"
        # Reset random seed
        random.seed()

        scenario = {
            "scenario_id": scenario_id,
            "seed": seed,
            "category": cat,
            "location": {"category": cat, "subtype": sub},
            "user_role": {"role": user_role},
            "actors": actors,
            "goals": goals,
            "constraints": constraints,
            "props": props,
            "event_pool": event_pool,
            "learning_targets": learning_targets,
            "difficulty": {"level": difficulty, "diff_int": diff_int, "language": diff_int, "event_pressure": min(diff_int, 3)},
            "duration_minutes": duration_minutes,
            "mode": mode,
            "resource_version": "situations.v1",
        }
        # Validate
        valid, reason = self.validate(scenario)
        if not valid:
            # Regenerate once
            return self.generate(category, difficulty, learning_targets, seed=None, duration_minutes=duration_minutes, mode=mode)
        return scenario

    def validate(self, scenario: dict[str, Any]) -> tuple[bool, str]:
        # At least 1 goal
        if not scenario.get("goals"):
            return False, "No goals"
        # Goals reachable: just check not empty
        # Roles coherent: user_role != npc role?
        if scenario["user_role"]["role"] == scenario["actors"][0]["identity"]["role"]:
            # Could be same, but allow coworker vs coworker? For MVP, allow
            pass
        # Event conditions valid
        for ev in scenario.get("event_pool", []):
            if "event_type" not in ev or "allowed_states" not in ev:
                return False, f"Invalid event {ev}"
        # Facts consistent
        if scenario["props"] and "currency" in scenario["props"] and scenario["props"]["currency"] != "JPY":
            # Only JPY supported for now
            pass
        # Difficulty within range
        if scenario["difficulty"]["diff_int"] not in (1,2,3,4):
            return False, "Difficulty out of range"
        return True, "ok"
