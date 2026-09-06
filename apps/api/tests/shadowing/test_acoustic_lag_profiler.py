"""Unit tests for Shadowing Acoustic Lag Profiler & Intonation DTW Engine."""

from app.domains.pronunciation.contracts import (
    AnalysisConfidenceLevel,
    PitchAssessment,
    PitchCurve,
    PitchPoint,
    PronunciationResult,
)
from app.domains.shadowing.analysis.acoustic_lag_profiler import ShadowingLagProfiler
from app.domains.shadowing.scoring import ShadowingScorer


def test_optimal_lag_scoring_and_classification():
    """Lag inside 150-400ms is classified as optimal and receives top scores."""
    rating = ShadowingLagProfiler.classify_lag(250.0)
    score = ShadowingLagProfiler.compute_lag_score(250.0)

    assert rating == "optimal"
    assert score >= 95.0

    result = ShadowingScorer.evaluate(
        target_text="日本語を勉強しています",
        user_transcript="にほんごをべんきょうしています",
        target_duration_sec=3.0,
        user_duration_sec=3.0,
        acoustic_lag_ms=250.0,
    )
    assert result.metrics.acoustic_lag_ms == 250.0
    assert result.metrics.lag_rating == "optimal"
    assert result.metrics.lag_score is not None and result.metrics.lag_score >= 95.0
    assert any("Độ trễ Shadowing" in s for s in result.strengths)


def test_too_fast_talking_over_penalty():
    """Lag < 100ms indicates talking over / concurrent interference and is penalized."""
    rating = ShadowingLagProfiler.classify_lag(60.0)
    score = ShadowingLagProfiler.compute_lag_score(60.0)

    assert rating == "too_fast"
    assert score < 65.0

    result = ShadowingScorer.evaluate(
        target_text="こんにちは",
        user_transcript="こんにちは",
        target_duration_sec=1.5,
        user_duration_sec=1.5,
        acoustic_lag_ms=50.0,
    )
    assert result.metrics.lag_rating == "too_fast"
    assert any("đè lên giọng mẫu" in issue["title"] for issue in result.top_issues)


def test_trailing_lag_penalty():
    """Lag > 700ms indicates trailing into delayed repeating rather than shadowing."""
    rating = ShadowingLagProfiler.classify_lag(850.0)
    score = ShadowingLagProfiler.compute_lag_score(850.0)

    assert rating == "trailing"
    assert score < 65.0

    result = ShadowingScorer.evaluate(
        target_text="ありがとうございます",
        user_transcript="ありがとうございます",
        target_duration_sec=2.0,
        user_duration_sec=2.0,
        acoustic_lag_ms=900.0,
    )
    assert result.metrics.lag_rating == "trailing"
    assert any("tụt nhịp" in issue["title"] for issue in result.top_issues)


def test_hesitant_lag():
    """Lag between 401ms and 700ms is classified as hesitant."""
    rating = ShadowingLagProfiler.classify_lag(550.0)
    score = ShadowingLagProfiler.compute_lag_score(550.0)

    assert rating == "hesitant"
    assert 60.0 <= score <= 90.0

    result = ShadowingScorer.evaluate(
        target_text="どうぞよろしく",
        user_transcript="どうぞよろしく",
        target_duration_sec=2.0,
        user_duration_sec=2.0,
        acoustic_lag_ms=550.0,
    )
    assert result.metrics.lag_rating == "hesitant"
    assert any("hơi chậm" in issue["title"] for issue in result.top_issues)


def test_dtw_pitch_contour_evaluation():
    """Evaluates DTW pitch contour similarity using pitch curve points."""
    points = [
        PitchPoint(timestamp_ms=0, frequency_hz=180.0, normalized_semitones=0.0),
        PitchPoint(timestamp_ms=100, frequency_hz=210.0, normalized_semitones=2.6),
        PitchPoint(timestamp_ms=200, frequency_hz=190.0, normalized_semitones=0.9),
        PitchPoint(timestamp_ms=300, frequency_hz=150.0, normalized_semitones=-3.1),
    ]
    pitch_curve = PitchCurve(points=points)
    pitch_assessment = PitchAssessment(pitch_curve=pitch_curve)
    pron_result = PronunciationResult(
        overall_score=85.0,
        overall_confidence=AnalysisConfidenceLevel.HIGH,
        score_interpretation="Good",
        pitch_assessment=pitch_assessment,
    )

    result = ShadowingScorer.evaluate(
        target_text="雨が降っています",
        user_transcript="あめがふっています",
        target_duration_sec=2.0,
        user_duration_sec=2.0,
        pron_result=pron_result,
        acoustic_lag_ms=220.0,
    )
    assert result.metrics.pitch_contour_similarity is not None
    assert result.metrics.pitch_contour_similarity > 0.0


def test_backward_compatibility_when_lag_is_none():
    """Ensures evaluation works seamlessly without acoustic lag parameters."""
    result = ShadowingScorer.evaluate(
        target_text="おはようございます",
        user_transcript="おはようございます",
        target_duration_sec=2.0,
        user_duration_sec=2.0,
    )
    assert result.score >= 90.0
    assert result.metrics.acoustic_lag_ms is None
    assert result.metrics.lag_rating is None
