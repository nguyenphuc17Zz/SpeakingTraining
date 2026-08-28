import pytest

from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    PronunciationResult,
    PronunciationScoreComponent,
)
from app.domains.shadowing.scoring import ShadowingScorer


def test_shadowing_empty_speech_zero_score():
    """Verify empty or no-speech audio returns 0 score without exceptions."""
    result = ShadowingScorer.evaluate(
        target_text="今日はいい天気ですね",
        user_transcript="",
        target_duration_sec=3.0,
        user_duration_sec=3.0,
    )
    assert result.score == 0.0
    assert result.accuracy_score == 0.0
    assert result.success is False
    assert "Không nhận diện được giọng nói" in result.feedback
    assert len(result.top_issues) > 0


def test_shadowing_perfect_repetition_high_score():
    """Verify perfect repetition with matching tempo receives high score."""
    result = ShadowingScorer.evaluate(
        target_text="おはようございます",
        user_transcript="おはようございます",
        target_duration_sec=2.0,
        user_duration_sec=2.0,
        shadowing_mode="shadow",
    )
    assert result.score >= 90.0
    assert result.accuracy_score >= 95.0
    assert result.timing_score >= 90.0
    assert result.success is True
    assert result.mastery_state == "comfortable"
    assert len(result.strengths) > 0


def test_shadowing_kanji_to_hiragana_equivalence():
    """Verify Kanji target vs Hiragana transcript is recognized as correct."""
    result = ShadowingScorer.evaluate(
        target_text="学校に行きます",
        user_transcript="がっこうにいきます",
        target_duration_sec=2.5,
        user_duration_sec=2.5,
        shadowing_mode="shadow",
    )
    assert result.accuracy_score >= 95.0
    assert result.score >= 90.0
    assert result.success is True


def test_shadowing_sokuon_omission_detection():
    """Verify missing small tsu (っ) is penalized and highlighted in top_issues."""
    result = ShadowingScorer.evaluate(
        target_text="切手を買いました",  # きって
        user_transcript="きてをかいました",  # きて (missing sokuon)
        target_duration_sec=2.5,
        user_duration_sec=2.5,
    )
    assert result.accuracy_score < 95.0
    assert any("っ" in issue["title"] or "っ" in issue["explanation"] for issue in result.top_issues)


def test_shadowing_speech_rate_tempo_penalty():
    """Verify speaking too fast or too slow affects timing score."""
    # Extremely slow (3x slower than native)
    result_slow = ShadowingScorer.evaluate(
        target_text="きょうは映画を見ました",
        user_transcript="きょうは映画を見ました",
        target_duration_sec=2.0,
        user_duration_sec=7.0,  # 3.5x slower
        shadowing_mode="shadow",
    )
    assert result_slow.timing_score < 75.0
    assert any("chậm" in issue["title"] or "chậm" in issue["explanation"] for issue in result_slow.top_issues)

    # Normal tempo matching native
    result_normal = ShadowingScorer.evaluate(
        target_text="きょうは映画を見ました",
        user_transcript="きょうは映画を見ました",
        target_duration_sec=2.5,
        user_duration_sec=2.5,
        shadowing_mode="shadow",
    )
    assert result_normal.timing_score >= 90.0


def test_shadowing_mode_weight_differences():
    """Verify pure shadow mode penalizes tempo deviations more than listen_shadow mode."""
    # Same minor tempo deviation in both modes
    res_shadow = ShadowingScorer.evaluate(
        target_text="よろしくお願いします",
        user_transcript="よろしくおねがいします",
        target_duration_sec=2.0,
        user_duration_sec=3.2,
        shadowing_mode="shadow",
    )
    res_listen_shadow = ShadowingScorer.evaluate(
        target_text="よろしくお願いします",
        user_transcript="よろしくおねがいします",
        target_duration_sec=2.0,
        user_duration_sec=3.2,
        shadowing_mode="listen_shadow",
    )
    # Listen & shadow should give higher overall score because accuracy (40%) > tempo (15%)
    assert res_listen_shadow.score >= res_shadow.score
