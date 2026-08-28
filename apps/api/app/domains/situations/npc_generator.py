"""NPCGenerator — small schema, dynamic per-session, consistent within session."""

from __future__ import annotations

import random
import uuid
from typing import Any


class NPCGenerator:
    def generate(
        self,
        role: str,
        location: str | None = None,
        difficulty: str = "normal",
        user_level: str = "N3",
    ) -> dict[str, Any]:
        # Difficulty affects complexity/speed
        speed_map = {"easy": 0.7, "normal": 0.85, "hard": 1.0, "challenge": 1.1}
        complexity_map = {"easy": "N5", "normal": "N4", "hard": "N3", "challenge": "N2"}
        # Random traits
        age_bands = ["young_adult", "middle_adult", "senior"]
        politeness = random.uniform(0.6, 0.95) if role in ("clerk", "server", "receptionist") else random.uniform(0.5, 0.85)
        patience = random.uniform(0.5, 0.9)
        directness = random.uniform(0.4, 0.8)
        helpfulness = random.uniform(0.5, 0.9)
        verbosity = random.uniform(0.3, 0.6)

        # Speech register based on role
        role_polite = {"clerk": "polite", "server": "polite", "receptionist": "polite", "manager": "polite", "doctor": "polite", "interviewer": "polite", "friend": "casual", "coworker": "polite"}
        register = role_polite.get(role, "polite")

        return {
            "identity": {
                "id": str(uuid.uuid4())[:8],
                "role": role,
                "name": f"{role}_{random.randint(1,99)}",  # generated, not hardcoded
                "age_band": random.choice(age_bands),
                "gender_presentation": random.choice(["neutral", "neutral"]),
            },
            "behavior": {
                "patience": round(patience, 2),
                "directness": round(directness, 2),
                "politeness": round(politeness, 2),
                "speech_speed": speed_map.get(difficulty, 0.85),
                "helpfulness": round(helpfulness, 2),
            },
            "speech": {
                "register": register,
                "complexity": complexity_map.get(difficulty, "N4") if difficulty in complexity_map else user_level,
                "verbosity": round(verbosity, 2),
            },
            "location": location,
        }
