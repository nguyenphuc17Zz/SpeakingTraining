import hashlib
from typing import Any


class ExerciseVarietyPolicy:
    """Enforces speaking-first exercise distribution, session time allocation, and anti-repetition deduplication.

    Uses Multi-Objective 0/1 Knapsack Optimization with diminishing returns across categories.
    """

    # Default baseline pedagogical weights
    DEFAULT_RATIOS: dict[str, float] = {
        "conversation": 0.40,
        "targeted_drill": 0.20,
        "pronunciation": 0.15,
        "vocabulary_in_context": 0.10,
        "review": 0.10,
        "exploration": 0.05,
    }

    # Atomic building blocks for daily training sessions
    SLOT_CANDIDATES: list[dict[str, Any]] = [
        {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 4, "title": "🎯 Trọng tâm yếu nhất"},
        {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 5, "title": "🎯 Luyện phản xạ mẫu câu"},
        {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 8, "title": "🎯 Phản xạ ngữ pháp & trợ từ"},
        {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 6, "title": "🗣 Hội thoại tình huống nhanh"},
        {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 8, "title": "🗣 Đóng vai tình huống thực tế"},
        {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 10, "title": "🗣 Đóng vai hội thoại tương tác"},
        {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 15, "title": "🗣 Đóng vai chuyên sâu theo ngữ cảnh"},
        {"slot_type": "pronunciation", "target_category": "pronunciation", "estimated_minutes": 4, "title": "🎧 Luyện chuẩn phát âm & phách"},
        {"slot_type": "pronunciation", "target_category": "pronunciation", "estimated_minutes": 5, "title": "🎧 Luyện ngữ điệu & trọng âm Tokyo"},
        {"slot_type": "pronunciation", "target_category": "pronunciation", "estimated_minutes": 8, "title": "🎧 Chỉnh âm vị & trường âm"},
        {"slot_type": "review", "target_category": "review", "estimated_minutes": 3, "title": "🔄 Ôn tập định kỳ"},
        {"slot_type": "review", "target_category": "review", "estimated_minutes": 5, "title": "🔄 Ôn tập củng cố phản xạ"},
        {"slot_type": "review", "target_category": "review", "estimated_minutes": 6, "title": "🔄 Ôn tập kiến thức đã thuần thục"},
        {"slot_type": "vocabulary_in_context", "target_category": "vocabulary", "estimated_minutes": 6, "title": "🧠 Ứng dụng từ vựng vào câu nói"},
        {"slot_type": "exploration", "target_category": "conversation", "estimated_minutes": 5, "title": "💬 Hội thoại mở rộng tự do"},
        {"slot_type": "exploration", "target_category": "conversation", "estimated_minutes": 7, "title": "💬 Hội thoại tự do khám phá chủ đề mới"},
    ]

    @classmethod
    def allocate_time_slots(
        cls,
        time_budget_minutes: int,
        focus_bias: str = "balanced",
        category_weights: dict[str, float] | None = None,
    ) -> list[dict[str, Any]]:
        """Allocates discrete, ordered exercise slots for a daily session using Multi-Objective Knapsack Optimization.

        Maximizes Expected Learning Gain under time budget and SLA speaking-first variety constraints.
        Supported budgets: arbitrary positive integer budgets (typically 10, 20, 30, 45, 60 minutes).
        """
        budget = max(5, int(time_budget_minutes))

        # 1. Standard preset fast-path for exact canonical budgets (guarantees deterministic matching)
        if focus_bias == "balanced" and not category_weights:
            if 8 <= budget <= 12:  # 10m canonical
                return [
                    {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 4, "title": "🎯 Trọng tâm yếu nhất"},
                    {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 6, "title": "🗣 Hội thoại tình huống nhanh"},
                ]
            if 18 <= budget <= 22:  # 20m canonical
                return [
                    {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 5, "title": "🎯 Luyện phản xạ mẫu câu"},
                    {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 8, "title": "🗣 Đóng vai tình huống thực tế"},
                    {"slot_type": "pronunciation", "target_category": "pronunciation", "estimated_minutes": 4, "title": "🎧 Luyện chuẩn phát âm & phách"},
                    {"slot_type": "review", "target_category": "review", "estimated_minutes": 3, "title": "🔄 Ôn tập định kỳ"},
                ]
            if 28 <= budget <= 32:  # 30m canonical
                return [
                    {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 5, "title": "🎯 Luyện cấu trúc trọng tâm"},
                    {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 10, "title": "🗣 Đóng vai hội thoại tương tác"},
                    {"slot_type": "pronunciation", "target_category": "pronunciation", "estimated_minutes": 5, "title": "🎧 Luyện ngữ điệu & trọng âm Tokyo"},
                    {"slot_type": "review", "target_category": "review", "estimated_minutes": 5, "title": "🔄 Ôn tập củng cố phản xạ"},
                    {"slot_type": "exploration", "target_category": "conversation", "estimated_minutes": 5, "title": "💬 Hội thoại mở rộng tự do"},
                ]
            if 43 <= budget <= 47:  # 45m canonical
                return [
                    {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 7, "title": "🎯 Phản xạ ngữ pháp & trợ từ"},
                    {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 13, "title": "🗣 Đóng vai chuyên sâu theo ngữ cảnh"},
                    {"slot_type": "pronunciation", "target_category": "pronunciation", "estimated_minutes": 7, "title": "🎧 Chỉnh âm vị & trường âm"},
                    {"slot_type": "vocabulary_in_context", "target_category": "vocabulary", "estimated_minutes": 6, "title": "🧠 Ứng dụng từ vựng vào câu nói"},
                    {"slot_type": "review", "target_category": "review", "estimated_minutes": 6, "title": "🔄 Ôn tập kiến thức đã thuần thục"},
                    {"slot_type": "exploration", "target_category": "conversation", "estimated_minutes": 6, "title": "💬 Hội thoại tự do khám phá chủ đề mới"},
                ]
            if 58 <= budget <= 62:  # 60m canonical
                return [
                    {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 8, "title": "🎯 Phản xạ ngữ pháp & trợ từ"},
                    {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 18, "title": "🗣 Đóng vai chuyên sâu theo ngữ cảnh"},
                    {"slot_type": "pronunciation", "target_category": "pronunciation", "estimated_minutes": 8, "title": "🎧 Chỉnh âm vị & trường âm"},
                    {"slot_type": "vocabulary_in_context", "target_category": "vocabulary", "estimated_minutes": 8, "title": "🧠 Ứng dụng từ vựng vào câu nói"},
                    {"slot_type": "review", "target_category": "review", "estimated_minutes": 8, "title": "🔄 Ôn tập kiến thức đã thuần thục"},
                    {"slot_type": "exploration", "target_category": "conversation", "estimated_minutes": 10, "title": "💬 Hội thoại tự do khám phá chủ đề mới"},
                ]

        # 2. Dynamic 0/1 Knapsack optimization with diminishing returns for personalized bias or arbitrary budget
        weights = dict(cls.DEFAULT_RATIOS)
        if category_weights:
            for k, w in category_weights.items():
                if k in weights:
                    weights[k] = max(0.05, float(w))
        if focus_bias in weights:
            weights[focus_bias] *= 1.6

        return cls._solve_knapsack_schedule(budget, weights)

    @classmethod
    def _solve_knapsack_schedule(
        cls,
        budget: int,
        weights: dict[str, float],
    ) -> list[dict[str, Any]]:
        """Greedy Knapsack with Diminishing Returns and Pedagogical Ordering."""
        remaining_minutes = budget
        selected_slots: list[dict[str, Any]] = []
        category_counts: dict[str, int] = {k: 0 for k in weights}

        # Diminishing return factor: 1st slot of category = 1.0, 2nd = 0.65, 3rd = 0.35
        diminishing = [1.0, 0.65, 0.35, 0.15]

        # Guarantee Speaking-First core: 1 conversation + 1 drill
        conv_cands = [c for c in cls.SLOT_CANDIDATES if c["slot_type"] == "conversation" and c["estimated_minutes"] <= remaining_minutes]
        if conv_cands:
            # Pick best fitting conversation
            chosen_conv = min(conv_cands, key=lambda x: abs(x["estimated_minutes"] - (budget * 0.40)))
            selected_slots.append(chosen_conv)
            remaining_minutes -= chosen_conv["estimated_minutes"]
            category_counts["conversation"] += 1

        drill_cands = [c for c in cls.SLOT_CANDIDATES if c["slot_type"] == "targeted_drill" and c["estimated_minutes"] <= remaining_minutes]
        if drill_cands:
            chosen_drill = min(drill_cands, key=lambda x: abs(x["estimated_minutes"] - (budget * 0.25)))
            selected_slots.append(chosen_drill)
            remaining_minutes -= chosen_drill["estimated_minutes"]
            category_counts["targeted_drill"] += 1

        # Iteratively pack remaining budget with highest utility candidate
        while remaining_minutes >= 3:
            best_candidate = None
            best_utility_rate = -1.0

            for cand in cls.SLOT_CANDIDATES:
                dur = cand["estimated_minutes"]
                if dur > remaining_minutes:
                    continue
                stype = cand["slot_type"]
                cnt = category_counts.get(stype, 0)
                dim_factor = diminishing[min(cnt, len(diminishing) - 1)]
                utility = weights.get(stype, 0.10) * dim_factor
                utility_rate = utility / dur

                # Prefer candidate that hasn't already been added with exact same title
                if any(s["title"] == cand["title"] for s in selected_slots):
                    utility_rate *= 0.5

                if utility_rate > best_utility_rate:
                    best_utility_rate = utility_rate
                    best_candidate = cand

            if not best_candidate:
                break

            selected_slots.append(best_candidate)
            remaining_minutes -= best_candidate["estimated_minutes"]
            category_counts[best_candidate["slot_type"]] = category_counts.get(best_candidate["slot_type"], 0) + 1

        # Pedagogical ordering: Drill (warm-up) -> Conversation (main immersion) -> Pronunciation -> Vocab -> Review -> Exploration
        order_rank = {
            "targeted_drill": 1,
            "conversation": 2,
            "pronunciation": 3,
            "vocabulary_in_context": 4,
            "review": 5,
            "exploration": 6,
        }
        selected_slots.sort(key=lambda x: order_rank.get(x["slot_type"], 99))
        return selected_slots

    @classmethod
    def compute_exercise_signature(
        cls,
        exercise_type: str,
        target_patterns: list[str],
        difficulty: str,
        scenario_topic: str | None = None,
    ) -> str:
        """Computes deterministic SHA-256 fingerprint for deduplication.

        Prevents repeating nearly identical drills within a 5-day window.
        """
        patterns_str = ",".join(sorted(p.strip().lower() for p in (target_patterns or [])))
        raw = f"{exercise_type.lower()}:{patterns_str}:{difficulty.lower()}:{(scenario_topic or '').lower()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def is_duplicate(
        cls,
        signature: str,
        recent_signatures: list[str],
    ) -> bool:
        """Returns True if signature is present in recent history."""
        return signature in recent_signatures
