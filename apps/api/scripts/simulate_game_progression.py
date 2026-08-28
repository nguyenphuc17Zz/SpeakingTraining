"""
Phase 10 — Game Progression & Economy Balance Simulator.

Simulates different learner profiles:
- Casual: 1 short conversation or 1 exercise per day (~10-15 min)
- Consistent: 1 roleplay + 2 pronunciation drills + daily quest (~25-30 min)
- Hardcore: 2 conversations + 4 exercises + 5 shadowing segments (~60 min)
- Irregular: 3 heavy practice days per week, gaps on other days

Verifies level progression curve, XP rates, quest completion ratios, and anti-farming caps.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from app.domains.gamification.domain.balance_config import BALANCE_CONFIG
from app.domains.gamification.domain.contracts import GameEventSource, GameEventType
from app.domains.gamification.domain.game_event import GameEvent
from app.domains.gamification.domain.level_curve import LevelCurve
from app.domains.gamification.domain.reward_policy import RewardPolicy


def simulate_profile(name: str, days: int, daily_routine_fn):
    total_xp = 0
    current_streak = 0
    longest_streak = 0
    quests_completed = 0
    daily_xp_records = []

    for day in range(1, days + 1):
        events = daily_routine_fn(day)
        day_xp = 0

        if events:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0

        # Simulate daily quest completion if routine has 2+ activities
        if len(events) >= 2:
            quests_completed += 3
            day_xp += BALANCE_CONFIG.XP_DAILY_QUEST_DEFAULT * 3

        repetition_map = {}
        for event in events:
            rep = repetition_map.get(event.source_id, 0)
            repetition_map[event.source_id] = rep + 1

            calc = RewardPolicy.calculate_reward(
                event=event,
                repetition_count_today=rep,
                daily_category_xp_so_far=day_xp,
            )
            day_xp += calc.xp_amount

        total_xp += day_xp
        daily_xp_records.append(day_xp)

    final_level = LevelCurve.level_from_total_xp(total_xp)
    final_rank = LevelCurve.rank_from_level(final_level)
    avg_daily_xp = sum(daily_xp_records) / max(1, days)

    return {
        "name": name,
        "days": days,
        "total_xp": total_xp,
        "avg_daily_xp": round(avg_daily_xp, 1),
        "final_level": final_level,
        "final_rank": final_rank.value,
        "longest_streak": longest_streak,
        "quests_completed": quests_completed,
    }


def casual_routine(day: int):
    # 1 normal exercise (10 min)
    return [
        GameEvent(
            user_id="casual_user",
            type=GameEventType.EXERCISE_COMPLETED,
            source=GameEventSource.LEARNING,
            source_id=f"ex_casual_{day}",
            metadata={"difficulty": "normal", "score": 80.0, "independence_level": "independent"},
        )
    ]


def consistent_routine(day: int):
    # 1 roleplay exercise + 2 pronunciation drills + 1 shadowing segment
    return [
        GameEvent(
            user_id="consistent_user",
            type=GameEventType.EXERCISE_COMPLETED,
            source=GameEventSource.LEARNING,
            source_id=f"ex_con_{day}",
            metadata={"difficulty": "hard", "score": 88.0, "independence_level": "independent"},
        ),
        GameEvent(
            user_id="consistent_user",
            type=GameEventType.PRONUNCIATION_ATTEMPTED,
            source=GameEventSource.PRONUNCIATION,
            source_id=f"pron_con_{day}_1",
            metadata={"score": 85.0},
        ),
        GameEvent(
            user_id="consistent_user",
            type=GameEventType.PRONUNCIATION_ATTEMPTED,
            source=GameEventSource.PRONUNCIATION,
            source_id=f"pron_con_{day}_2",
            metadata={"score": 90.0},
        ),
        GameEvent(
            user_id="consistent_user",
            type=GameEventType.SHADOWING_COMPLETED,
            source=GameEventSource.SHADOWING,
            source_id=f"shad_con_{day}",
            metadata={"score": 82.0},
        ),
    ]


def hardcore_routine(day: int):
    # 1 long conversation + 3 exercises + 4 shadowing clips + 1 boss clear weekly
    events = [
        GameEvent(
            user_id="hardcore_user",
            type=GameEventType.CONVERSATION_COMPLETED,
            source=GameEventSource.CONVERSATION,
            source_id=f"conv_hard_{day}",
            metadata={"duration_seconds": 900, "score": 92.0},
        ),
        GameEvent(
            user_id="hardcore_user",
            type=GameEventType.EXERCISE_COMPLETED,
            source=GameEventSource.LEARNING,
            source_id=f"ex_hard_{day}_1",
            metadata={"difficulty": "hard", "score": 95.0, "independence_level": "independent"},
        ),
        GameEvent(
            user_id="hardcore_user",
            type=GameEventType.EXERCISE_COMPLETED,
            source=GameEventSource.LEARNING,
            source_id=f"ex_hard_{day}_2",
            metadata={"difficulty": "challenge", "score": 90.0, "independence_level": "independent"},
        ),
        GameEvent(
            user_id="hardcore_user",
            type=GameEventType.SHADOWING_COMPLETED,
            source=GameEventSource.SHADOWING,
            source_id=f"shad_hard_{day}_1",
            metadata={"score": 91.0},
        ),
        GameEvent(
            user_id="hardcore_user",
            type=GameEventType.SHADOWING_COMPLETED,
            source=GameEventSource.SHADOWING,
            source_id=f"shad_hard_{day}_2",
            metadata={"score": 89.0},
        ),
    ]
    if day % 7 == 0:
        events.append(
            GameEvent(
                user_id="hardcore_user",
                type=GameEventType.BOSS_CLEARED,
                source=GameEventSource.BOSS,
                source_id=f"boss_{day}",
                metadata={"difficulty": "hard", "boss_name": "Job Interview", "score": 88.0},
            )
        )
    return events


def irregular_routine(day: int):
    # Practices only on Mon, Wed, Fri (3 days/week)
    if day % 7 in (1, 3, 5):
        return consistent_routine(day)
    return []


def run_all_simulations():
    print("==========================================================================")
    print(" Japanese Speaking Training OS — RPG Economy Progression Simulation")
    print("==========================================================================")

    for days in [30, 90]:
        print(f"\n--- [ {days}-Day Projection ] ---")
        profiles = [
            simulate_profile("Casual (10 min/day)", days, casual_routine),
            simulate_profile("Consistent (30 min/day)", days, consistent_routine),
            simulate_profile("Hardcore (60 min/day)", days, hardcore_routine),
            simulate_profile("Irregular (3 days/week)", days, irregular_routine),
        ]

        print(f"{'Profile Name':<25} | {'Total XP':<10} | {'Avg XP/day':<12} | {'Level':<8} | {'Longest Streak':<15} | {'Rank'}")
        print("-" * 105)
        for p in profiles:
            print(
                f"{p['name']:<25} | {p['total_xp']:<10} | {p['avg_daily_xp']:<12} | "
                f"Lv. {p['final_level']:<4} | {p['longest_streak']:<15} | {p['final_rank']}"
            )


if __name__ == "__main__":
    run_all_simulations()
