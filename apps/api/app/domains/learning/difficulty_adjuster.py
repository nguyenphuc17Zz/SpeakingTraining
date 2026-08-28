from typing import Any

from app.domains.learning.contracts import (
    DifficultyLevel,
    ExerciseResult,
    ExerciseType,
    IndependenceLevel,
    ScaffoldingLevel,
)


class DifficultyAdjuster:
    """Session-level adaptive difficulty, scaffolding management, and fatigue safeguards."""

    @classmethod
    def determine_scaffolding(
        cls,
        mastery: float,
        consecutive_failures: int = 0,
        difficulty: DifficultyLevel = DifficultyLevel.NORMAL,
    ) -> tuple[ScaffoldingLevel, str | None]:
        """
        Determines appropriate scaffolding level and hint strategy based on mastery and failure streaks.
        Goal: Fading scaffolding towards spontaneous production as learner improves.
        """
        # If learner is struggling in this session
        if consecutive_failures >= 2:
            return ScaffoldingLevel.SENTENCE_STARTER, "Gợi ý mẫu câu mở đầu để hỗ trợ bạn bật phản xạ tự tin hơn."

        if consecutive_failures == 1 or mastery < 0.25:
            return ScaffoldingLevel.KEYWORD_HINT, "Gợi ý từ khóa ngữ pháp/từ vựng trọng tâm."

        if mastery >= 0.70 or difficulty == DifficultyLevel.CHALLENGE:
            return ScaffoldingLevel.NONE, None

        if mastery >= 0.45:
            return ScaffoldingLevel.NONE, None

        return ScaffoldingLevel.KEYWORD_HINT, "Gợi ý từ khóa ngắn."

    @classmethod
    def adjust_next_difficulty(
        cls,
        current_difficulty: DifficultyLevel,
        recent_results: list[ExerciseResult],
    ) -> DifficultyLevel:
        """
        Adapts difficulty level based on recent streak of exercise results.
        Does NOT jump more than 1 tier at a time.
        """
        if not recent_results:
            return current_difficulty

        # Window of last 3 results
        window = recent_results[-3:]
        successes = sum(1 for r in window if r.success and r.score >= 75.0)
        failures = sum(1 for r in window if not r.success or r.score < 55.0)

        diff_order = [
            DifficultyLevel.EASY,
            DifficultyLevel.NORMAL,
            DifficultyLevel.HARD,
            DifficultyLevel.CHALLENGE,
        ]
        curr_idx = diff_order.index(current_difficulty)

        # 3 consecutive strong passes -> Increase difficulty
        if len(window) >= 3 and successes == 3:
            new_idx = min(len(diff_order) - 1, curr_idx + 1)
            return diff_order[new_idx]

        # 2 or more consecutive failures -> Decrease difficulty
        if len(window) >= 2 and failures >= 2:
            new_idx = max(0, curr_idx - 1)
            return diff_order[new_idx]

        return current_difficulty

    @classmethod
    def check_fatigue_and_recommend_switch(
        cls,
        consecutive_failures: int,
        session_exercises_done: int,
    ) -> tuple[bool, str | None, ExerciseType | None]:
        """
        Safeguards against learning fatigue:
        If user fails 3 times on drills, suggest switching to an easier/casual roleplay or pronunciation practice.
        """
        if consecutive_failures >= 3:
            return (
                True,
                "Nhận thấy bạn đang gặp thử thách ở dạng bài này. Chúng ta hãy đổi sang luyện phát âm hoặc hội thoại tự do thư giãn nhé!",
                ExerciseType.PRONUNCIATION_REPEAT,
            )

        if session_exercises_done >= 6:
            return (
                True,
                "Bạn đã hoàn thành rất nhiều bài tập hôm nay! Hãy kết thúc bằng một buổi hội thoại tự do nhẹ nhàng.",
                ExerciseType.CONVERSATION,
            )

        return False, None, None
