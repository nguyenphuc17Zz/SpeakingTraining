import hashlib
from typing import Any

from app.domains.learning.contracts import ExerciseType


class ExerciseVarietyPolicy:
    """Enforces speaking-first exercise distribution, session time allocation, and anti-repetition deduplication."""

    # Default baseline percentage weights
    DEFAULT_RATIOS = {
        "conversation": 0.40,
        "targeted_drill": 0.20,
        "pronunciation": 0.15,
        "vocabulary_in_context": 0.10,
        "review": 0.10,
        "exploration": 0.05,
    }

    @classmethod
    def allocate_time_slots(
        cls,
        time_budget_minutes: int,
        focus_bias: str = "balanced",
    ) -> list[dict[str, Any]]:
        """
        Allocates discrete, ordered exercise slots for a daily session based on time budget.
        Supported budgets: 10, 20, 30, 45, 60 minutes.
        """
        budget = max(5, time_budget_minutes)

        if budget <= 12:  # Quick 10-minute session
            return [
                {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 4, "title": "🎯 Trọng tâm yếu nhất"},
                {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 6, "title": "🗣 Hội thoại tình huống nhanh"},
            ]

        if budget <= 22:  # 20-minute session
            return [
                {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 5, "title": "🎯 Luyện phản xạ mẫu câu"},
                {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 8, "title": "🗣 Đóng vai tình huống thực tế"},
                {"slot_type": "pronunciation", "target_category": "pronunciation", "estimated_minutes": 4, "title": "🎧 Luyện chuẩn phát âm & phách"},
                {"slot_type": "review", "target_category": "review", "estimated_minutes": 3, "title": "🔄 Ôn tập định kỳ"},
            ]

        if budget <= 35:  # Standard 30-minute session
            return [
                {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 5, "title": "🎯 Luyện cấu trúc trọng tâm"},
                {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 10, "title": "🗣 Đóng vai hội thoại tương tác"},
                {"slot_type": "pronunciation", "target_category": "pronunciation", "estimated_minutes": 5, "title": "🎧 Luyện ngữ điệu & trọng âm Tokyo"},
                {"slot_type": "review", "target_category": "review", "estimated_minutes": 5, "title": "🔄 Ôn tập củng cố phản xạ"},
                {"slot_type": "exploration", "target_category": "conversation", "estimated_minutes": 5, "title": "💬 Hội thoại mở rộng tự do"},
            ]

        # 45 - 60 minute deep training session
        return [
            {"slot_type": "targeted_drill", "target_category": "grammar", "estimated_minutes": 8, "title": "🎯 Phản xạ ngữ pháp & trợ từ"},
            {"slot_type": "conversation", "target_category": "roleplay", "estimated_minutes": 15, "title": "🗣 Đóng vai chuyên sâu theo ngữ cảnh"},
            {"slot_type": "pronunciation", "target_category": "pronunciation", "estimated_minutes": 8, "title": "🎧 Chỉnh âm vị & trường âm"},
            {"slot_type": "vocabulary_in_context", "target_category": "vocabulary", "estimated_minutes": 6, "title": "🧠 Ứng dụng từ vựng vào câu nói"},
            {"slot_type": "review", "target_category": "review", "estimated_minutes": 6, "title": "🔄 Ôn tập kiến thức đã thuần thục"},
            {"slot_type": "exploration", "target_category": "conversation", "estimated_minutes": 7, "title": "💬 Hội thoại tự do khám phá chủ đề mới"},
        ]

    @classmethod
    def compute_exercise_signature(
        cls,
        exercise_type: str,
        target_patterns: list[str],
        difficulty: str,
        scenario_topic: str | None = None,
    ) -> str:
        """
        Computes deterministic SHA-256 fingerprint for deduplication.
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
