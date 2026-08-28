"""Composable scenario dimension providers — small ontology, replaceable, not giant DB."""

from __future__ import annotations

import random
from typing import Any


class LocationProvider:
    CATEGORIES = {
        "food": ["izakaya", "convenience_store", "ramen_shop", "cafe"],
        "transportation": ["train_station", "taxi", "airport"],
        "retail": ["convenience_store", "pharmacy", "clothing_shop"],
        "healthcare": ["clinic", "pharmacy"],
        "workplace": ["office", "meeting_room"],
        "social": ["izakaya", "cafe"],
        "travel": ["hotel", "ryokan", "station"],
    }

    def pick(self, category: str | None = None) -> tuple[str, str]:
        if category and category in self.CATEGORIES:
            sub = random.choice(self.CATEGORIES[category])
            return category, sub
        cat = random.choice(list(self.CATEGORIES.keys()))
        sub = random.choice(self.CATEGORIES[cat])
        return cat, sub

    def list_categories(self) -> list[str]:
        return list(self.CATEGORIES.keys())


class RoleProvider:
    ROLES = ["customer", "clerk", "server", "manager", "receptionist", "taxi_driver", "interviewer", "coworker", "landlord", "doctor", "nurse", "teacher"]

    def pick(self, location: str | None = None) -> str:
        mapping = {
            "convenience_store": ["customer", "clerk"],
            "izakaya": ["customer", "server"],
            "train_station": ["customer", "clerk"],
            "clinic": ["customer", "receptionist"],
            "office": ["coworker", "manager"],
            "hotel": ["customer", "receptionist"],
        }
        if location and location in mapping:
            return random.choice(mapping[location])
        return random.choice(self.ROLES)


class TaskProvider:
    # Tasks map directly to IntentResolver intents (DECLINE_BAG/ORDER_FOOD/ORDER_DRINK/REQUEST/CONFIRM etc)
    TASKS = {
        "convenience_store": ["ORDER_FOOD", "DECLINE_BAG", "REQUEST"],
        "izakaya": ["ORDER_FOOD", "ORDER_DRINK", "ASK_RECOMMENDATION", "DECLINE_BAG"],
        "train_station": ["REQUEST", "CONFIRM", "ASK_RECOMMENDATION"],
        "clinic": ["REQUEST", "APOLOGIZE", "CONFIRM"],
        "office": ["REQUEST", "CONFIRM", "APOLOGIZE"],
        "hotel": ["REQUEST", "CONFIRM", "ASK_RECOMMENDATION"],
    }

    def pick(self, location: str | None = None) -> list[str]:
        if location and location in self.TASKS:
            base = self.TASKS[location]
            k = min(len(base), random.randint(2, 3))
            return random.sample(base, k)
        return random.sample(["ORDER_FOOD", "DECLINE_BAG", "REQUEST"], 2)


class ConstraintProvider:
    CONSTRAINTS = [
        {"type": "item_unavailable", "allowed_states": ["ORDERING"], "difficulty": 2},
        {"type": "wrong_order", "allowed_states": ["CONFIRM"], "difficulty": 2},
        {"type": "unexpected_fee", "allowed_states": ["PAY"], "difficulty": 3},
        {"type": "schedule_change", "allowed_states": ["SCHEDULE"], "difficulty": 3},
        {"type": "cannot_heat", "allowed_states": ["ORDERING"], "difficulty": 1},
        {"type": "allergy", "allowed_states": ["ORDERING"], "difficulty": 2},
    ]

    def pick(self, allowed_state: str | None = None, difficulty: int = 2) -> list[dict[str, Any]]:
        pool = [c for c in self.CONSTRAINTS if c["difficulty"] <= difficulty]
        if allowed_state:
            pool = [c for c in pool if allowed_state in c["allowed_states"]] or pool
        if not pool:
            return []
        # Return 0-1 constraint for beginner, 1-2 for advanced
        n = 1 if difficulty <= 2 else random.randint(1, 2)
        return random.sample(pool, min(n, len(pool)))


class EventProvider:
    EVENTS = [
        {"event_type": "ITEM_UNAVAILABLE", "allowed_states": ["ORDERING"], "difficulty": 2, "resolution_options": ["choose_alternative", "cancel_item", "ask_for_recommendation"]},
        {"event_type": "WRONG_ORDER", "allowed_states": ["CONFIRM"], "difficulty": 2, "resolution_options": ["point_out_error", "accept"]},
        {"event_type": "SCHEDULE_CHANGE", "allowed_states": ["SCHEDULE"], "difficulty": 3, "resolution_options": ["reschedule", "cancel"]},
        {"event_type": "NPC_CLARIFICATION", "allowed_states": ["REQUEST"], "difficulty": 1, "resolution_options": ["clarify", "repeat"]},
        {"event_type": "PHONE_RING", "allowed_states": ["DISCOVER"], "difficulty": 1, "resolution_options": ["wait", "ask_to_wait"]},
    ]

    def sample(self, state: str, difficulty: int, count: int = 1) -> list[dict[str, Any]]:
        pool = [e for e in self.EVENTS if state in e["allowed_states"] and e["difficulty"] <= difficulty]
        if not pool:
            pool = [e for e in self.EVENTS if e["difficulty"] <= difficulty]
        # Adaptive: beginner 0-1, advanced 2-3
        if difficulty <= 2:
            n = random.randint(0, 1)
        elif difficulty <= 3:
            n = random.randint(1, 2)
        else:
            n = random.randint(2, 3)
        n = min(n, count, len(pool))
        if n == 0:
            return []
        return random.sample(pool, n)


class PropProvider:
    PROPS = {
        "izakaya": {"type": "menu", "items": [{"name": "生ビール", "price": 580}, {"name": "枝豆", "price": 380}, {"name": "焼き鳥", "price": 680}], "currency": "JPY"},
        "convenience_store": {"type": "ticket_machine", "items": [{"name": "おにぎり", "price": 150}, {"name": "お茶", "price": 130}], "currency": "JPY"},
        "train_station": {"type": "train_map", "lines": ["山手線", "中央線"], "currency": "JPY"},
        "clinic": {"type": "form", "fields": ["symptom", "allergy", "medicine"], "currency": "JPY"},
    }

    def get(self, location: str) -> dict[str, Any] | None:
        return self.PROPS.get(location)

    def generate(self, location: str, constraints: list[dict]) -> dict[str, Any] | None:
        base = self.get(location)
        if not base:
            return None
        # Copy and maybe mark item unavailable if constraint
        import copy

        prop = copy.deepcopy(base)
        for c in constraints:
            if c["type"] == "item_unavailable" and "items" in prop:
                if prop["items"]:
                    # Mark random item as sold out
                    idx = random.randrange(len(prop["items"]))
                    prop["items"][idx]["available"] = False
        return prop
