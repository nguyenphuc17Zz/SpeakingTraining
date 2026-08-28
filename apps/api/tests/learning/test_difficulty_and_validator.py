import pytest

from app.domains.learning.contracts import DifficultyLevel, ExerciseResult, ExerciseType, IndependenceLevel, ScaffoldingLevel
from app.domains.learning.difficulty_adjuster import DifficultyAdjuster
from app.domains.learning.exercise_validator import ExerciseValidator


def test_difficulty_adaptation_streak():
    results_pass = [
        ExerciseResult(exercise_id="1", user_id="u1", score=85, success=True, feedback="", independence=IndependenceLevel.INDEPENDENT),
        ExerciseResult(exercise_id="2", user_id="u1", score=88, success=True, feedback="", independence=IndependenceLevel.INDEPENDENT),
        ExerciseResult(exercise_id="3", user_id="u1", score=92, success=True, feedback="", independence=IndependenceLevel.INDEPENDENT),
    ]
    new_diff = DifficultyAdjuster.adjust_next_difficulty(DifficultyLevel.NORMAL, results_pass)
    assert new_diff == DifficultyLevel.HARD

    results_fail = [
        ExerciseResult(exercise_id="1", user_id="u1", score=40, success=False, feedback="", independence=IndependenceLevel.INDEPENDENT),
        ExerciseResult(exercise_id="2", user_id="u1", score=50, success=False, feedback="", independence=IndependenceLevel.INDEPENDENT),
    ]
    new_diff_down = DifficultyAdjuster.adjust_next_difficulty(DifficultyLevel.NORMAL, results_fail)
    assert new_diff_down == DifficultyLevel.EASY


def test_scaffolding_and_fatigue():
    # Consecutive failures -> add sentence starter scaffold
    scaffold, hint = DifficultyAdjuster.determine_scaffolding(mastery=0.3, consecutive_failures=2)
    assert scaffold == ScaffoldingLevel.SENTENCE_STARTER

    # High failure streak -> fatigue trigger recommends switching to pronunciation or conversation
    fatigue, msg, switch_type = DifficultyAdjuster.check_fatigue_and_recommend_switch(consecutive_failures=3, session_exercises_done=3)
    assert fatigue is True
    assert switch_type == ExerciseType.PRONUNCIATION_REPEAT


def test_exercise_validator():
    valid_data = {
        "title": "Hội thoại kính ngữ",
        "objective": "Luyện chuyển đổi desu masu",
        "instructions": "Hãy nói to câu hoàn chỉnh bằng kính ngữ chuẩn.",
        "target_patterns": ["です", "ます"],
        "estimated_minutes": 5,
    }
    is_valid, issues = ExerciseValidator.validate_exercise_data(valid_data)
    assert is_valid is True
    assert len(issues) == 0

    invalid_data = {
        "title": "",
        "objective": "Short",
        "instructions": "Too short",
        "target_patterns": [],
        "estimated_minutes": 60,
    }
    is_valid_inv, issues_inv = ExerciseValidator.validate_exercise_data(invalid_data)
    assert is_valid_inv is False
    assert len(issues_inv) >= 3
